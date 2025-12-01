# 🤖 Gemini 사용 가이드 (무료!)

Gemini 모델은 Google에서 제공하는 무료 LLM입니다. OpenAI보다 저렴하고(무료) 한국어 처리도 우수합니다!

## 🚀 빠른 시작

### 1. 패키지 설치

```bash
pip install langchain-google-genai google-generativeai
```

또는 requirements.txt 사용:

```bash
pip install -r requirements.txt
```

### 2. Google API 키 발급

1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. "Create API Key" 클릭
3. API 키 복사

### 3. .env 파일에 추가

`.env` 파일에 추가:

```
GOOGLE_API_KEY=your_google_api_key_here
```

### 4. 사용하기

```python
from rag.rag_system import RAGSystem

# Gemini 사용 (기본값)
rag_system = RAGSystem(
    llm_model="gemini-2.0-flash",  # 또는 "gemini-2.5-flash-lite"
    # GOOGLE_API_KEY 환경 변수에서 자동으로 읽음
)

# 또는 API 키 직접 전달
rag_system = RAGSystem(
    llm_model="gemini-2.0-flash",
    api_key="your_google_api_key"
)
```

---

## 📋 사용 가능한 Gemini 모델

| 모델명 | 설명 | 무료 |
|--------|------|------|
| `gemini-2.0-flash` | 최신, 빠르고 효율적 (기본값, 추천!) | ✅ |
| `gemini-2.5-flash-lite` | 더 가벼운 버전 | ✅ |
| `gemini-pro` | 구버전 (호환용) | ✅ |

---

## 💡 OpenAI vs Gemini

### OpenAI
- 💰 유료 (사용량에 따라 과금)
- 🚀 빠름
- 🌍 전 세계적으로 널리 사용

### Gemini
- 🆓 **무료!**
- 🇰🇷 한국어 처리 우수
- ⚡ 무료 요금제에도 충분히 빠름

**추천**: RAG 시스템에서는 **Gemini가 더 경제적이고 실용적**입니다!

---

## 📝 예제

### 기본 사용 (Gemini)

```python
from rag.rag_system import RAGSystem

rag_system = RAGSystem(
    document_dir="document",
    persist_directory="./chroma_db",
    llm_model="gemini-2.0-flash"  # Gemini 사용 (최신)
)

situation_info = {
    "disasterLarge": "구급",
    "disasterMedium": "낙상",
    "urgencyLevel": "긴급",
    "sentiment": "불안",
    "triage": "적색"
}

result = rag_system.generate_guideline(situation_info)
print(result['guideline'])
```

### OpenAI 사용 (기존 방식)

```python
rag_system = RAGSystem(
    llm_model="gpt-3.5-turbo",  # OpenAI 사용
    api_key="sk-..."  # OpenAI API 키
)
```

---

## ⚙️ 코드에서 기본값 변경

`rag/rag_system.py`에서 기본 모델 변경:

```python
llm_model: str = "gemini-2.0-flash",  # 기본값
```

---

## 🔑 API 키 무료 한도

Gemini API는 **매우 관대한 무료 한도**를 제공합니다:
- Gemini 1.5 Flash: 분당 15회 요청, 일일 무제한
- Gemini 1.5 Pro: 분당 2회 요청

개인 프로젝트나 소규모 프로젝트에는 충분합니다!

---

## ❓ FAQ

**Q: Gemini가 OpenAI보다 성능이 낮나요?**  
A: 아닙니다! Gemini는 Google이 개발한 최신 LLM으로, 많은 작업에서 OpenAI와 비슷하거나 더 나은 성능을 보입니다.

**Q: 무료 한도가 부족하면?**  
A: Gemini는 무료 한도가 매우 관대합니다. 소규모 프로젝트에는 충분하며, 필요시 유료 플랜으로 업그레이드 가능합니다.

**Q: OpenAI와 Gemini 둘 다 사용 가능한가요?**  
A: 네! 모델명만 바꿔주면 됩니다. 코드는 자동으로 적절한 API를 선택합니다.

