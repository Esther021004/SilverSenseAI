# RAG 기반 응급 지침 생성 시스템

노인 응급·재난 상황 인지 및 실시간 대응 시나리오 생성 AI 프로젝트의 RAG(Retrieval-Augmented Generation) 모듈입니다.

## 📋 목차

- [기능](#기능)
- [설치](#설치)
- [사용 방법](#사용-방법)
- [프로젝트 구조](#프로젝트-구조)
- [주요 모듈](#주요-모듈)

## ✨ 기능

- **문서 자동 로딩**: PDF, HWP 등 다양한 형식의 응급처치 문서 자동 로딩
- **지능형 검색**: 상황에 맞는 관련 응급 지침을 벡터 검색으로 찾기
- **맞춤형 지침 생성**: 고령층을 위한 간단하고 명확한 응급 대응 지침 자동 생성
- **한국어 특화**: 한국어 문서와 임베딩 모델 사용

## 🔧 설치

### 1. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## 🚀 사용 방법

### 1단계: 벡터 스토어 구축

문서를 로딩하고 벡터 DB를 생성합니다. (처음 한 번만 실행)

```bash
python build_vectorstore.py
```

이 스크립트는:
- `document/` 폴더의 모든 PDF 파일을 로딩
- 텍스트를 의미 있는 청크로 분할
- 임베딩 생성 및 벡터 DB에 저장

### 2단계: RAG 시스템 사용

#### 기본 사용법

```python
from rag.rag_system import RAGSystem

# RAG 시스템 초기화
rag_system = RAGSystem(
    document_dir="document",
    persist_directory="./chroma_db",
    rebuild_vectorstore=False  # 이미 구축했다면 False
)

# 상황 정보 설정 (STT 구조화 결과 등)
situation_info = {
    "disasterLarge": "구급",
    "disasterMedium": "낙상",
    "urgencyLevel": "긴급",
    "sentiment": "불안",
    "triage": "적색"
}

# 응급 지침 생성
result = rag_system.generate_guideline(
    situation_info,
    additional_context="쓰러진 상태에서 숨을 못 쉬고 있음"
)

print(result['guideline'])  # 생성된 지침
print(result['report_message'])  # 신고 메시지
print(result['sources'])  # 참고 출처
```

#### 예제 실행

```bash
python example_usage.py
```

### 고급 사용법

#### 개별 모듈 사용

```python
from rag.document_loader import DocumentLoader
from rag.text_splitter import KoreanTextSplitter
from rag.embedding_store import EmbeddingStore
from rag.guideline_generator import GuidelineGenerator

# 1. 문서 로딩
loader = DocumentLoader(document_dir="document")
documents = loader.load_all_documents()

# 2. 텍스트 분할
splitter = KoreanTextSplitter(chunk_size=1000, chunk_overlap=200)
split_docs = splitter.split_documents(documents)

# 3. 벡터 스토어 생성
embedding_store = EmbeddingStore()
vectorstore = embedding_store.create_vectorstore(split_docs)

# 4. 지침 생성기 초기화
generator = GuidelineGenerator(embedding_store)

# 5. 지침 생성
result = generator.generate_guideline(situation_info)
```

## 📁 프로젝트 구조

```
.
├── document/                          # 응급처치 문서 (PDF, HWP)
│   ├── 응급처치 강의 요약본.pdf
│   ├── 노인 낙상 예방 가이드라인.pdf
│   └── ...
├── rag/                               # RAG 모듈
│   ├── __init__.py
│   ├── document_loader.py            # 문서 로딩
│   ├── text_splitter.py              # 텍스트 분할
│   ├── embedding_store.py            # 임베딩 및 벡터 스토어
│   ├── guideline_generator.py        # 지침 생성
│   └── rag_system.py                 # 통합 시스템
├── chroma_db/                         # 벡터 DB (자동 생성)
├── build_vectorstore.py              # 벡터 스토어 구축 스크립트
├── example_usage.py                   # 사용 예제
├── requirements.txt                   # 필요한 패키지
└── README_RAG.md                      # 이 파일
```

## 🔍 주요 모듈

### 1. DocumentLoader (`rag/document_loader.py`)

다양한 형식의 문서를 로딩합니다.

- PDF 파일: PyPDF, PDFPlumber, LangChain 로더 지원
- HWP 파일: 기본 지원 (완전한 지원을 위해서는 추가 라이브러리 필요)
- 자동 문서 탐지 및 로딩

### 2. KoreanTextSplitter (`rag/text_splitter.py`)

한국어 문서에 특화된 텍스트 분할기.

- 문단, 문장 단위 분할
- 청크 간 겹침(overlap) 지원
- 한국어 구분자 최적화

### 3. EmbeddingStore (`rag/embedding_store.py`)

문서를 임베딩하고 벡터 DB에 저장합니다.

- **로컬 모델**: `jhgan/ko-sroberta-multitask` (기본값, 한국어 특화)
- **OpenAI 모델**: OpenAI 임베딩 사용 가능 (선택사항)
- ChromaDB 벡터 스토어 사용
- 유사도 기반 검색

### 4. GuidelineGenerator (`rag/guideline_generator.py`)

RAG 기반 응급 지침 생성기.

- 상황 정보 기반 관련 문서 검색
- LLM을 통한 맞춤형 지침 생성
- 고령층 친화적 간단한 지침 생성
- 신고 메시지 자동 생성

### 5. RAGSystem (`rag/rag_system.py`)

모든 구성 요소를 통합한 메인 클래스.

- 초기화 시 자동으로 벡터 스토어 로딩/생성
- 간편한 API 제공

## ⚙️ 설정 옵션

### 임베딩 모델 변경

```python
rag_system = RAGSystem(
    embedding_model_name="jhgan/ko-sbert-multitask",  # 다른 한국어 모델
    # 또는
    use_openai_embedding=True  # OpenAI 임베딩 사용
)
```

### LLM 모델 변경

```python
rag_system = RAGSystem(
    llm_model="gpt-4"  # 기본값: gpt-3.5-turbo
)
```

### 텍스트 분할 설정

```python
from rag.text_splitter import KoreanTextSplitter

splitter = KoreanTextSplitter(
    chunk_size=1500,      # 청크 크기 (기본: 1000)
    chunk_overlap=300     # 겹침 크기 (기본: 200)
)
```

## 🔗 프로젝트 통합

이 RAG 모듈은 전체 프로젝트의 지침 생성 부분에 통합되어 사용됩니다:

```python
# 전체 프로젝트에서의 사용 예시
from rag.rag_system import RAGSystem

# STT 구조화 결과 + AED 결과를 받아서
situation_info = {
    "disasterLarge": stt_result["disasterLarge"],
    "disasterMedium": aed_result["event_type"],  # AED 결과
    "urgencyLevel": stt_result["urgencyLevel"],
    "sentiment": stt_result["sentiment"],
    "triage": stt_result["triage"]
}

# RAG로 지침 생성
rag_system = RAGSystem()
guideline = rag_system.generate_guideline(situation_info)

# 생성된 지침을 음성 안내로 출력
```

## 🐛 문제 해결

### 벡터 스토어를 찾을 수 없음

```bash
python build_vectorstore.py
```

### OpenAI API 키 오류

`.env` 파일에 `OPENAI_API_KEY`를 올바르게 설정했는지 확인하세요.

### 임베딩 모델 다운로드 오류

인터넷 연결을 확인하고, HuggingFace 모델이 자동으로 다운로드되도록 허용하세요.

### 문서 로딩 실패

- PDF 파일이 손상되지 않았는지 확인
- 파일 경로가 올바른지 확인
- 필요한 패키지가 설치되어 있는지 확인 (`pip install -r requirements.txt`)

## 📝 향후 개선 계획

- [ ] HWP 파일 완전 지원
- [ ] 대화 히스토리를 고려한 컨텍스트 인식 검색
- [ ] 다양한 임베딩 모델 지원
- [ ] 지침 생성 품질 평가 및 개선
- [ ] 실시간 문서 업데이트 지원

## 📄 라이선스

프로젝트 라이선스에 따릅니다.

