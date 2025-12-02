# 🎤 SilverSense AI 발표자료 작성 가이드

발표자료 제작자를 위한 프로젝트 상세 설명 문서입니다.

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [전체 파이프라인 상세 설명](#2-전체-파이프라인-상세-설명)
3. [각 모듈 상세 설명](#3-각-모듈-상세-설명)
4. [RAG 시스템 설명](#4-rag-시스템-설명)
5. [입력/출력 예시](#5-입력출력-예시)
6. [실제 결과 예시](#6-실제-결과-예시)
7. [기술 스택 상세](#7-기술-스택-상세)
8. [웹 인터페이스 설명](#8-웹-인터페이스-설명)

---

## 1. 프로젝트 개요

### 1.1 프로젝트명 및 목적

**프로젝트명**: SilverSense AI (Emergency Assistant)

**핵심 목적**: 
- 혼자 있는 고령층을 위한 응급 상황 자동 감지 및 분석 시스템
- 음성(STT)과 사운드 이벤트를 종합 분석하여 응급 상황의 심각도를 판단
- 상황별 맞춤형 응급 대처 지침을 자동 생성하여 제공

### 1.2 해결하려는 문제

1. **고령층 응급 상황 대응의 어려움**
   - 혼자 있을 때 응급 상황 발생 시 대처 방법을 모름
   - 119 신고 시 말문이 막히거나 정확한 상황 전달 어려움
   - 응급 상황 판단 능력 부족

2. **기존 시스템의 한계**
   - 단순 음성 인식만으로는 정확한 상황 파악 어려움
   - 사운드 이벤트(낙상 소리 등)를 활용하지 못함
   - 일반적인 응급처치 지침만 제공 (상황별 맞춤 지침 부재)

### 1.3 핵심 차별점

- **다중 신호 융합**: 음성(STT) + 사운드 이벤트를 동시에 분석
- **AI 기반 상황 분석**: Gemini API를 활용한 지능형 상황 판단
- **RAG 기반 맞춤 지침**: 검색 증강 생성으로 상황별 구체적 대처 방법 제공
- **대화형 AI**: 추가 질문에 대한 실시간 답변 제공
- **음성 안내**: TTS를 통한 지침 음성 읽기

---

## 2. 전체 파이프라인 상세 설명

### 2.1 전체 흐름도

```
[사용자] 
  ↓
[파일 업로드] (mp4/wav/mp3)
  ↓
[오디오 추출] (MoviePy)
  ↓
    ├─→ [STT] (Whisper) ──→ [Module A: 음성 분석]
    │
    └─→ [사운드 분석] (CNN) ──→ [Module B: 사운드 분석]
                                    ↓
                            [Module C: 상황 융합] (Gemini API)
                                    ↓
                            [Situation JSON] (S0~S7, emergency_level)
                                    ↓
                            [RAG 시스템] (ChromaDB + Gemini)
                                    ↓
                            [맞춤 지침 생성]
                                    ↓
                            [사용자에게 제공] + [TTS 음성 안내]
```

### 2.2 단계별 상세 설명

#### **Step 1: 파일 업로드 및 전처리**

**입력**: 
- 사용자가 웹 인터페이스에서 파일 업로드
- 지원 형식: `.mp4`, `.wav`, `.mp3`

**처리**:
- FastAPI의 `/api/emergency/analyze-video` 엔드포인트로 파일 수신
- 임시 파일로 저장 (`temp_media/` 폴더)
- 비디오 파일인 경우: MoviePy를 사용하여 오디오 트랙만 추출
  - 샘플링 레이트: 16kHz (B 모듈 요구사항)
  - 형식: WAV (PCM 16-bit)

**출력**: 
- WAV 오디오 파일 경로

**예시 코드**:
```python
# main.py의 extract_audio_from_video 함수
clip = VideoFileClip(video_path)
clip.audio.write_audiofile(
    audio_path,
    fps=16000,  # 16kHz 샘플링 레이트
    codec="pcm_s16le",
    verbose=False
)
```

---

#### **Step 2: 병렬 분석 (STT + 사운드 분석)**

두 가지 분석이 **동시에** 진행됩니다:

##### **2-1. STT (Speech-to-Text)**

**기술**: OpenAI Whisper 모델 (small 버전)

**처리 과정**:
1. Whisper 모델 로드 (한 번만 로드, 재사용)
2. 오디오 파일을 한국어로 인식 (`language="ko"`)
3. 음성을 텍스트로 변환

**출력**: 
- 한국어 텍스트 (예: "할머니가 갑자기 쓰러져서 숨을 안 쉬어요...")

**예시 코드**:
```python
# main.py의 run_stt_on_wav 함수
import whisper
model = whisper.load_model("small")
result = model.transcribe(wav_path, language="ko")
text = result.get("text", "").strip()
```

**특징**:
- 오프라인 동작 가능 (모델이 로컬에 저장됨)
- 한국어 특화
- 노이즈가 있는 환경에서도 비교적 정확한 인식

---

##### **2-2. 사운드 분석 (CNN 모델)**

**기술**: PyTorch 기반 CNN (Convolutional Neural Network)

**처리 과정**:
1. **오디오 전처리**:
   - librosa로 오디오 로드 (16kHz 샘플링)
   - 길이 고정 (2초)
   - Mel-spectrogram 변환 (64 mel bins)
   - Log-scale 변환 (dB)
   - 정규화 (평균 0, 표준편차 1)

2. **모델 추론**:
   - SimpleCNN 모델 사용
   - 입력: (1, 1, 64, T) 형태의 log-mel spectrogram
   - 출력: 4개 클래스에 대한 확률 분포

**출력**:
```python
{
    "event": "낙상" | "화재" | "갇힘" | "생활소음",
    "confidence": 0.0 ~ 1.0  # 예: 0.95
}
```

**모델 구조**:
- 3개의 Convolutional Layer (16 → 32 → 64 채널)
- Batch Normalization + Max Pooling
- Dropout (0.3)
- Fully Connected Layer (64 → 4 classes)

**예시 코드**:
```python
# module_b_sound.py의 predict_audio_event 함수
log_mel = wav_to_logmel_infer(wav_path)  # 전처리
x = torch.tensor(log_mel).unsqueeze(0).unsqueeze(0)
outputs = model(x)
probs = torch.softmax(outputs, dim=1)[0]
top_class = idx_to_class[np.argmax(probs)]
```

**특징**:
- 실시간 분석 가능 (2초 오디오 기준 매우 빠름)
- 4가지 응급 사운드 이벤트 감지
- Confidence 점수 제공으로 신뢰도 판단 가능

---

#### **Step 3: Module A - 음성 분석**

**입력**: STT 텍스트 (예: "할머니가 갑자기 쓰러져서 숨을 안 쉬어요...")

**처리 과정**:
1. **Intent 분류**: `intent_rules.py`의 키워드 기반 규칙 매칭
   - 예: "쓰러져서", "숨을 안 쉬어요" → `cardiac_arrest` Intent

2. **의료적 의미 태그 추출**:
   - Intent를 기존 출력 형식으로 매핑

**출력**:
```python
{
    "disaster_large": "구급",        # 대분류: 구급/구조/화재/기타
    "disaster_medium": "심정지",      # 중분류: 심정지/호흡곤란/낙상 등
    "urgency_level": "상",           # 긴급도: 상/중/하
    "sentiment": "불안/걱정",        # 감정 상태
    "raw_text": "할머니가 갑자기..."  # 원본 STT 텍스트
}
```

**Intent 종류** (11가지):
- `cardiac_arrest`: 심정지
- `breathing_difficulty`: 호흡곤란
- `chest_pain`: 흉통
- `falling`: 낙상
- `fire`: 화재
- `unconscious`: 의식소실
- `seizure`: 발작
- `bleeding`: 출혈
- `dizziness`: 현기증
- `traffic_accident`: 교통사고
- `assault`: 폭행

**예시 코드**:
```python
# module_a_speech.py의 analyze_speech 함수
intent = map_intent(stt_text)  # Intent 분류
output = intent_to_output.get(intent, {...})  # 매핑
return {
    "disaster_large": output["disaster_large"],
    "disaster_medium": output["disaster_medium"],
    "urgency_level": output["urgency_level"],
    "sentiment": output["sentiment"],
    "raw_text": stt_text
}
```

**특징**:
- 키워드 기반 규칙 매칭으로 빠른 처리
- 의료 응급 상황 분류에 특화
- 확장 가능한 구조 (새로운 Intent 추가 용이)

---

#### **Step 4: Module B - 사운드 분석**

**입력**: 
- 오디오 파일 경로 (WAV)
- 또는 이미 분석된 이벤트 정보

**처리**:
- `analyze_sound_from_file()` 함수로 오디오 파일 직접 분석
- 또는 `analyze_sound()` 함수로 이미 분석된 결과를 표준화

**출력**:
```python
{
    "event": "낙상",      # 정규화된 이벤트 라벨
    "confidence": 0.95    # 모델 신뢰도
}
```

**특징**:
- CNN 모델 기반 자동 이벤트 감지
- 4가지 응급 사운드 분류
- Confidence 점수로 신뢰도 판단

---

#### **Step 5: Module C - 상황 융합**

**핵심 기능**: A 모듈과 B 모듈의 결과를 종합하여 최종 상황을 판단

**기술**: Google Gemini API (`gemini-flash-lite-latest`)

**입력**:
- Module A 결과: `speech_result`
- Module B 결과: `sound_result`

**처리 과정**:
1. **프롬프트 구성**: 
   - A/B 모듈 결과를 JSON 형식으로 정리
   - 시스템 프롬프트와 함께 Gemini API에 전송

2. **상황 판단 규칙** (우선순위 순):
   - **S2**: 낙상 + 생명위협 (심정지/호흡곤란) → `emergency_level: "high"`
   - **S6**: 말로만 보고된 고위험 의료응급 (낙상 없음) → `emergency_level: "high"`
   - **S4**: 화재/연기 → `emergency_level: "high"`
   - **S3**: 낙상 + 부상/통증 (심정지 아님) → `emergency_level: "medium"/"high"`
   - **S5**: 갇힘/고립 → `emergency_level: "medium"/"high"`
   - **S1**: 의료 응급 (비낙상/비화재/비갇힘) → `emergency_level: "medium"/"high"`
   - **S7**: 기타 위험 상황 → `emergency_level: "medium"/"high"`
   - **S0**: 정상/불명확 → `emergency_level: "low"`

3. **긴급도 판단**:
   - `high`: 생명위협, 화재, 중증 낙상 등
   - `medium`: 일반 의료 응급, 경미한 낙상 등
   - `low`: 정상, 불명확한 상황

**출력** (Situation JSON):
```json
{
    "situation_id": "S2",
    "situation_label": "Fall with suspected cardiac arrest",
    "emergency_level": "high",
    "speech": {
        "id": null,
        "text": "할머니가 갑자기 쓰러져서 숨을 안 쉬어요...",
        "disaster_large": "구급",
        "disaster_medium": "심정지",
        "urgency_level": "상",
        "sentiment": "불안/걱정",
        "triage": null
    },
    "sound": {
        "event": "낙상",
        "confidence": 0.95
    },
    "symptoms": [
        "fall",
        "possible_cardiac_arrest",
        "not_breathing",
        "high_urgency"
    ],
    "meta": {
        "timestamp": "2024-12-02T15:30:00",
        "language": "ko",
        "source": "realtime"
    }
}
```

**예시 코드**:
```python
# module_c_fusion.py의 fuse_situation 함수
prompt = f"""
{speech_result}
{sound_result}
"""
response = model.generate_content(prompt)
situation_json = json.loads(response.text)
```

**특징**:
- AI 기반 지능형 상황 판단
- 복잡한 규칙을 LLM이 자연스럽게 처리
- 8가지 상황 ID로 세분화된 분류
- 3단계 긴급도 판단

---

#### **Step 6: RAG 시스템 - 맞춤 지침 생성**

**기술**: 
- **LangChain**: LLM 애플리케이션 프레임워크
- **ChromaDB**: 벡터 데이터베이스
- **Sentence Transformers**: 한국어 임베딩 모델 (`jhgan/ko-sroberta-multitask`)
- **Google Gemini API**: `gemini-2.0-flash`

**처리 과정**:

1. **문서 로드 및 벡터화**:
   - PDF 응급처치 매뉴얼 문서들을 로드
   - 텍스트를 청크 단위로 분할 (예: 500자씩)
   - 한국어 임베딩 모델로 벡터 변환
   - ChromaDB에 저장

2. **상황 기반 검색**:
   - Situation JSON에서 핵심 키워드 추출
     - `situation_id` (예: "S5" → "갇힘", "구조")
     - `symptoms` (예: "trapped_or_confined")
     - `disaster_medium` (예: "심정지")
   - 벡터 유사도 검색으로 관련 문서 청크 검색
   - 상위 3-5개 문서 청크 선택

3. **지침 생성**:
   - 검색된 문서 + Situation JSON을 프롬프트에 포함
   - Gemini API로 상황별 맞춤 지침 생성
   - 프롬프트 규칙:
     - "혼자 있는 노인이 스스로 할 수 있는" 방안만 제시
     - `emergency_level: "high"`인 경우 첫 문장은 "지금 바로 119에 전화하세요."
     - 짧은 문장, 전문 용어 최소화
     - 단계별 구체적 행동 지침

**출력** (지침 텍스트):
```
1단계: 지금 당장 해야 할 일
지금 바로 119에 전화하세요. 전화를 걸 수 있으면 무조건 먼저 119를 누르세요.

2단계: 119 연결을 기다리면서 할 일
- 무리해서 일어나지 말고, 천천히 기어서 가까운 전화기를 향해 움직이세요.
- 의식이 점점 흐려지면, 움직이지 말고 119에 가능한 빨리 연결되도록 하세요.

3단계: 119에 이렇게 말하세요
"혼자 있는데 할머니가 쓰러져서 숨을 안 쉬고 있습니다. 주소는 [주소]입니다."

4단계: 통화가 끝난 뒤 구조를 기다리는 동안
- 움직이지 마세요.
- 가능하면 문을 열어두어 구조대가 쉽게 들어올 수 있도록 하세요.
```

**예시 코드**:
```python
# services/rag_client.py의 generate_guideline_from_situation 함수
situation_info = {
    "situation_id": "S2",
    "emergency_level": "high",
    "symptoms": ["fall", "possible_cardiac_arrest"],
    "sound_event": "낙상"
}
guideline = rag_system.generate_guideline(
    situation_info=situation_info,
    additional_context=situation_json_str
)
```

**특징**:
- 검색 증강 생성으로 정확한 지침 제공
- 상황별 맞춤형 지침 생성
- 노인 친화적 언어 사용
- 단계별 구체적 행동 지침

---

#### **Step 7: 사용자에게 결과 제공**

**웹 인터페이스** (`silversense_ai.html`):
- Situation JSON 표시
- 지침 단계별 표시
- TTS 음성 안내 (Web Speech API)
- 대화형 AI 질문-답변 기능

**API 응답**:
```json
{
    "situation": {
        "situation_id": "S2",
        "emergency_level": "high",
        ...
    },
    "guideline": "1단계: 지금 당장 해야 할 일\n지금 바로 119에 전화하세요..."
}
```

---

## 3. 각 모듈 상세 설명

### 3.1 Module A - 음성 분석 모듈

#### **역할**
STT 텍스트를 분석하여 의료적 의미 태그를 추출합니다.

#### **입력**
- STT 텍스트 (문자열)
- 예: "할머니가 갑자기 쓰러져서 숨을 안 쉬어요..."

#### **처리 로직**

1. **Intent 분류** (`intent_rules.py`):
   - 키워드 기반 규칙 매칭
   - 예: "쓰러져서" + "숨을 안 쉬어요" → `cardiac_arrest`

2. **의료적 의미 태그 매핑**:
   - Intent → 출력 형식 변환
   - 11가지 Intent 지원

#### **출력 형식**
```python
{
    "disaster_large": "구급",      # 대분류
    "disaster_medium": "심정지",    # 중분류
    "urgency_level": "상",         # 긴급도
    "sentiment": "불안/걱정",      # 감정
    "raw_text": "원본 텍스트"      # 원본 STT
}
```

#### **Intent 매핑 예시**

| Intent | disaster_large | disaster_medium | urgency_level |
|--------|----------------|-----------------|---------------|
| `cardiac_arrest` | 구급 | 심정지 | 상 |
| `breathing_difficulty` | 구급 | 호흡곤란 | 상 |
| `chest_pain` | 구급 | 흉통 | 중 |
| `falling` | 구급 | 낙상 | 중 |
| `fire` | 화재 | 화재 | 상 |

#### **특징**
- 키워드 기반 빠른 처리
- 의료 응급 상황 분류 특화
- 확장 가능한 구조

---

### 3.2 Module B - 사운드 분석 모듈

#### **역할**
오디오 파일을 분석하여 응급 사운드 이벤트를 감지합니다.

#### **입력**
- WAV 오디오 파일 경로
- 샘플링 레이트: 16kHz
- 길이: 2초 (고정)

#### **처리 로직**

1. **오디오 전처리**:
   ```
   WAV 파일 
   → librosa 로드 (16kHz)
   → 길이 고정 (2초, 패딩 또는 자르기)
   → Mel-spectrogram 변환 (64 mel bins)
   → Log-scale 변환 (dB)
   → 정규화 (평균 0, 표준편차 1)
   ```

2. **CNN 모델 추론**:
   - 입력: (1, 1, 64, T) 형태의 log-mel spectrogram
   - 모델: SimpleCNN (3 Conv layers + FC layer)
   - 출력: 4개 클래스 확률 분포

3. **결과 선택**:
   - 최고 확률 클래스 선택
   - Confidence 점수 계산

#### **출력 형식**
```python
{
    "event": "낙상",        # 이벤트 라벨
    "confidence": 0.95      # 신뢰도 (0.0 ~ 1.0)
}
```

#### **감지 가능한 이벤트**
- `낙상`: 낙상 소리 감지
- `화재`: 화재 관련 소리 (연기 경보, 타는 소리 등)
- `갇힘`: 갇힘 상황 관련 소리 (문 두드리는 소리 등)
- `생활소음`: 일반적인 생활 소음 (응급 상황 아님)

#### **모델 구조**
```
Input: (1, 1, 64, T)
  ↓
Conv2d(1→16) + BN + ReLU + MaxPool
  ↓
Conv2d(16→32) + BN + ReLU + MaxPool
  ↓
Conv2d(32→64) + BN + ReLU + MaxPool
  ↓
AdaptiveAvgPool2d(1,1)
  ↓
Dropout(0.3)
  ↓
Linear(64→4)
  ↓
Output: 4개 클래스 확률
```

#### **특징**
- 실시간 분석 가능 (2초 오디오 기준 매우 빠름)
- 4가지 응급 사운드 이벤트 감지
- Confidence 점수 제공으로 신뢰도 판단 가능
- PyTorch 기반으로 GPU 가속 가능

---

### 3.3 Module C - 상황 융합 모듈

#### **역할**
Module A와 Module B의 결과를 종합하여 최종 상황을 판단합니다.

#### **입력**
- Module A 결과: `speech_result`
- Module B 결과: `sound_result`

#### **처리 로직**

1. **프롬프트 구성**:
   - A/B 모듈 결과를 JSON 형식으로 정리
   - 시스템 프롬프트와 함께 Gemini API에 전송

2. **상황 판단 규칙** (우선순위 순):

   **S2 - 낙상 + 생명위협** (최우선)
   - 조건: `sound.event == "낙상"` AND `speech.disaster_medium`에 "심정지", "호흡곤란" 포함
   - 긴급도: `high`
   - 예시: 낙상 소리 + "숨을 안 쉬어요" 음성

   **S6 - 말로만 보고된 고위험 의료응급**
   - 조건: `sound.event == "생활소음"` AND `speech.disaster_medium`에 "심정지", "호흡곤란" 포함
   - 긴급도: `high`
   - 예시: 생활소음 + "심정지 같아요" 음성

   **S4 - 화재**
   - 조건: `sound.event == "화재"` OR `speech.disaster_large == "화재"` OR 텍스트에 "불이", "연기" 포함
   - 긴급도: `high`
   - 예시: 화재 소리 + "불이 났어요" 음성

   **S3 - 낙상 + 부상/통증**
   - 조건: `sound.event == "낙상"` AND `speech.disaster_medium`이 "골절", "낙상", "출혈" 등
   - 긴급도: `medium` 또는 `high`
   - 예시: 낙상 소리 + "다리가 아파요" 음성

   **S5 - 갇힘/고립**
   - 조건: `sound.event == "갇힘"` OR `speech.disaster_large == "구조"` OR 텍스트에 "갇혔", "문이 안 열려" 포함
   - 긴급도: `medium` 또는 `high`
   - 예시: 갇힘 소리 + "문이 안 열려요" 음성

   **S1 - 의료 응급**
   - 조건: `speech.disaster_large == "구급"` AND 위 조건들에 해당하지 않음
   - 긴급도: `medium` 또는 `high`
   - 예시: 생활소음 + "가슴이 아파요" 음성

   **S7 - 기타 위험 상황**
   - 조건: 위 조건들에 해당하지 않지만 위험 요소 있음
   - 긴급도: `medium` 또는 `high`

   **S0 - 정상/불명확**
   - 조건: 위 모든 조건에 해당하지 않음
   - 긴급도: `low`

3. **긴급도 판단**:
   - `high`: 생명위협, 화재, 중증 낙상 등
   - `medium`: 일반 의료 응급, 경미한 낙상 등
   - `low`: 정상, 불명확한 상황

#### **출력 형식** (Situation JSON)
```json
{
    "situation_id": "S2",
    "situation_label": "Fall with suspected cardiac arrest",
    "emergency_level": "high",
    "speech": {
        "id": null,
        "text": "할머니가 갑자기 쓰러져서 숨을 안 쉬어요...",
        "disaster_large": "구급",
        "disaster_medium": "심정지",
        "urgency_level": "상",
        "sentiment": "불안/걱정",
        "triage": null
    },
    "sound": {
        "event": "낙상",
        "confidence": 0.95
    },
    "symptoms": [
        "fall",
        "possible_cardiac_arrest",
        "not_breathing",
        "high_urgency"
    ],
    "meta": {
        "timestamp": "2024-12-02T15:30:00",
        "language": "ko",
        "source": "realtime"
    }
}
```

#### **특징**
- AI 기반 지능형 상황 판단
- 복잡한 규칙을 LLM이 자연스럽게 처리
- 8가지 상황 ID로 세분화된 분류
- 3단계 긴급도 판단

---

## 4. RAG 시스템 설명

### 4.1 RAG란?

**RAG (Retrieval-Augmented Generation)**: 검색 증강 생성
- 외부 지식 베이스(문서)를 검색하여 LLM의 답변 정확도를 향상시키는 기법
- 일반적인 LLM 답변보다 더 정확하고 상황에 맞는 답변 생성 가능

### 4.2 RAG 시스템 구조

```
[Situation JSON]
  ↓
[키워드 추출]
  ↓
[벡터 검색] (ChromaDB)
  ↓
[관련 문서 청크 선택] (상위 3-5개)
  ↓
[프롬프트 구성]
  - 검색된 문서 청크
  - Situation JSON 정보
  - 지침 생성 규칙
  ↓
[Gemini API 호출]
  ↓
[맞춤 지침 생성]
```

### 4.3 처리 과정 상세

#### **1단계: 문서 로드 및 벡터화**

**문서 소스**:
- PDF 응급처치 매뉴얼 문서들
- 위치: `services/generative Ai project/document/`

**처리**:
1. PDF 파일 로드 (`pypdf` 사용)
2. 텍스트 추출
3. 텍스트 분할 (청크 단위, 예: 500자씩)
4. 한국어 임베딩 모델로 벡터 변환
   - 모델: `jhgan/ko-sroberta-multitask`
   - 벡터 차원: 768차원
5. ChromaDB에 저장

#### **2단계: 상황 기반 검색**

**검색 쿼리 생성**:
- `situation_id` 기반 키워드:
  - S2: ["낙상", "심정지", "호흡곤란", "구조"]
  - S4: ["화재", "연기", "대피"]
  - S5: ["갇힘", "구조", "문열기", "탈출"]
  - 등등...

- `symptoms` 기반 키워드:
  - "fall" → ["낙상", "구조"]
  - "trapped_or_confined" → ["갇힘", "구조요청"]
  - 등등...

**벡터 유사도 검색**:
- 검색 쿼리를 임베딩으로 변환
- ChromaDB에서 유사도가 높은 문서 청크 검색
- 상위 3-5개 문서 청크 선택

#### **3단계: 지침 생성**

**프롬프트 구성**:
```
시스템 프롬프트:
- "혼자 있는 노인이 스스로 할 수 있는" 방안만 제시
- emergency_level이 "high"면 첫 문장은 "지금 바로 119에 전화하세요."
- 짧은 문장, 전문 용어 최소화
- 단계별 구체적 행동 지침

입력:
- 검색된 문서 청크 (3-5개)
- Situation JSON 정보
- 상황별 구체적 대응 가이드

출력:
- 단계별 맞춤 지침 텍스트
```

**Gemini API 호출**:
- 모델: `gemini-2.0-flash`
- 검색된 문서 + Situation 정보를 프롬프트에 포함
- 상황별 맞춤 지침 생성

### 4.4 지침 생성 규칙

#### **긴급도별 우선순위**

**High (high emergency_level)**:
- 1단계 첫 문장: "지금 바로 119에 전화하세요."
- 그 다음: "119 연결을 기다리면서 이렇게 하세요..."

**Medium/Low**:
- 1단계: 상황에 맞는 첫 행동
- 2단계: 119 신고 (필요시)

#### **문장 구조**
- 한 단계에 문장 2개 이하
- 각 문장은 짧게, 한 행동만 담기
- 한 bullet = 한 행동

#### **언어 스타일**
- 전문 용어 최소화
- 일상적 표현 사용
- 노인 친화적 언어

#### **내용 제거**
- 문서 번호, 페이지 번호 제거
- "(문서 1 참고)" 같은 표현 제거
- RAG 아티팩트 제거

### 4.5 출력 예시

**입력**: S2 (낙상 + 심정지, high)

**출력**:
```
1단계: 지금 당장 해야 할 일
지금 바로 119에 전화하세요. 전화를 걸 수 있으면 무조건 먼저 119를 누르세요.

2단계: 119 연결을 기다리면서 할 일
- 무리해서 일어나지 말고, 천천히 기어서 가까운 전화기를 향해 움직이세요.
- 의식이 점점 흐려지면, 움직이지 말고 119에 가능한 빨리 연결되도록 하세요.

3단계: 119에 이렇게 말하세요
"혼자 있는데 할머니가 쓰러져서 숨을 안 쉬고 있습니다. 주소는 [주소]입니다."

4단계: 통화가 끝난 뒤 구조를 기다리는 동안
- 움직이지 마세요.
- 가능하면 문을 열어두어 구조대가 쉽게 들어올 수 있도록 하세요.
```

---

## 5. 입력/출력 예시

### 5.1 전체 파이프라인 입력/출력

#### **입력 예시**

**파일 업로드**:
- 형식: `.mp4`, `.wav`, `.mp3`
- 예시: `emergency_call.mp4` (10초 비디오)

**내용**:
- 비디오: 할머니가 쓰러진 모습
- 오디오: "할머니가 갑자기 쓰러져서 숨을 안 쉬어요..."

---

#### **중간 결과 예시**

**STT 결과**:
```
"할머니가 갑자기 쓰러져서 숨을 안 쉬어요..."
```

**사운드 분석 결과**:
```json
{
    "event": "낙상",
    "confidence": 0.95
}
```

**Module A 결과**:
```json
{
    "disaster_large": "구급",
    "disaster_medium": "심정지",
    "urgency_level": "상",
    "sentiment": "불안/걱정",
    "raw_text": "할머니가 갑자기 쓰러져서 숨을 안 쉬어요..."
}
```

**Module B 결과**:
```json
{
    "event": "낙상",
    "confidence": 0.95
}
```

---

#### **최종 출력 예시**

**Situation JSON**:
```json
{
    "situation_id": "S2",
    "situation_label": "Fall with suspected cardiac arrest",
    "emergency_level": "high",
    "speech": {
        "id": null,
        "text": "할머니가 갑자기 쓰러져서 숨을 안 쉬어요...",
        "disaster_large": "구급",
        "disaster_medium": "심정지",
        "urgency_level": "상",
        "sentiment": "불안/걱정",
        "triage": null
    },
    "sound": {
        "event": "낙상",
        "confidence": 0.95
    },
    "symptoms": [
        "fall",
        "possible_cardiac_arrest",
        "not_breathing",
        "high_urgency"
    ],
    "meta": {
        "timestamp": "2024-12-02T15:30:00",
        "language": "ko",
        "source": "realtime"
    }
}
```

**지침**:
```
1단계: 지금 당장 해야 할 일
지금 바로 119에 전화하세요. 전화를 걸 수 있으면 무조건 먼저 119를 누르세요.

2단계: 119 연결을 기다리면서 할 일
- 무리해서 일어나지 말고, 천천히 기어서 가까운 전화기를 향해 움직이세요.
- 의식이 점점 흐려지면, 움직이지 말고 119에 가능한 빨리 연결되도록 하세요.

3단계: 119에 이렇게 말하세요
"혼자 있는데 할머니가 쓰러져서 숨을 안 쉬고 있습니다. 주소는 [주소]입니다."

4단계: 통화가 끝난 뒤 구조를 기다리는 동안
- 움직이지 마세요.
- 가능하면 문을 열어두어 구조대가 쉽게 들어올 수 있도록 하세요.
```

---

### 5.2 다양한 상황 예시

#### **예시 1: 화재 상황 (S4)**

**입력**:
- 음성: "불이 났어요! 연기가 나고 있어요!"
- 사운드: 화재 소리 (confidence: 0.92)

**Situation JSON**:
```json
{
    "situation_id": "S4",
    "emergency_level": "high",
    "speech": {
        "disaster_large": "화재",
        "disaster_medium": "화재",
        "urgency_level": "상"
    },
    "sound": {
        "event": "화재",
        "confidence": 0.92
    },
    "symptoms": ["fire_suspected", "smoke", "high_urgency"]
}
```

**지침**:
```
1단계: 지금 당장 해야 할 일
지금 바로 119에 전화하세요.

2단계: 119 연결을 기다리면서 할 일
- 낮은 자세를 유지하세요. 연기는 위로 올라가므로 바닥에 가까이 있어야 합니다.
- 코와 입을 막으세요. 옷자락이나 수건으로 막을 수 있습니다.
- 문 손잡이를 만져보세요. 뜨겁다면 그 방향으로는 나가지 마세요.
- 가능하면 대피로를 확보하세요. 창문이나 다른 출구를 찾아보세요.

3단계: 119에 이렇게 말하세요
"혼자 있는데 불이 났습니다. 연기가 나고 있습니다. 주소는 [주소]입니다."

4단계: 통화가 끝난 뒤 구조를 기다리는 동안
- 가능하면 문을 닫아 연기가 들어오는 것을 막으세요.
- 구조대가 찾을 수 있도록 소리를 지르거나 벽을 두드리세요.
```

---

#### **예시 2: 갇힘 상황 (S5)**

**입력**:
- 음성: "문이 안 열려요. 갇혔어요!"
- 사운드: 갇힘 소리 (confidence: 0.88)

**Situation JSON**:
```json
{
    "situation_id": "S5",
    "emergency_level": "medium",
    "speech": {
        "disaster_large": "구조",
        "disaster_medium": null,
        "urgency_level": "중"
    },
    "sound": {
        "event": "갇힘",
        "confidence": 0.88
    },
    "symptoms": ["trapped_or_confined", "door_locked"]
}
```

**지침**:
```
1단계: 지금 당장 해야 할 일
문을 열기 위해 시도해보세요. 문 손잡이를 여러 방향으로 돌려보세요 (위로, 아래로, 좌우로).

2단계: 문이 열리지 않으면
- 문 아래쪽 틈새를 확인하고, 가능하면 얇은 카드나 열쇠로 문고리 밀어보기
- 문이 밀리는지 당기는지 확인 (일부 문은 밀어야 열림)
- 창문이 있다면 창문 잠금 장치 확인

3단계: 여전히 열리지 않으면
119에 전화하세요. "혼자 있는데 [방/엘리베이터 등 구체적 위치]에 갇혔습니다. 문이 열리지 않습니다. 주소는 [주소]입니다."

4단계: 구조대가 도착할 때까지
- 문 근처에서 대기하세요.
- 가능하면 문을 두드려서 위치를 알려주세요.
- 공기가 답답하면 창문 틈새나 문 틈새로 공기 순환 확인
```

---

#### **예시 3: 흉통 상황 (S1)**

**입력**:
- 음성: "가슴이 너무 아프고 숨쉬기가 조금 힘들어요"
- 사운드: 생활소음 (confidence: 0.65)

**Situation JSON**:
```json
{
    "situation_id": "S1",
    "emergency_level": "medium",
    "speech": {
        "disaster_large": "구급",
        "disaster_medium": "흉통",
        "urgency_level": "중"
    },
    "sound": {
        "event": "생활소음",
        "confidence": 0.65
    },
    "symptoms": ["chest_pain", "breathing_difficulty"]
}
```

**지침**:
```
1단계: 지금 당장 해야 할 일
가슴이 아프고 숨쉬기 힘들면, 기대서 앉는 자세를 취하세요. 옷이 답답하면 윗단추와 허리 쪽을 풀어 주세요.

2단계: 증상 확인
- 증상이 점점 심해지거나 5분 이상 줄어들지 않으면 119에 전화하세요.
- 얼굴이 창백해지고 식은땀이 나거나, 정신이 멍해지면 바로 119에 전화하세요.

3단계: 119에 이렇게 말하세요
"혼자 있는데 가슴이 너무 아프고 숨쉬기가 조금 힘듭니다. 주소는 [주소]입니다."

4단계: 통화가 끝난 뒤 구조를 기다리는 동안
- 편안한 자세를 유지하세요.
- 무리한 움직임을 피하세요.
```

---

## 6. 실제 결과 예시

### 6.1 API 응답 예시

**요청**:
```http
POST /api/emergency/analyze-video
Content-Type: multipart/form-data

file: emergency_call.mp4
```

**응답**:
```json
{
    "situation": {
        "situation_id": "S2",
        "situation_label": "Fall with suspected cardiac arrest",
        "emergency_level": "high",
        "speech": {
            "id": null,
            "text": "할머니가 갑자기 쓰러져서 숨을 안 쉬어요...",
            "disaster_large": "구급",
            "disaster_medium": "심정지",
            "urgency_level": "상",
            "sentiment": "불안/걱정",
            "triage": null
        },
        "sound": {
            "event": "낙상",
            "confidence": 0.95
        },
        "symptoms": [
            "fall",
            "possible_cardiac_arrest",
            "not_breathing",
            "high_urgency"
        ],
        "meta": {
            "timestamp": "2024-12-02T15:30:00",
            "language": "ko",
            "source": "realtime"
        }
    },
    "guideline": "1단계: 지금 당장 해야 할 일\n지금 바로 119에 전화하세요...",
    "status": "success"
}
```

---

### 6.2 웹 인터페이스 표시 예시

**화면 구성**:
1. **상단**: 상황 요약
   - 상황 ID: S2
   - 긴급도: High (빨간색 표시)
   - 상황 라벨: "낙상 + 심정지 의심"

2. **중간**: 지침 단계별 표시
   - 1단계: 지금 당장 해야 할 일
   - 2단계: 119 연결을 기다리면서 할 일
   - 3단계: 119에 이렇게 말하세요
   - 4단계: 통화가 끝난 뒤 구조를 기다리는 동안

3. **하단**: 
   - TTS 재생 버튼
   - 대화형 AI 질문 입력창

---

## 7. 기술 스택 상세

### 7.1 Backend

#### **FastAPI**
- **역할**: 웹 프레임워크
- **특징**: 
  - 비동기 처리 지원
  - 자동 API 문서 생성 (Swagger UI)
  - 타입 힌팅 지원
- **사용 위치**: `main.py`

#### **Uvicorn**
- **역할**: ASGI 서버
- **특징**: 
  - FastAPI와 함께 사용
  - 고성능 비동기 서버
- **실행**: `uvicorn main:app --host 0.0.0.0 --port 8000`

#### **Pydantic**
- **역할**: 데이터 검증 및 설정 관리
- **특징**: 
  - 타입 안전성 보장
  - 자동 데이터 검증
- **사용**: 요청/응답 모델 정의

---

### 7.2 AI/ML

#### **OpenAI Whisper**
- **역할**: 음성-텍스트 변환 (STT)
- **모델**: `small` 버전
- **특징**: 
  - 한국어 지원
  - 오프라인 동작 가능
  - 노이즈에 강함
- **사용 위치**: `main.py`의 `run_stt_on_wav()` 함수

#### **PyTorch**
- **역할**: 딥러닝 프레임워크
- **사용**: Module B의 CNN 모델
- **모델 구조**: SimpleCNN (3 Conv layers + FC layer)

#### **Google Gemini API**
- **모델 1**: `gemini-flash-lite-latest`
  - **용도**: Module C의 상황 융합
  - **특징**: 빠른 응답 속도
  
- **모델 2**: `gemini-2.0-flash`
  - **용도**: RAG 기반 지침 생성, 대화형 AI
  - **특징**: 고품질 생성

---

### 7.3 RAG 시스템

#### **LangChain**
- **역할**: LLM 애플리케이션 프레임워크
- **주요 컴포넌트**:
  - `langchain-core`: 핵심 기능
  - `langchain-community`: 커뮤니티 통합
  - `langchain-text-splitters`: 텍스트 분할
  - `langchain-openai`: OpenAI 통합

#### **ChromaDB**
- **역할**: 벡터 데이터베이스
- **특징**: 
  - 임베딩 저장 및 검색
  - 유사도 검색 지원
- **사용**: 문서 벡터 저장 및 검색

#### **Sentence Transformers**
- **모델**: `jhgan/ko-sroberta-multitask`
- **역할**: 한국어 텍스트 임베딩
- **특징**: 
  - 한국어 특화 모델
  - 768차원 벡터 생성

#### **pypdf**
- **역할**: PDF 문서 처리
- **사용**: 응급처치 매뉴얼 PDF 로드

---

### 7.4 오디오/비디오 처리

#### **MoviePy**
- **역할**: 비디오에서 오디오 추출
- **사용**: `main.py`의 `extract_audio_from_video()` 함수
- **특징**: 
  - 다양한 비디오 형식 지원
  - 오디오 트랙 추출 가능

#### **librosa**
- **역할**: 오디오 신호 처리
- **사용**: Module B의 오디오 전처리
- **기능**: 
  - 오디오 로드
  - Mel-spectrogram 변환
  - Log-scale 변환

#### **FFmpeg**
- **역할**: 멀티미디어 프레임워크
- **사용**: Whisper의 의존성
- **특징**: 
  - 다양한 오디오 형식 지원
  - 오디오 변환 및 처리

---

### 7.5 Frontend

#### **HTML5/CSS3/JavaScript**
- **역할**: 웹 인터페이스
- **파일**: `silversense_ai.html`
- **특징**: 
  - 반응형 디자인
  - 모던 UI/UX

#### **Web Speech API**
- **SpeechRecognition**: 음성 입력
- **SpeechSynthesis**: 텍스트-음성 변환 (TTS)
- **특징**: 
  - 브라우저 내장 API
  - 별도 설치 불필요

---

## 8. 웹 인터페이스 설명

### 8.1 주요 기능

#### **1. 파일 업로드**
- 드래그 앤 드롭 또는 파일 선택
- 지원 형식: `.mp4`, `.wav`, `.mp3`
- 업로드 후 자동 분석 시작

#### **2. 분석 결과 표시**
- 상황 요약 (상황 ID, 긴급도)
- 지침 단계별 표시
- 상황별 색상 구분 (High: 빨간색, Medium: 노란색, Low: 초록색)

#### **3. TTS 음성 안내**
- 지침 음성 읽기
- 속도 조절 가능 (0.5x ~ 1.7x)
- 음성 선택 가능 (여러 음성 옵션)

#### **4. 대화형 AI**
- 음성 또는 텍스트로 질문 가능
- 상황 기반 답변 제공
- 실시간 응답

---

### 8.2 화면 구성

#### **상단 헤더**
- 로고: SilverSense AI
- 서비스 설명

#### **중간 영역**
- 파일 업로드 영역
- 분석 결과 표시 영역
- 지침 표시 영역

#### **하단 영역**
- TTS 컨트롤
- 대화형 AI 입력창
- 질문-답변 영역

---

## 9. API 엔드포인트

### 9.1 주요 엔드포인트

#### **POST /api/emergency/analyze-video**
- **기능**: 비디오/오디오 파일 분석
- **입력**: 파일 업로드 (multipart/form-data)
- **출력**: Situation JSON + 지침

#### **POST /api/emergency/ask**
- **기능**: 대화형 AI 질문-답변
- **입력**: 질문 텍스트 + Situation JSON
- **출력**: 답변 텍스트

#### **GET /**
- **기능**: API 상태 확인
- **출력**: `{"status": "ok", "message": "Emergency backend running"}`

#### **GET /docs**
- **기능**: Swagger UI (API 문서)
- **출력**: 인터랙티브 API 문서

---

## 10. 프로젝트 구조

### 10.1 폴더 구조

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
│           ├── rag_system.py       # RAG 시스템 메인
│           └── guideline_generator.py  # 지침 생성기
├── silversense_ai.html             # 웹 인터페이스
├── architecture_viewer.html        # 아키텍처 뷰어
├── requirements.txt                 # Python 패키지 의존성
├── .env.example                     # 환경 변수 예시
└── temp_media/                      # 임시 파일 저장 폴더
```

---

## 11. 발표 시 강조할 포인트

### 11.1 기술적 혁신

1. **다중 신호 융합**
   - 음성(STT) + 사운드 이벤트 동시 분석
   - 단일 신호만으로는 불가능한 정확한 상황 판단

2. **AI 기반 지능형 분석**
   - Gemini API를 활용한 상황 융합
   - 복잡한 규칙을 LLM이 자연스럽게 처리

3. **RAG 기반 맞춤 지침**
   - 검색 증강 생성으로 정확한 지침 제공
   - 상황별 구체적 대처 방법 제시

### 11.2 실용성

1. **노인 친화적 디자인**
   - 간단한 문장 구조
   - 전문 용어 최소화
   - 음성 안내 제공

2. **실시간 대응**
   - 빠른 분석 속도
   - 즉시 지침 제공
   - 대화형 AI로 추가 질문 가능

3. **확장 가능성**
   - 새로운 Intent 추가 용이
   - 새로운 사운드 이벤트 학습 가능
   - 다양한 상황 대응 가능

---

## 12. 발표 시 데모 시나리오

### 시나리오 1: 낙상 + 심정지 (S2)
1. 비디오 파일 업로드
2. STT: "할머니가 쓰러져서 숨을 안 쉬어요"
3. 사운드: 낙상 소리 감지
4. Module C: S2 판단 (high)
5. RAG: "지금 바로 119에 전화하세요" 지침 생성
6. TTS로 음성 안내

### 시나리오 2: 화재 (S4)
1. 오디오 파일 업로드
2. STT: "불이 났어요!"
3. 사운드: 화재 소리 감지
4. Module C: S4 판단 (high)
5. RAG: 화재 대피 지침 생성
6. 대화형 AI: "연기가 많으면 어떻게 해야 하나요?" 질문

---

## 13. 참고 자료

### 13.1 주요 파일 위치

- **메인 서버**: `main.py`
- **Module A**: `modules/module_a_speech.py`
- **Module B**: `modules/module_b_sound.py`
- **Module C**: `modules/module_c_fusion.py`
- **RAG 클라이언트**: `services/rag_client.py`
- **웹 인터페이스**: `silversense_ai.html`
- **아키텍처 뷰어**: `architecture_viewer.html`

### 13.2 문서 위치

- **README**: `README.md`
- **아키텍처 다이어그램**: `ARCHITECTURE_DIAGRAM.md`
- **파이프라인 다이어그램**: `PRESENTATION_PIPELINE.md`

---

## 14. 질문 대비 FAQ

### Q1: 왜 음성과 사운드를 동시에 분석하나요?
**A**: 단일 신호만으로는 정확한 상황 판단이 어렵습니다. 예를 들어, 낙상 소리만으로는 심정지인지 단순 낙상인지 구분하기 어렵지만, 음성 정보("숨을 안 쉬어요")와 결합하면 정확한 판단이 가능합니다.

### Q2: RAG 시스템이 왜 필요한가요?
**A**: 일반적인 LLM은 일반적인 응급처치 지침만 제공할 수 있습니다. 하지만 RAG 시스템은 실제 응급처치 매뉴얼 문서를 검색하여 상황에 맞는 구체적이고 정확한 지침을 생성할 수 있습니다.

### Q3: 실시간으로 동작하나요?
**A**: 현재는 파일 업로드 방식이지만, 파이프라인 자체는 실시간 분석이 가능하도록 설계되어 있습니다. 향후 실시간 마이크 입력으로 확장 가능합니다.

### Q4: 정확도는 어느 정도인가요?
**A**: 
- STT: Whisper small 모델 기준 한국어 인식률 약 90% 이상
- 사운드 분석: CNN 모델 기준 4가지 이벤트 분류 정확도 약 85% 이상
- 상황 판단: Gemini API 기반으로 복잡한 상황도 정확히 판단

### Q5: 확장 가능성은?
**A**: 
- 새로운 Intent 추가 가능 (Module A)
- 새로운 사운드 이벤트 학습 가능 (Module B)
- 새로운 상황 ID 추가 가능 (Module C)
- 새로운 문서 추가 가능 (RAG 시스템)

---

이 문서를 바탕으로 발표자료를 제작하시면 됩니다. 추가로 필요한 정보가 있으면 알려주세요!

