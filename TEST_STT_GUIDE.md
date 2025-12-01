# STT 기능 테스트 가이드

STT(Speech-to-Text) 기능이 제대로 작동하는지 확인하는 방법입니다.

## 방법 1: 테스트 스크립트 사용 (추천)

### 1-1. 기본 테스트 스크립트

```cmd
python test_stt.py <오디오파일경로>
```

**예시:**
```cmd
# temp_media 폴더의 파일 테스트
python test_stt.py temp_media\abc123.wav

# 직접 오디오 파일 테스트
python test_stt.py test_audio.wav
```

**출력 예시:**
```
============================================================
STT 테스트 시작
============================================================
📁 테스트 파일: temp_media/abc123.wav
📊 파일 크기: 123456 bytes

🔄 STT 실행 중...
✅ STT 시작: temp_media/abc123.wav (파일 크기: 123456 bytes)
🔄 Whisper 모델 로드 중...
✅ Whisper 모델 로드 완료
🔄 음성 인식 중...
✅ STT 완료: 할머니가 갑자기 쓰러져서...

============================================================
✅ STT 결과
============================================================
인식된 텍스트: 할머니가 갑자기 쓰러져서 숨을 안 쉬어요

✅ STT가 정상적으로 작동합니다!
```

### 1-2. 간단한 테스트 스크립트

```cmd
python test_stt_simple.py <오디오파일경로>
```

이 스크립트는 Whisper를 직접 사용하여 테스트합니다.

---

## 방법 2: 웹 인터페이스에서 테스트

1. **서버 실행**
   ```cmd
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **브라우저에서 접속**
   ```
   http://localhost:8000/app
   ```

3. **오디오/영상 파일 업로드**
   - 파일 선택 버튼 클릭
   - 오디오 파일(wav, mp3) 또는 영상 파일(mp4) 업로드
   - "상황 분석하기" 버튼 클릭

4. **터미널 로그 확인**
   서버 터미널에서 다음 로그를 확인하세요:
   ```
   ✅ STT 시작: temp_media/xxxxx.wav (파일 크기: xxxx bytes)
   🔄 Whisper 모델 로드 중...
   ✅ Whisper 모델 로드 완료
   🔄 음성 인식 중...
   ✅ STT 완료: [인식된 텍스트]...
   ```

5. **결과 확인**
   - 웹 페이지에 표시된 "인식된 텍스트" 확인
   - A 모듈 분석 결과 확인

---

## 방법 3: API 직접 호출 테스트

### 3-1. curl 사용 (Windows)

```cmd
curl -X POST "http://localhost:8000/api/emergency/analyze-video" ^
  -H "Content-Type: multipart/form-data" ^
  -F "file=@test_audio.wav"
```

### 3-2. Python requests 사용

```python
import requests

url = "http://localhost:8000/api/emergency/analyze-video"
files = {"file": open("test_audio.wav", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

---

## 방법 4: Whisper 설치 확인

### 4-1. 설치 여부 확인

```cmd
pip list | findstr whisper
```

**예상 출력:**
```
openai-whisper    20231117
```

### 4-2. 설치되지 않은 경우

```cmd
pip install openai-whisper
```

### 4-3. 모델 다운로드 확인

Whisper 모델은 첫 실행 시 자동으로 다운로드됩니다.
- `tiny`: 가장 작고 빠름 (약 39MB)
- `base`: 작음 (약 74MB)
- `small`: 중간 (약 244MB) ← 현재 사용 중
- `medium`: 큼 (약 769MB)
- `large`: 가장 큼 (약 1550MB)

모델은 다음 위치에 저장됩니다:
- Windows: `C:\Users\<사용자명>\.cache\whisper\`
- Linux/Mac: `~/.cache/whisper/`

---

## 문제 해결

### 문제 1: "지정된 파일을 찾을 수 없습니다" 오류

**원인:**
- 오디오 파일 경로가 잘못됨
- 임시 파일이 제대로 생성되지 않음

**해결:**
1. 파일 경로 확인:
   ```cmd
   dir temp_media
   ```
2. 파일이 존재하는지 확인:
   ```cmd
   python test_stt.py temp_media\실제파일명.wav
   ```

### 문제 2: "whisper가 설치되지 않았습니다" 오류

**해결:**
```cmd
pip install openai-whisper
```

### 문제 3: 모델 로드가 느림

**원인:**
- 첫 실행 시 모델 다운로드
- 큰 모델 사용 (small, medium, large)

**해결:**
- `main.py`의 `run_stt_on_wav()` 함수에서 모델 크기 변경:
  ```python
  model = whisper.load_model("tiny")  # 또는 "base"
  ```

### 문제 4: 인식 결과가 비어있음

**원인:**
- 오디오 파일에 음성이 없음
- 오디오 형식이 지원되지 않음
- 음성이 너무 작거나 노이즈가 많음

**해결:**
1. 오디오 파일 재생해서 음성 확인
2. 다른 오디오 파일로 테스트
3. 오디오 파일 형식 확인 (wav, mp3 권장)

---

## 테스트 오디오 파일 준비

### 방법 1: 직접 녹음
- Windows: 음성 녹음기 사용
- 스마트폰: 음성 메모 앱 사용

### 방법 2: 샘플 오디오 다운로드
- 한국어 음성이 포함된 샘플 오디오 사용

### 방법 3: 기존 파일 사용
- `temp_media` 폴더에 있는 업로드된 파일 사용

---

## 성공 기준

✅ **STT가 정상 작동하는 경우:**
- 터미널에 "✅ STT 완료: [텍스트]..." 메시지 출력
- 인식된 텍스트가 비어있지 않음
- A 모듈이 텍스트를 분석하여 결과 반환

❌ **STT가 작동하지 않는 경우:**
- "⚠️ STT 오류 발생" 메시지 출력
- 인식된 텍스트가 "음성을 인식할 수 없습니다."
- A 모듈이 기본값만 반환

---

## 빠른 체크리스트

- [ ] Whisper 설치 확인: `pip list | findstr whisper`
- [ ] 테스트 스크립트 실행: `python test_stt.py <파일경로>`
- [ ] 웹 인터페이스에서 파일 업로드 테스트
- [ ] 터미널 로그 확인
- [ ] 인식된 텍스트 확인

---

## 추가 도움말

문제가 계속되면:
1. 터미널의 전체 오류 메시지 확인
2. `test_stt.py` 실행 결과 확인
3. 오디오 파일 형식 및 크기 확인

