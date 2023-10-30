# KingdomOfAnimal
2023 모두의 말뭉치 EA 감정분석 동물의 왕국

### 코드 구조

```
${PROJECT}
├── EA/
│   ├── data/
│   │   ├── train.jsonl
│   │   ├── dev.jsonl
│   │   └── test.jsonl
│   ├── models/
│   │   ├── EnhancedPoolingModel2.py
│   │   └── RealAttention5.py
│   ├── modules/
│   │   ├── arg_parser.py
│   │   ├── dataset_preprocessor.py
│   │   ├── logger_module.py
│   │   └── utils.py
│   └── results/
│   ├── ensemble.py
│   ├── inference_logits.py
│   ├── inference_logitslora.py
│   ├── run.py
│   └── runllm.py
├── Ensemble/
│   └── 가젤왕.jsonl
├── inf.sh
└── requirements.yaml
```

- EA
    - data
      - train.jsonl: 학습 데이터
      - dev.jsonl: 검증 데이터
      - test.jsonl: 추론 데이터
    - models
      - EnhancedPoolingModel2.py: Mean, Max Pooling만 사용한 모델 class
      - RealAttention5.py: Prompt형태로 특정단어 주위의 단어 N_gram을 attention해서 이용한 모델 class
    - modules
      - arg_parser.py: parser 인자 저장 class
      - dataset_preprocessor.py: 데이터 전처리 class
      - logger_module.py: logger module class
      - utils.py: 나머지 전체 utils 저장 class
  - run.py: Encoder 기반 모델 학습 코드
  - runllm.py: LLM 모델 학습 코드
  - inference_logits.py: Encoder 기반 모델 추론 코드
  - inference_logitslora.py: LLM 모델 추론 코드
  - ensemble.py: 최종 logits 기반 앙상블 코드
- ENSEMBLE


---

### 추론 process

1. 데이터 폴더 준비
   - data 폴더내에 업로드된 데이터파일을 추가 train.jsonl,val.jsonl,test.jsonl 은 EA폴더내의 data에
   - 가젤왕.jsonl은 ENSEMBLE/ 폴더 안에
   - https://drive.google.com/file/d/1_sbvG2bXVfkU_sDk_5XaqERthDeOlB1h/view?usp=sharing
2. EA안에 results폴더 추가
   - https://drive.google.com/file/d/1GzZ_mg0fOBJCspA0aUJ9HpILSA_0T_-e/view?usp=sharing
4. ENSEMBLE 파일에 업로드된 '가젤왕' 파일 추가
5. 가상환경인 requiremnets,yaml을 이용하여 가상환경 setting
   - conda env create -f requirements.yaml를 통해 생성된 가상환경 testsub를 통해 검증
7. 맨앞의 폴더로 돌아가 bash inf.sh를 실행후 inference를 실행
8. ENSEMBLE폴더 안에 '최종제출.jsonl' 형태로 결과가 출력
