# KingdomOfAnimal: 2023 모두의 말뭉치 EA 감정분석 동물의 왕국

동물의 왕국 프로젝트는 2023 모두의 말뭉치를 사용한 감정 분석에 초점을 맞춘 프로젝트입니다. 본 프로젝트는 학습 데이터를 기반으로 감정 분석 모델을 학습시키고, 검증 및 테스트 데이터를 통해 모델의 성능을 평가. 이를 위해 Mean, Max Pooling과 특정 단어 주위의 N-gram을 Attention으로 분석하는 두 가지 방식의 모델을 사용.

### 프로젝트 구조

${PROJECT}
├── EA/
│ ├── data/
│ │ ├── train.jsonl
│ │ ├── dev.jsonl
│ │ └── test.jsonl
│ ├── models/
│ │ ├── EnhancedPoolingModel2.py
│ │ └── RealAttention5.py
│ ├── modules/
│ │ ├── arg_parser.py
│ │ ├── dataset_preprocessor.py
│ │ ├── logger_module.py
│ │ └── utils.py
│ └── results/
│ ├── ensemble.py
│ ├── inference_logits.py
│ ├── inference_logitslora.py
│ ├── run.py
│ └── runllm.py
├── Ensemble/
│ └── 가젤왕.jsonl
├── inf.sh
└── requirements.yaml

markdown
Copy code

- **EA 폴더**: 모델 학습 및 추론에 필요한 모든 파일이 포함됩니다.
  - `data`: 학습, 검증, 테스트 데이터셋이 포함됩니다.
  - `models`: 학습에 사용되는 모델 클래스 파일이 포함됩니다.
  - `modules`: 데이터 전처리, 로깅 등에 사용되는 유틸리티 클래스 파일이 포함됩니다.
  - `results`: 추론 결과를 저장하는 폴더입니다.
- **Ensemble 폴더**: 앙상블을 위한 추가 데이터셋이 포함됩니다.

### 추론 과정

1. **데이터 준비**:
   - `EA/data` 폴더에 `train.jsonl`, `dev.jsonl`, `test.jsonl`을 준비합니다.
   - `Ensemble` 폴더에 `가젤왕.jsonl`을 위치시킵니다.

2. **가상 환경 설정**:
   - `requirements.yaml` 파일을 이용하여 가상 환경을 설정합니다.
   - ```conda env create -f requirements.yaml``` 명령어로 가상 환경을 생성합니다.

3. **추론 실행**:
   - 프로젝트의 루트 디렉토리에서 `bash inf.sh`를 실행하여 추론을 시작합니다.

4. **결과 확인**:
   - `Ensemble` 폴더 안에 `최종제출.jsonl` 형태로 결과가 출력됩니다.
