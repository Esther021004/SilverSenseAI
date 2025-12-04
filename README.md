# 🚑 Emergency Assistant - SilverSense AI

응급 상황을 자동으로 감지하고 분석하여 실시간 대처 지침을 제공하는 AI 기반 응급 지원 시스템입니다.

## SilverSense AI Architecture Viewer
https://20251203.netlify.app/
("SilverSense AI의 시스템 아키텍처를 시각화한 아키텍처 뷰어입니다.")

## 📋 프로젝트 개요

SilverSense AI는 음성(STT), 사운드 이벤트, 환경 신호를 종합 분석하여 응급 상황의 심각도를 판단하고, 혼자 있는 고령층을 위한 맞춤형 대처 지침을 생성합니다.

### 핵심 기능

- 🎤 **음성 인식 (STT)**: OpenAI Whisper를 사용한 한국어 음성-텍스트 변환
- 🔊 **사운드 분석**: PyTorch CNN 모델을 사용한 응급 사운드 이벤트 감지 (낙상, 화재 등)
- 🧠 **상황 분석**: A/B/C 모듈을 통한 종합 상황 분석 및 긴급도 판단 (S0~S7)
- 📚 **RAG 기반 지침 생성**: LangChain + ChromaDB를 사용한 검색 증강 생성으로 상황별 맞춤 응급 대처 지침 제공
- 💬 **대화형 AI**: Google Gemini API를 사용한 상황 기반 질문-답변 기능
- 🔊 **TTS**: Web Speech API를 사용한 지침 음성 안내
- 🌐 **웹 인터페이스**: FastAPI 기반 RESTful API 및 실시간 웹 인터페이스

## 🛠️ 기술 스택

### Backend
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증 및 설정 관리

### AI/ML
- **OpenAI Whisper**: 음성-텍스트 변환 (STT)
- **PyTorch**: 딥러닝 프레임워크 (CNN 모델)
- **Google Gemini API**: 
  - 상황 분석 및 융합 (gemini-flash-lite-latest)
  - RAG 기반 지침 생성 (gemini-2.0-flash)
  - 대화형 AI (gemini-2.0-flash)

### RAG (Retrieval-Augmented Generation)
- **LangChain**: LLM 애플리케이션 프레임워크
  - `langchain-core`: 핵심 기능
  - `langchain-community`: 커뮤니티 통합
  - `langchain-text-splitters`: 텍스트 분할
  - `langchain-openai`: OpenAI 통합
- **ChromaDB**: 벡터 데이터베이스 (임베딩 저장 및 검색)
- **Sentence Transformers**: 한국어 임베딩 모델 (jhgan/ko-sroberta-multitask)
- **pypdf**: PDF 문서 처리

### 오디오/비디오 처리
- **MoviePy**: 비디오에서 오디오 추출
- **librosa**: 오디오 신호 처리
- **FFmpeg**: 멀티미디어 프레임워크 (Whisper 의존성)

### 데이터 처리
- **NumPy**: 수치 연산
- **httpx**: HTTP 클라이언트

### Frontend
- **HTML5/CSS3/JavaScript**: 웹 인터페이스
- **Web Speech API**: 
  - SpeechRecognition: 음성 입력
  - SpeechSynthesis: 텍스트-음성 변환 (TTS)

### 개발 도구
- **python-dotenv**: 환경 변수 관리
- **python-multipart**: 파일 업로드 처리

### 배포/네트워킹
- **ngrok**: 로컬 서버 터널링 (선택적)

## 🏗️ 아키텍처

```
emergency-assistant/
├── main.py                          # FastAPI 서버 진입점
├── modules/                         # 분석 모듈
│   ├── module_a_speech.py          # A 모듈: 음성 분석
│   ├── module_b_sound.py           # B 모듈: 사운드 분석
│   ├── module_c_fusion.py          # C 모듈: 상황 융합
│   └── module_A/                   # Module A 구현
│       ├── intent_rules.py         # Intent 분류 규칙
│       └── server.py               # Module A 서버
├── services/                        # 서비스 레이어
│   ├── rag_client.py               # RAG 클라이언트
│   └── generative Ai project/      # RAG 시스템
│       └── rag/                    # RAG 구현
├── silversense_ai.html             # 웹 인터페이스
├── requirements.txt                 # Python 패키지 의존성
└── .env.example                     # 환경 변수 예시
```

