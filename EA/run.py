import os
import sys
import torch
import wandb
import numpy as np

from sklearn.metrics import f1_score, roc_auc_score, accuracy_score

from torch.utils.data import DataLoader, ConcatDataset, Subset
from sklearn.model_selection import KFold
from datasets import concatenate_datasets,Dataset
# from peft import get_peft_config, get_peft_model, LoraConfig, TaskType
from transformers import (AutoModel, AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    EvalPrediction,
    AdamW,
    get_linear_schedule_with_warmup,
    EarlyStoppingCallback
)
from adamp import AdamP

# module import
from modules.logger_module import get_logger, log_args, setup_seed
from modules.utils import create_output_dir, load_tokenizer, load_datasets, get_labels_from_dataset
from modules.arg_parser import get_args
from modules.dataset_preprocessor import load_and_preprocess_datasets, CustomDataset, preprocess_data_special_token
from modules.utils import jsonldump, save_as_jsonl

# model import
from models.EnhancedPoolingModel2 import EnhancedPoolingModel2
from models.RealAttention5 import RealAttention5

os.environ["TOKENIZERS_PARALLELISM"] = "false"

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model_classes = {
    'EnhancedPoolingModel2': EnhancedPoolingModel2,
    'RealAttention5': RealAttention5
}

def main(args):
    # Setup logger
    create_output_dir(args.output_dir)
    
    # 그 다음 로거를 설정합니다.
    logger = get_logger("train", f'{args.output_dir}logfile.log')
    log_args(args, logger)
    setup_seed(args.seed, logger)

    # 생성된 디렉토리에 대한 정보를 로그로 기록합니다.
    logger.info(f"Created output directory at {args.output_dir}")

    # Log the GPU information
    logger.info(f"[+] GPU: {args.gpus}")

    # Load tokenizer and log the action
    tokenizer = load_tokenizer(args.tokenizer)
    
    #tokenizer에 특수토큰을 추가
    if args.special_token is True:
        special_tokens_dict = {
            'additional_special_tokens': [
                '<e>', '</e>',
                '&name1&', '&name2&', '&name3&', '&name4&', '&name5&', '&affiliation1&',
                '&account1&', '&account2&', '&account3&', '&account4&', '&account5&',
            ]
        }
        tokenizer.add_special_tokens(special_tokens_dict)
    logger.info(f'[+] Loaded Tokenizer')

    # Load datasets and log the action
    train_ds, _ = load_datasets(args.train_path, args.val_path)
    
    logger.info(f'[+] Loaded Dataset')

    # Get label mappings
    _, id2label, _ = get_labels_from_dataset(train_ds)
    
    # Get encoded data value for the combined datasets

    model_class = model_classes[args.model_class]
    model = model_class(args, len(id2label), tokenizer)
    if args.kfold:
        kfold = KFold(n_splits=args.kfold, shuffle=True, random_state=args.seed)
        encoded_kfold_data_ds, _ = load_and_preprocess_datasets(tokenizer, args.kfold_data_path, None, args.max_seq_len, args.special_token, args.clean)#, args.label_smoothing)
        original_ds = Dataset.from_json(args.kfold_data_path)
        #combined_dataset = CustomDataset(encoded_kfold_data_ds)
        
        for fold, (train_idx, val_idx) in enumerate(kfold.split(encoded_kfold_data_ds)):
            initialize_wandb(args, fold)
            
            logger.info(f"Starting fold {fold + 1}/{args.kfold}")
            model_class = model_classes[args.model_class]
            model = model_class(args, len(id2label), tokenizer)
                    
            train_loader, val_loader = get_data_loaders(args, encoded_kfold_data_ds, train_idx, val_idx)
            # 폴더 및 데이터 관리
            manage_kfold_data(args, original_ds, fold, train_idx, val_idx)
            
            train_and_validate(args, tokenizer, model, train_loader, val_loader, fold)
            
            wandb.finish()

    else:
        initialize_wandb(args, None)
        
        encoded_train_ds, encoded_valid_ds = load_and_preprocess_datasets(tokenizer, args.train_path, args.val_path, args.max_seq_len, args.special_token, args.clean)#, args.label_smoothing)
        

        train_and_validate(args, tokenizer, model, encoded_train_ds, encoded_valid_ds)
        wandb.finish()

def manage_kfold_data(args, original_ds, fold, train_idx, val_idx):
    # 폴더 생성
    fold_dir = os.path.join(args.output_dir, f"fold_{fold + 1}")
    os.makedirs(fold_dir, exist_ok=True)

    # train과 val 데이터를 해당 폴더에 jsonl 형식으로 저장
    save_as_jsonl(original_ds, [int(i) for i in train_idx], os.path.join(fold_dir, "train.jsonl"))
    save_as_jsonl(original_ds, [int(i) for i in val_idx], os.path.join(fold_dir, "val.jsonl"))

def initialize_wandb(args, fold):
    run_name = f'{args.wandb_run_name}' if fold is None else f'{args.wandb_run_name}_fold_{fold}'
    wandb.init(name=run_name, project=args.wandb_project, entity=args.wandb_entity)
    wandb.config.update(args)

def get_data_loaders(args, combined_dataset, train_idx, val_idx):
    train_subset = Subset(combined_dataset, [int(i) for i in train_idx])
    val_subset = Subset(combined_dataset, [int(i) for i in val_idx])

    return train_subset, val_subset

def compute_metrics(p: EvalPrediction):
    labels = p.label_ids
    preds = np.where(p.predictions >= 0.5, 1, 0)
    f1_micro_average = f1_score(y_true=labels, y_pred=preds, average='micro')
    roc_auc = roc_auc_score(labels, preds, average='micro')
    accuracy = accuracy_score(y_true=labels, y_pred=preds)

    return {
        'Validation F1': f1_micro_average,
        'Validation ROC AUC': roc_auc,
        'Validation Accuracy': accuracy,
    }

def train_and_validate(args, tokenizer, model, train_loader, val_loader, fold=None):
    logger = get_logger("train", f'{args.output_dir}train_and_validate.log')
    
    output_dir = args.output_dir if fold is None else os.path.join(args.output_dir, f"fold_{fold+1}")
    
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        evaluation_strategy="steps",
        logging_dir=args.output_dir,
        logging_steps=args.logging_steps,
        save_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="Validation F1",  # f1 점수를 기준으로 가장 좋은 모델을 선택
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        #auto_find_batch_size=True
    )
    
    FULL_FINETUNING = True
    if FULL_FINETUNING:
        param_optimizer = list(model.named_parameters())
        no_decay = ['bias', 'LayerNorm.weight']
        optimizer_grouped_parameters = [
            {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
             'weight_decay_rate': 0.01},
            {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)],
             'weight_decay_rate': 0.0}
        ]
    else:
        param_optimizer = list(model.classifier.named_parameters())
        optimizer_grouped_parameters = [{"params": [p for n, p in param_optimizer]}]

    
    optimizer = AdamP(optimizer_grouped_parameters, lr=args.learning_rate)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=0, num_training_steps=len(train_loader) * args.epochs)

    trainer = Trainer(
        model=model,
        args=training_args,
        callbacks = [EarlyStoppingCallback(early_stopping_patience=5)],
        train_dataset=train_loader,
        eval_dataset=val_loader,
        tokenizer=tokenizer, 
        compute_metrics=compute_metrics,
        optimizers=(optimizer, scheduler)
    )

    trainer.train()
    
    torch.save(model.state_dict(), os.path.join(output_dir, "model.pt"))
    tokenizer.save_pretrained(output_dir)


if __name__ == "__main__":
    args = get_args()
    exit(main(args))