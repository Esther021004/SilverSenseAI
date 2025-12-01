# 🚑 Emergency Assistant - SilverSense AI

응급 상황을 자동으로 감지하고 분석하여 실시간 대처 지침을 제공하는 AI 기반 응급 지원 시스템입니다.

## 📋 프로젝트 개요

SilverSense AI는 음성(STT), 사운드 이벤트, 환경 신호를 종합 분석하여 응급 상황의 심각도를 판단하고, 혼자 있는 고령층을 위한 맞춤형 대처 지침을 생성합니다.

### 주요 기능

- 🎤 **음성 인식 (STT)**: Whisper 모델을 사용한 한국어 음성-텍스트 변환
- 🔊 **사운드 분석**: CNN 모델을 사용한 응급 사운드 이벤트 감지 (낙상, 화재 등)
- 🧠 **상황 분석**: A/B/C 모듈을 통한 종합 상황 분석 및 긴급도 판단
- 📚 **RAG 기반 지침 생성**: 검색 증강 생성으로 상황별 맞춤 응급 대처 지침 제공
- 💬 **대화형 AI**: 상황에 맞는 질문-답변 기능
- 🔊 **TTS**: 생성된 지침을 음성으로 읽어주는 기능

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

## 📁 주요 파일 설명

### `main.py`
FastAPI 서버의 메인 파일입니다. 다음 기능을 제공합니다:
- `/api/emergency/analyze`: STT 텍스트와 사운드 이벤트를 받아 상황 분석
- `/api/emergency/analyze-video`: 영상/오디오 파일 업로드 및 분석
- `/api/emergency/ask`: 상황에 맞는 질문-답변

### `modules/`
- **module_a_speech.py**: 음성 텍스트를 분석하여 재난 유형, 긴급도, 감정 등을 추출
- **module_b_sound.py**: CNN 모델을 사용하여 사운드 이벤트 분류 (낙상, 화재 등)
- **module_c_fusion.py**: A/B 모듈 결과를 융합하여 최종 상황 JSON 생성 (Gemini API 사용)

### `services/rag_client.py`
RAG 시스템과의 인터페이스입니다. 상황 JSON을 받아 응급 대처 지침을 생성합니다.

## 🔧 설정

### 모델 파일

다음 모델 파일이 필요합니다 (GitHub에는 포함되지 않음):
- `aed_cnn_final_trainaug_fin.pth`: B 모듈 CNN 모델
- `modules/module_A/weights/small.pt`: Whisper 모델 (자동 다운로드)

### RAG 문서

RAG 시스템을 사용하려면 `services/generative Ai project/document/` 폴더에 응급처치 관련 PDF 문서가 필요합니다.


## 📦 모델 파일 다운로드

다음 모델 파일이 필요합니다 (GitHub에는 포함되지 않음):

1. **B 모듈 CNN 모델**: `aed_cnn_final_trainaug_fin.pth`
   - 프로젝트 루트에 배치

2. **Module A Whisper 모델**: `modules/module_A/weights/small.pt`
   - Whisper가 자동으로 다운로드하거나 수동 다운로드 가능

3. **RAG 문서**: `services/generative Ai project/document/`
   - 응급처치 관련 PDF 문서 필요

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

- [STT 테스트 가이드](TEST_STT_GUIDE.md)
- [FFmpeg 설치 가이드](INSTALL_FFMPEG.md)
- [서버 시작 가이드](START_SERVER.md)

## 🤝 기여

이슈나 풀 리퀘스트를 환영합니다!

## 📄 라이선스

[라이선스 정보를 여기에 추가하세요]

## 👥 팀

- Module A: 음성 분석
- Module B: 사운드 분석
- Module C: 상황 융합 및 RAG

## 🙏 감사의 말

- OpenAI Whisper: STT 기능
- Google Gemini: 상황 분석 및 지침 생성
- FastAPI: 웹 프레임워크
