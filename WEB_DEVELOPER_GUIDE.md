# 🚑 Emergency Assistant API - 웹 개발자 가이드

## 📋 서비스 개요

Emergency Assistant는 응급 상황을 자동으로 분석하고, 혼자 있는 노인을 위한 맞춤형 응급 대처 지침을 제공하는 백엔드 API 서비스입니다.

### 주요 기능
- **음성/영상 파일 분석**: 업로드된 파일에서 음성을 추출하고 텍스트로 변환 (STT)
- **응급 상황 자동 분류**: 음성 분석 + 사운드 이벤트 감지를 통해 상황을 8가지 레벨(S0~S7)로 분류
- **맞춤형 지침 생성**: 상황별로 혼자 있는 노인이 스스로 할 수 있는 구체적인 응급 대처 방법 제공

### 서비스 흐름
```
파일 업로드 → STT → 음성 분석 → 사운드 분석 → 상황 융합 → 지침 생성 → 응답
```

---

## 🔌 API 엔드포인트

### 1. 텍스트 기반 분석 (간단한 테스트용)

**엔드포인트:** `POST /api/emergency/analyze`

**요청 형식:**
```json
{
  "stt_text": "할머니가 갑자기 쓰러져서 숨을 안 쉬어요",
  "sound_event": "낙상",
  "sound_confidence": 0.93
}
```

**응답 형식:**
```json
{
  "situation": {
    "situation_id": "S2",
    "situation_label": "Fall with suspected cardiac arrest",
    "emergency_level": "high",
    "speech": {
      "disaster_large": "구급",
      "disaster_medium": "심정지",
      "urgency_level": "상",
      "sentiment": "불안/걱정",
      "raw_text": "할머니가 갑자기 쓰러져서 숨을 안 쉬어요"
    },
    "sound": {
      "event": "낙상",
      "confidence": 0.93
    },
    "symptoms": ["fall", "possible_cardiac_arrest", "not_breathing"],
    "meta": {
      "timestamp": "2024-01-01T12:00:00",
      "language": "ko",
      "source": "realtime"
    }
  },
  "guideline": "지금은 쓰러진 상태에서 숨쉬기가 어려운 위험한 상황입니다.\n\n**1단계: 지금 당장 해야 할 일**\n- 지금 바로 119에 전화하세요. 전화를 걸 수 있으면 무조건 먼저 119를 누르세요.\n\n**2단계: 119 연결을 기다리면서 할 일**\n- 무리해서 일어나지 말고, 가능한 한 편안한 자세를 유지하세요.\n- 전화기가 손 닿는 거리에 없으면, 천천히 기어가서 가까운 전화기를 향해 움직이세요.\n\n**3단계: 119에 이렇게 말하세요**\n- \"혼자 있는데 쓰러져서 숨쉬기가 어렵습니다. 심정지 가능성이 있습니다. 주소는 [주소]입니다.\""
}
```

---

### 2. 파일 업로드 분석 (실제 사용)

**엔드포인트:** `POST /api/emergency/analyze-video`

**요청 형식:**
- **Content-Type:** `multipart/form-data`
- **파라미터:** `file` (파일 업로드)

**지원 파일 형식:**
- **영상:** `.mp4`, `.avi`, `.mov`, `.mkv` 등
- **오디오:** `.wav` (권장), `.mp3`, `.m4a`, `.flac`, `.ogg` 등

**응답 형식:**
```json
{
  "situation": {
    "situation_id": "S2",
    "situation_label": "Fall with suspected cardiac arrest",
    "emergency_level": "high",
    "speech": {...},
    "sound": {...},
    "symptoms": [...],
    "meta": {...}
  },
  "guideline": "지금은 쓰러진 상태에서 숨쉬기가 어려운 위험한 상황입니다.\n\n**1단계: 지금 당장 해야 할 일**\n..."
}
```

---

## 📊 상황 ID (situation_id) 설명

