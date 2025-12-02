# 🌐 SilverSense AI 웹페이지 기능 상세 정리

실제 웹페이지(`silversense_ai.html`)에서 구현된 모든 기능들을 정리한 문서입니다.

---

## 📋 목차

1. [UI/UX 구성](#1-uiux-구성)
2. [파일 업로드 기능](#2-파일-업로드-기능)
3. [분석 결과 표시](#3-분석-결과-표시)
4. [TTS (Text-to-Speech) 기능](#4-tts-text-to-speech-기능)
5. [대화형 AI 기능](#5-대화형-ai-기능)
6. [반응형 디자인](#6-반응형-디자인)
7. [추가 UI 요소](#7-추가-ui-요소)

---

## 1. UI/UX 구성

### 1.1 상단 헤더 (Top Bar)

**구성 요소**:
- **로고**: 
  - 하트 아이콘 (SVG, 그라데이션: 핑크→보라)
  - 심전도 라인 포함
  - "SilverSense AI" 텍스트
  - "AI" 텍스트는 핑크→보라 그라데이션

**특징**:
- Sticky 헤더 (스크롤 시 상단 고정)
- 깔끔한 디자인
- 브랜드 아이덴티티 강조

---

### 1.2 히어로 섹션 (Hero Section)

**구성 요소**:
- **타이틀**: 
  - "혼자 계실 때도 **안심하세요.**"
  - "AI가 **위험 신호를 감지해** 바로 안내합니다."
  - 하이라이트: "안심하세요", "위험 신호를 감지해" (보라색 강조)

- **서브타이틀**: 
  - 서비스 목적 설명
  - 프로토타입 작동 방식 안내

**디자인**:
- 그라데이션 배경 (핑크→보라)
- 중앙 정렬
- 반응형 폰트 크기

---

### 1.3 메인 카드 (Main Card)

**구성 요소**:
- **업로드 영역**:
  - 파일 선택 버튼
  - 드래그 앤 드롭 영역
  - 파일 정보 표시 (파일명, 크기)
  - 분석 시작 버튼

- **로딩 상태**:
  - 로딩 애니메이션
  - "분석 중..." 메시지

- **결과 표시 영역**:
  - 상황 요약
  - 긴급도 표시
  - 지침 단계별 표시

---

## 2. 파일 업로드 기능

### 2.1 파일 선택

**기능**:
- 파일 선택 버튼 클릭
- 파일 탐색기에서 파일 선택
- 지원 형식: `.mp4`, `.wav`, `.mp3` 등

**구현**:
```javascript
fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) {
    statusText.textContent = `선택된 파일: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    analyzeBtn.disabled = false;
  }
});
```

---

### 2.2 드래그 앤 드롭

**기능**:
- 파일을 업로드 영역에 드래그 앤 드롭
- 드래그 중 시각적 피드백 (배경색 변경)
- 드롭 시 자동으로 파일 선택

**구현**:
```javascript
uploadArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadArea.style.background = '#f0f0f0';
});

uploadArea.addEventListener('drop', (e) => {
  e.preventDefault();
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    fileInput.files = files;
    fileInput.dispatchEvent(new Event('change'));
  }
});
```

**특징**:
- 직관적인 사용자 경험
- 파일 탐색기 없이도 업로드 가능

---

### 2.3 파일 분석

**기능**:
- 선택된 파일을 FastAPI 서버로 전송
- FormData를 사용한 multipart/form-data 전송
- 분석 진행 상태 표시

**구현**:
```javascript
async function analyzeFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/emergency/analyze-video`, {
    method: 'POST',
    body: formData
  });

  const data = await response.json();
  displayResult(data);
}
```

**특징**:
- 비동기 처리 (async/await)
- 에러 처리 포함
- 로딩 상태 표시

---

## 3. 분석 결과 표시

### 3.1 상황 요약 표시

**표시 내용**:
- **긴급도**: 
  - High: 빨간색 배지
  - Medium: 노란색 배지
  - Low: 초록색 배지

- **증상 목록**:
  - `symptoms` 배열의 각 항목을 리스트로 표시
  - 예: "fall", "possible_cardiac_arrest", "not_breathing"

**구현**:
```javascript
const emergencyLevel = document.getElementById('emergencyLevel');
emergencyLevel.textContent = `긴급도: ${level === 'high' ? '높음' : level === 'medium' ? '보통' : '낮음'}`;
emergencyLevel.className = 'emergency-badge ' + level;
```

---

### 3.2 지침 단계별 표시

**3단계 구조**:
1. **1단계: 지금 당장 해야 할 일**
   - 가장 우선순위가 높은 행동
   - 예: "지금 바로 119에 전화하세요"

2. **2단계: 119 연결을 기다리면서 할 일**
   - 대기 중 할 수 있는 응급처치
   - 예: "낮은 자세 유지", "코와 입 막기"

3. **3단계: 119에 이렇게 말하세요**
   - 신고 멘트 템플릿
   - 예: "혼자 있는데 할머니가 쓰러져서..."

**지침 파싱 로직**:
```javascript
function parseGuideline(guideline) {
  const lines = guideline.split('\n');
  let currentStep = null;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // 단계 감지
    if (line.includes('1단계:')) {
      currentStep = 'now';
    } else if (line.includes('2단계:')) {
      currentStep = 'wait';
    } else if (line.includes('3단계:')) {
      currentStep = 'call';
    }
    
    // 리스트 항목 추가
    if (line.startsWith('- ') || line.startsWith('• ')) {
      const li = document.createElement('li');
      li.textContent = line.replace(/^[-•*]\s+/, '').trim();
      currentList.appendChild(li);
    }
  }
}
```

**특징**:
- 자동 파싱으로 지침 텍스트를 단계별로 분리
- 시각적으로 명확한 단계 구분
- 각 단계별 아이콘과 색상 구분

---

### 3.3 상황별 색상 구분

**긴급도별 색상**:
- **High**: 빨간색 (`#ef4444`)
- **Medium**: 노란색 (`#f59e0b`)
- **Low**: 초록색 (`#10b981`)

**시각적 피드백**:
- 배지 색상으로 긴급도 즉시 파악 가능
- 사용자가 우선순위를 쉽게 이해

---

## 4. TTS (Text-to-Speech) 기능

### 4.1 기본 TTS 재생

**기능**:
- 지침 텍스트를 음성으로 읽어주기
- Web Speech API 사용
- 재생/정지 제어

**구현**:
```javascript
function playTTS() {
  const guidelineText = document.getElementById('guidelineText').textContent;
  const fullText = guidelineText.replace(/119/g, '일일구'); // "119" → "일일구" 변환
  
  startTTSPlayback(fullText);
}

function startTTSPlayback(fullText) {
  const utterance = new SpeechSynthesisUtterance(fullText);
  utterance.lang = 'ko-KR';
  utterance.rate = currentTTSRate;
  utterance.voice = currentTTSVoice;
  
  speechSynthesis.speak(utterance);
}
```

**특징**:
- 한국어 음성 지원
- "119"를 "일일구"로 자동 변환 (올바른 발음)
- 브라우저 내장 API 사용 (별도 설치 불필요)

---

### 4.2 음성 선택

**기능**:
- 여러 음성 옵션 중 선택 가능
- 브라우저에서 지원하는 음성 목록 표시
- 실시간 음성 변경

**구현**:
```javascript
function loadVoices() {
  const voices = speechSynthesis.getVoices();
  const voiceSelect = document.getElementById('ttsVoiceSelect');
  
  voices.forEach((voice, index) => {
    const option = document.createElement('option');
    option.value = index;
    option.textContent = `${voice.name} (${voice.lang})`;
    voiceSelect.appendChild(option);
  });
}
```

**특징**:
- 사용자 선호 음성 선택 가능
- 다양한 음성 옵션 제공

---

### 4.3 속도 조절

**기능**:
- 읽기 속도 조절 (0.5x ~ 1.7x)
- 5단계 속도 옵션:
  - 매우 느림 (0.5x)
  - 느림 (0.7x)
  - 보통 (1.0x)
  - 빠름 (1.3x)
  - 매우 빠름 (1.7x)

**구현**:
```javascript
const speedSelect = document.getElementById('ttsSpeedSelect');
speedSelect.addEventListener('change', (e) => {
  currentTTSRate = parseFloat(e.target.value);
});
```

**특징**:
- 노인 사용자를 위한 느린 속도 옵션
- 개인 선호도에 맞춘 속도 조절

---

### 4.4 TTS 제어

**기능**:
- 재생 버튼: 지침 읽기 시작
- 정지 버튼: 읽기 중단
- 재생 중 상태 표시

**구현**:
```javascript
function stopTTS() {
  speechSynthesis.cancel();
  setTimeout(() => {
    // 재생 상태 초기화
  }, 100);
}
```

**특징**:
- 언제든지 중단 가능
- 재생 상태 시각적 표시

---

## 5. 대화형 AI 기능

### 5.1 텍스트 질문

**기능**:
- 텍스트 입력창에 질문 입력
- "질문하기" 버튼 클릭
- 상황 기반 답변 제공

**구현**:
```javascript
function submitTextQuestion() {
  const questionInput = document.getElementById('textQuestionInput');
  const questionText = questionInput.value.trim();
  
  if (questionText) {
    handleQuestion(questionText);
    questionInput.value = '';
  }
}

async function handleQuestion(questionText) {
  const response = await fetch(`${API_BASE_URL}/api/emergency/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question: questionText,
      situation: currentSituation
    })
  });
  
  const data = await response.json();
  displayAnswer(data.answer);
}
```

**특징**:
- 간단한 텍스트 입력으로 질문 가능
- 상황 정보를 함께 전송하여 정확한 답변

---

### 5.2 음성 질문

**기능**:
- 마이크 버튼 클릭
- 음성으로 질문
- 자동으로 텍스트 변환 후 질문 전송

**구현**:
```javascript
function startVoiceQuestion() {
  if (!recognition) {
    alert('음성 인식이 지원되지 않습니다.');
    return;
  }
  
  recognition.start();
  voiceQuestionBtn.textContent = '🎤 듣는 중...';
  voiceQuestionBtn.disabled = true;
}

recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  handleQuestion(transcript);
};
```

**특징**:
- Web Speech API의 SpeechRecognition 사용
- 음성으로 직접 질문 가능
- 실시간 음성 인식

---

### 5.3 답변 표시

**기능**:
- 답변 텍스트 표시
- "답변 듣기" 버튼 (TTS로 답변 읽기)
- 닫기 버튼

**구현**:
```javascript
function displayAnswer(answer) {
  const answerDiv = document.getElementById('questionAnswer');
  answerDiv.innerHTML = `
    <div class="answer-text">${answer}</div>
    <button onclick="speakAnswer('${answer}')">🔊 답변 듣기</button>
    <button onclick="document.getElementById('questionAnswer').classList.add('hidden')">닫기</button>
  `;
  answerDiv.classList.remove('hidden');
}
```

**특징**:
- 상황에 맞는 맞춤 답변
- 답변도 TTS로 들을 수 있음
- 깔끔한 UI로 표시

---

## 6. 반응형 디자인

### 6.1 모바일 대응

**기능**:
- 모바일 화면 크기에 맞춘 레이아웃
- 터치 친화적 버튼 크기
- 가로 스크롤 방지

**구현**:
```css
@media (max-width: 768px) {
  .hero-title {
    font-size: 24px;
  }
  
  .steps-grid {
    grid-template-columns: 1fr;
  }
  
  .examples-grid {
    grid-template-columns: 1fr;
  }
}
```

**특징**:
- 모든 화면 크기에서 사용 가능
- 모바일에서도 편리한 사용 경험

---

### 6.2 그리드 레이아웃

**기능**:
- 데스크톱: 2x2 그리드
- 모바일: 1열 레이아웃
- 자동 반응형 조정

**구현**:
```css
.examples-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

