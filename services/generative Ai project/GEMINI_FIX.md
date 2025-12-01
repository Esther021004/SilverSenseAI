# 🔧 Gemini 패키지 버전 충돌 해결

## 문제

`langchain-core`가 오래된 버전(0.3.80)으로 설치되어 최신 패키지들과 충돌합니다.

## 해결 방법

### 방법 1: 자동 스크립트 실행 (가장 쉬움)

```bash
fix_gemini_dependencies.bat
```

### 방법 2: 수동으로 명령어 실행

```bash
# 1. 오래된 langchain-core 제거
pip uninstall -y langchain-core

# 2. 최신 버전 설치
pip install "langchain-core>=1.1.0,<2.0.0"

# 3. protobuf 버전 조정 (mediapipe 호환)
pip install "protobuf>=4.25.3,<5"

# 4. Gemini 패키지 재설치
pip install langchain-google-genai google-generativeai
```

### 방법 3: requirements.txt로 한 번에 설치

```bash
# 먼저 오래된 패키지 제거
pip uninstall -y langchain-core protobuf

# 그 다음 requirements.txt 설치
pip install -r requirements.txt
```

---

## 확인

설치 후 다음 명령어로 테스트:

```bash
python example_gemini.py
```

---

## 문제가 계속되면

모든 LangChain 관련 패키지를 제거하고 재설치:

```bash
pip uninstall -y langchain-core langchain-openai langchain-community langchain-text-splitters langchain-google-genai

pip install "langchain-core>=1.1.0,<2.0.0"
pip install langchain-openai langchain-community langchain-text-splitters
pip install langchain-google-genai google-generativeai
```