## 🚀 시작하기

### 1. 저장소 클론

```bash
git clone https://github.com/your-username/emergency-assistant.git
cd emergency-assistant
```

### 2. 가상환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example`을 참고하여 `.env` 파일을 생성하고 API 키를 설정하세요:

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 API 키 입력
GEMINI_API_KEY=your_actual_api_key_here
```

**API 키 발급:**
- Gemini API: https://aistudio.google.com/app/apikey

### 5. FFmpeg 설치

Whisper STT 기능을 사용하려면 FFmpeg가 필요합니다.

**Windows:**
```cmd
winget install ffmpeg
# 또는
choco install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

### 6. 서버 실행

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 다음 주소로 접속할 수 있습니다:
- API 문서: http://localhost:8000/docs
- 웹 인터페이스: http://localhost:8000/app

## 📊 시스템 아키텍처

### 데이터 흐름

```
[음성/영상 파일] 
    ↓
[STT (Whisper)] → [A 모듈: 음성 분석] 
    ↓                    ↓
[오디오 추출] → [B 모듈: 사운드 분석]
    ↓                    ↓
[C 모듈: 상황 융합 (Gemini)] → [Situation JSON]
    ↓
[RAG 시스템] → [검색된 문서] + [Gemini] → [맞춤 지침]
    ↓
[웹 인터페이스] → [TTS] → [사용자]
```

### 모듈 구조

- **Module A (Speech)**: STT 텍스트를 분석하여 재난 유형, 긴급도, 감정 추출
- **Module B (Sound)**: CNN 모델로 사운드 이벤트 분류 (낙상, 화재, 갇힘 등)
- **Module C (Fusion)**: A+B 결과를 융합하여 최종 상황 JSON 생성 (S0~S7)
- **RAG System**: 상황별 맞춤 응급 대처 지침 생성
- **Conversational AI**: 상황 기반 질문-답변

## 🎯 주요 특징

- **모듈화 설계**: 각 모듈이 독립적으로 개발 및 업데이트 가능
- **실시간 처리**: 파일 업로드부터 지침 생성까지 자동화된 파이프라인
- **고령층 맞춤**: 혼자 있는 노인이 스스로 대처할 수 있는 구체적 지침
- **다중 입력 지원**: 음성, 오디오, 영상 파일 모두 지원
- **확장 가능**: 새로운 상황 유형 및 지침 추가 용이

## 📁 주요 파일 설명

### `main.py`
FastAPI 서버의 메인 파일입니다. 다음 기능을 제공합니다:
- `/api/emergency/analyze`: STT 텍스트와 사운드 이벤트를 받아 상황 분석
- `/api/emergency/analyze-video`: 영상/오디오 파일 업로드 및 분석
- `/api/emergency/ask`: 상황에 맞는 질문-답변
- `/app`: 웹 인터페이스 제공
- CORS 및 정적 파일 서빙

### `modules/`
- **module_a_speech.py**: 음성 텍스트를 분석하여 재난 유형, 긴급도, 감정 등을 추출
  - `modules/module_A/intent_rules.py`: 키워드 기반 Intent 분류
- **module_b_sound.py**: PyTorch CNN 모델을 사용하여 사운드 이벤트 분류 (낙상, 화재 등)
- **module_c_fusion.py**: A/B 모듈 결과를 융합하여 최종 상황 JSON 생성 (Gemini API 사용)
  - 상황 ID 결정 (S0~S7)
  - 긴급도 판단 (low/medium/high)