@media (max-width: 768px) {
  .examples-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## 7. 추가 UI 요소

### 7.1 예시 섹션

**기능**:
- 6가지 상황 예시 표시:
  1. 낙상 + 심정지 (S2, High)
  2. 화재 (S4, High)
  3. 호흡곤란 (S6, High)
  4. 낙상 + 부상 (S3, Medium)
  5. 흉통 (S1, Medium)
  6. 갇힘 (S5, Medium)

**각 예시 카드 구성**:
- 상황 제목
- 긴급도 배지
- 입력 예시 (음성, 소리)
- 분석 결과 (상황 ID, 증상)
- 제공되는 지침 요약

**디자인**:
- 왼쪽 그라데이션 보더 (핑크→보라)
- 긴급도별 색상 구분
- 카드 형태로 깔끔한 정리

---

### 7.2 서비스 소개 섹션

**기능**:
- 서비스 목적 설명
- 동작 원리 안내
- 프로토타입 작동 방식 설명

**구성**:
- 3개의 정보 카드:
  1. 실시간 위험 감지
  2. 즉시 대처 안내
  3. 프로토타입 작동 방식

---

### 7.3 중요 안내 섹션

**기능**:
- 서비스의 한계 명시
- 응급 상황 시 119 신고 강조
- 보조 도구임을 명확히 안내

**내용**:
- "SilverSense AI는 응급 상황을 더 잘 이해하는 데 도움을 주는 **보조 도구**입니다."
- "실제 생명 위협이 느껴질 경우, 안내 내용과 상관없이 **항상 119에 바로 신고**해 주세요."

---

### 7.4 리셋 기능

**기능**:
- "다시 분석하기" 버튼
- 분석 결과 초기화
- 새로운 파일 업로드 가능

**구현**:
```javascript
function resetAnalysis() {
  resultSection.classList.add('hidden');
  fileInput.value = '';
  analyzeBtn.disabled = true;
  statusText.textContent = '';
  currentSituation = null;
}
```

**특징**:
- 언제든지 새로 시작 가능
- 깔끔한 상태 초기화

---

### 7.5 로딩 상태 표시

**기능**:
- 분석 중 로딩 애니메이션
- "분석 중..." 메시지
- 버튼 비활성화

**구현**:
```javascript
loadingBox.classList.remove('hidden');
mainCard.style.opacity = '0.6';
mainCard.style.pointerEvents = 'none';
analyzeBtn.disabled = true;
```

**특징**:
- 명확한 진행 상태 표시
- 중복 요청 방지

---

### 7.6 에러 처리

**기능**:
- API 오류 시 에러 메시지 표시
- 사용자 친화적 에러 메시지
- 상태 복구

**구현**:
```javascript
catch (err) {
  statusText.textContent = '오류 발생: ' + err.message;
  statusText.style.color = '#c33';
  loadingBox.classList.add('hidden');
  mainCard.style.opacity = '1';
  mainCard.style.pointerEvents = 'auto';
  analyzeBtn.disabled = false;
}
```

**특징**:
- 명확한 에러 메시지
- 자동 상태 복구

---

## 8. API 연동

### 8.1 동적 API URL

**기능**:
- URL 파라미터로 API 서버 주소 지정
- 기본값: 현재 도메인

**구현**:
```javascript
const urlParams = new URLSearchParams(window.location.search);
const API_BASE_URL = urlParams.get('api') || window.location.origin;
```

**사용 예시**:
```
silversense_ai.html?api=https://example.com
```

**특징**:
- 다양한 환경에서 사용 가능
- 개발/프로덕션 환경 분리 용이

---

### 8.2 API 엔드포인트

**사용하는 엔드포인트**:

1. **POST /api/emergency/analyze-video**
   - 파일 업로드 및 분석
   - 입력: 파일 (multipart/form-data)
   - 출력: `{ situation, guideline }`

2. **POST /api/emergency/ask**
   - 대화형 AI 질문-답변
   - 입력: `{ question, situation }`
   - 출력: `{ answer }`

---

## 9. 사용자 경험 (UX) 특징

### 9.1 직관적인 인터페이스

- **명확한 단계**: 업로드 → 분석 → 결과 → 질문
- **시각적 피드백**: 로딩, 성공, 에러 상태 명확히 표시
- **색상 구분**: 긴급도별 색상으로 즉시 파악

### 9.2 접근성

- **음성 안내**: TTS로 지침 읽어주기
- **큰 버튼**: 터치하기 쉬운 크기
- **명확한 텍스트**: 읽기 쉬운 폰트와 크기

### 9.3 사용 편의성

- **드래그 앤 드롭**: 파일 탐색기 없이도 업로드
- **자동 파싱**: 지침을 자동으로 단계별로 분리
- **음성/텍스트 질문**: 두 가지 방법 모두 지원

---

## 10. 기술 스택

### Frontend 기술

- **HTML5**: 시맨틱 마크업
- **CSS3**: 
  - Flexbox, Grid 레이아웃
  - 그라데이션, 애니메이션
  - 반응형 미디어 쿼리
- **JavaScript (ES6+)**:
  - async/await 비동기 처리
  - Fetch API
  - Web Speech API (TTS, STT)
  - DOM 조작

### 브라우저 API

- **Web Speech API**:
  - `SpeechSynthesis`: TTS
  - `SpeechRecognition`: STT
- **File API**: 파일 읽기
- **Drag and Drop API**: 드래그 앤 드롭

---

## 11. 주요 함수 목록

### 파일 처리
- `analyzeFile(file)`: 파일 분석 시작
- `displayResult(data)`: 결과 표시
- `parseGuideline(guideline)`: 지침 파싱

### TTS 관련
- `playTTS()`: TTS 재생 시작
- `startTTSPlayback(text)`: TTS 재생 실행
- `stopTTS()`: TTS 정지
- `loadVoices()`: 음성 목록 로드

### 질문-답변 관련
- `submitTextQuestion()`: 텍스트 질문 제출
- `startVoiceQuestion()`: 음성 질문 시작
- `stopVoiceRecording()`: 음성 녹음 정지
- `handleQuestion(questionText)`: 질문 처리
- `displayAnswer(answer)`: 답변 표시
- `speakAnswer(text)`: 답변 TTS 재생

### 유틸리티
- `resetAnalysis()`: 분석 결과 리셋
- `initSpeechRecognition()`: 음성 인식 초기화

---

## 12. 화면 구성 요약

### 상단
- 로고 (하트 아이콘 + SilverSense AI)
- 히어로 섹션 (타이틀 + 서브타이틀)

### 메인 영역
- 파일 업로드 카드
- 분석 결과 카드 (상황 요약 + 지침 3단계)
- TTS 컨트롤
- 질문-답변 섹션

### 하단
- 예시 섹션 (6가지 상황)
- 서비스 소개 섹션
- 중요 안내 섹션
- 푸터

---