| ID | 설명 | 긴급도 | 예시 |
|----|------|--------|------|
| **S2** | 낙상 + 생명위협 (심정지/호흡곤란) | high | 쓰러져서 숨을 못 쉬는 경우 |
| **S3** | 낙상 + 부상/통증 | high/medium | 넘어져서 다리가 아픈 경우 |
| **S4** | 화재 | high | 불이 나고 연기가 나는 경우 |
| **S5** | 갇힘/고립 | medium/high | 문이 안 열리는 경우 |
| **S1** | 의료 응급 (비낙상/비화재) | medium | 가슴이 아픈 경우 |
| **S6** | 고위험 의료 응급 (낙상 없음) | high | 호흡곤란만 있는 경우 |
| **S7** | 기타 위험 상황 | medium/high | 기타 응급 상황 |
| **S0** | 정상/불명확 | low | 명확하지 않은 경우 |

---

## 💻 웹 통합 예시

### JavaScript (Fetch API)

```javascript
// 파일 업로드 분석
async function analyzeEmergency(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch('http://localhost:8000/api/emergency/analyze-video', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // 결과 처리
    console.log('상황 ID:', data.situation.situation_id);
    console.log('긴급도:', data.situation.emergency_level);
    console.log('지침:', data.guideline);
    
    return data;
  } catch (error) {
    console.error('오류 발생:', error);
    throw error;
  }
}

// 사용 예시
const fileInput = document.querySelector('#file-input');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (file) {
    const result = await analyzeEmergency(file);
    // UI에 결과 표시
    displayResult(result);
  }
});
```

### React 예시

```jsx
import React, { useState } from 'react';

function EmergencyAnalyzer() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/emergency/analyze-video', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('분석 실패');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="emergency-analyzer">
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept="video/*,audio/*"
          onChange={handleFileChange}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !file}>
          {loading ? '분석 중...' : '응급 상황 분석'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="result">
          <h3>상황 분석 결과</h3>
          <p>상황 ID: {result.situation.situation_id}</p>
          <p>긴급도: {result.situation.emergency_level}</p>
          
          <h3>응급 대처 지침</h3>
          <div className="guideline">
            {result.guideline.split('\n').map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default EmergencyAnalyzer;
```

### HTML + JavaScript (간단한 예시)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>응급 상황 분석</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 800px;
      margin: 50px auto;
      padding: 20px;
    }
    .upload-area {
      border: 2px dashed #ccc;
      padding: 40px;
      text-align: center;
      margin-bottom: 20px;
    }
    .result {
      margin-top: 30px;
      padding: 20px;
      background: #f5f5f5;
      border-radius: 8px;
    }
    .guideline {
      white-space: pre-line;
      line-height: 1.6;
    }
    .emergency-high {
      color: #d32f2f;
      font-weight: bold;
    }
    .emergency-medium {
      color: #f57c00;
    }
    .emergency-low {
      color: #388e3c;
    }
  </style>
</head>
<body>
  <h1>🚑 응급 상황 분석</h1>
  
  <div class="upload-area">
    <input type="file" id="fileInput" accept="video/*,audio/*">
    <button onclick="analyzeFile()">분석하기</button>
  </div>

  <div id="loading" style="display: none;">분석 중...</div>
  <div id="error" style="display: none; color: red;"></div>
  <div id="result"></div>

  <script>
    async function analyzeFile() {
      const fileInput = document.getElementById('fileInput');
      const file = fileInput.files[0];
      
      if (!file) {
        alert('파일을 선택해주세요.');
        return;
      }

      const formData = new FormData();
      formData.append('file', file);

      const loading = document.getElementById('loading');
      const error = document.getElementById('error');
      const result = document.getElementById('result');

      loading.style.display = 'block';
      error.style.display = 'none';
      result.innerHTML = '';

      try {
        const response = await fetch('http://localhost:8000/api/emergency/analyze-video', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error('분석 실패');
        }

        const data = await response.json();
        displayResult(data);
      } catch (err) {
        error.textContent = '오류: ' + err.message;
        error.style.display = 'block';
      } finally {
        loading.style.display = 'none';
      }
    }

    function displayResult(data) {
      const result = document.getElementById('result');
      const situation = data.situation;
      const emergencyClass = `emergency-${situation.emergency_level}`;

      result.innerHTML = `
        <div class="result">
          <h2>상황 분석 결과</h2>
          <p><strong>상황 ID:</strong> ${situation.situation_id}</p>
          <p><strong>긴급도:</strong> <span class="${emergencyClass}">${situation.emergency_level}</span></p>
          <p><strong>증상:</strong> ${situation.symptoms.join(', ')}</p>
          
          <h3>응급 대처 지침</h3>
          <div class="guideline">${data.guideline}</div>
        </div>
      `;
    }
  </script>