### `services/`
- **rag_client.py**: RAG 시스템과의 인터페이스
- **generative Ai project/rag/**: RAG 시스템 구현
  - `rag_system.py`: RAG 시스템 메인 클래스
  - `guideline_generator.py`: 지침 생성기 (LangChain + Gemini)
  - `embedding_store.py`: ChromaDB 벡터 스토어 관리
  - `document_loader.py`: PDF 문서 로더
  - `text_splitter.py`: 텍스트 분할
  - `gemini_adapter.py`: Gemini API 어댑터

### `silversense_ai.html`
웹 인터페이스:
- 파일 업로드 및 분석
- 결과 시각화
- TTS 기능
- 대화형 AI (음성/텍스트 질문)

## 🔧 설정

### 필수 요구사항

1. **Python 3.8 이상**
2. **FFmpeg**: Whisper STT 기능 사용 시 필요
   - Windows: `winget install ffmpeg` 또는 `choco install ffmpeg`
   - 자세한 내용: [INSTALL_FFMPEG.md](INSTALL_FFMPEG.md)

### 모델 파일

다음 모델 파일이 필요합니다 (GitHub에는 포함되지 않음):
- `aed_cnn_final_trainaug_fin.pth`: B 모듈 CNN 모델 (프로젝트 루트)
- Whisper 모델: 자동 다운로드 (첫 실행 시 `~/.cache/whisper/`에 저장)

### RAG 문서

RAG 시스템을 사용하려면 `services/generative Ai project/document/` 폴더에 응급처치 관련 PDF 문서가 필요합니다.

### 환경 변수

`.env` 파일을 생성하고 다음을 설정하세요:
```env
GEMINI_API_KEY=your_api_key_here
```

API 키 발급: https://aistudio.google.com/app/apikey

## 📝 API 사용 예시

### 파일 업로드 및 분석

```python
import requests

url = "http://localhost:8000/api/emergency/analyze-video"
files = {"file": open("emergency_audio.wav", "rb")}
response = requests.post(url, files=files)
result = response.json()

print("상황:", result["situation"])
print("지침:", result["guideline"])
```

### 질문-답변

```python
import requests

url = "http://localhost:8000/api/emergency/ask"
data = {
    "question": "다리가 너무 아픈데 어떻게 해야 하나요?",
    "situation": {
        "situation_id": "S3",
        "emergency_level": "medium",
        "symptoms": ["fall", "possible_fracture"]
    }
}
response = requests.post(url, json=data)
print(response.json()["answer"])
```

## 🧪 테스트

### STT 테스트

```bash
python test_stt.py temp_media/test_audio.wav
```

### 전체 파이프라인 테스트

웹 인터페이스에서 파일을 업로드하여 테스트할 수 있습니다.

## 📚 문서

### 설치 및 설정
- [서버 시작 가이드](START_SERVER.md)
- [FFmpeg 설치 가이드](INSTALL_FFMPEG.md)
- [GitHub 업로드 가이드](GITHUB_UPLOAD_GUIDE.md)

### 테스트 및 개발
- [STT 테스트 가이드](TEST_STT_GUIDE.md)
- [웹 개발자 가이드](WEB_DEVELOPER_GUIDE.md)

### 네트워크 및 배포
- [ngrok 사용 가이드](NGROK_USAGE.md)
- [사용자 접근 가이드](USER_ACCESS_GUIDE.md)

## 🤝 기여

이슈나 풀 리퀘스트를 환영합니다!

## 📈 성능 및 제한사항

### 처리 시간
- STT: 약 5-10초 (파일 크기에 따라 다름)
- 사운드 분석: 약 1-2초
- 상황 융합: 약 2-5초 (Gemini API 응답 시간)
- RAG 지침 생성: 약 3-8초 (문서 검색 + 생성)

### 제한사항
- Whisper 모델: CPU에서 실행 시 느릴 수 있음 (GPU 권장)
- Gemini API: 무료 티어 할당량 제한 (분당 요청 수 제한)
- 파일 크기: 업로드 파일 크기 제한 (기본적으로 서버 설정에 따름)

## 🔐 보안

- API 키는 환경 변수로 관리 (`.env` 파일 사용)
- `.env` 파일은 Git에 포함되지 않음 (`.gitignore`에 포함)
- 프로덕션 환경에서는 HTTPS 사용 권장

## 👥 기여자

- Module A: 음성 분석 - 조예진
- Module B: 사운드 분석 - 김수빈
- Module C: 상황 융합 - 문혜원
- RAG 지침 생성 - 문혜원