</body>
</html>
```

---

## 🔧 기술 스택

### 백엔드
- **FastAPI**: 웹 프레임워크
- **Whisper**: 음성-텍스트 변환 (STT)
- **PyTorch CNN**: 사운드 이벤트 분류
- **Google Gemini API**: 상황 분석 및 지침 생성
- **ChromaDB + LangChain**: RAG (문서 기반 지침 생성)

### API 서버
- **포트:** 기본 8000
- **Base URL:** `http://localhost:8000` (개발 환경)
- **문서:** `http://localhost:8000/docs` (Swagger UI)

---

## 📝 요청/응답 상세

### 요청 파라미터

#### `/api/emergency/analyze` (텍스트 기반)
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `stt_text` | string | ✅ | STT 변환된 텍스트 |
| `sound_event` | string | ✅ | 사운드 이벤트 ("낙상", "화재", "갇힘", "생활소음") |
| `sound_confidence` | float | ✅ | 사운드 이벤트 신뢰도 (0.0 ~ 1.0) |

#### `/api/emergency/analyze-video` (파일 업로드)
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `file` | File | ✅ | 업로드할 영상/오디오 파일 |

### 응답 필드

#### `situation` 객체
| 필드 | 타입 | 설명 |
|------|------|------|
| `situation_id` | string | 상황 ID (S0~S7) |
| `situation_label` | string | 상황 레이블 (영어) |
| `emergency_level` | string | 긴급도 ("low", "medium", "high") |
| `speech` | object | 음성 분석 결과 |
| `sound` | object | 사운드 분석 결과 |
| `symptoms` | array | 증상 태그 리스트 |
| `meta` | object | 메타데이터 (timestamp, language, source) |

#### `guideline` 문자열
- 마크다운 형식의 응급 대처 지침
- 단계별로 구성됨 (1단계, 2단계, 3단계 등)
- 혼자 있는 노인을 위한 구체적 행동 지시

---

## ⚠️ 주의사항

### 파일 크기 제한
- 기본 제한: 약 100MB
- 더 큰 파일은 서버 설정 변경 필요

### 처리 시간
- **STT (Whisper):** 10-30초 (파일 크기에 따라)
- **사운드 분석:** 1-5초
- **상황 분석 (Gemini):** 2-5초
- **지침 생성 (RAG):** 5-10초
- **총 소요 시간:** 약 20-50초

### 에러 처리
```javascript
try {
  const response = await fetch(url, options);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || '요청 실패');
  }
  
  const data = await response.json();
  // 성공 처리
} catch (error) {
  // 에러 처리
  console.error('오류:', error);
}
```

---

## 🚀 서버 실행 방법

### 개발 환경
```bash
# 가상환경 활성화
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 서버 실행
uvicorn main:app --reload
```

### 프로덕션 환경
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📞 연락처 및 지원

### API 문서
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 테스트
- 서버 실행 후 `http://localhost:8000/docs`에서 직접 테스트 가능
- 파일 업로드 기능도 Swagger UI에서 테스트 가능

---

## 💡 사용 팁

1. **파일 형식**: `.wav` 오디오 파일이 가장 빠르게 처리됩니다
2. **에러 처리**: 네트워크 오류, 타임아웃 등을 고려한 에러 핸들링 구현
3. **로딩 상태**: 분석 중 사용자에게 로딩 상태 표시 권장
4. **결과 표시**: `guideline`은 마크다운 형식이므로 적절히 렌더링 필요
5. **긴급도 표시**: `emergency_level`에 따라 시각적으로 구분하여 표시

---

## 📚 추가 자료

- **전체 파이프라인 설명**: `PIPELINE_FLOW.md`
- **비대칭 케이스 처리**: `ASYMMETRIC_CASES.md`
- **파일 업로드 가이드**: `HOW_TO_UPLOAD_FILES.md`

