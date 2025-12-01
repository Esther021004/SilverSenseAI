# Proxies 오류 해결 방법

## 문제 원인

최신 `openai` (1.x) 및 `langchain-openai` 버전에서는 `proxies` 파라미터를 더 이상 지원하지 않습니다.

## 해결 방법

### 1. 패키지 업데이트 (권장)

터미널에서 다음 명령어 실행:

```bash
pip install --upgrade langchain-openai openai
```

### 2. 코드 확인

`rag/guideline_generator.py`에서 ChatOpenAI 초기화 시:
- ✅ `proxies` 파라미터 제거됨
- ✅ 환경 변수에서 API 키 자동 읽기
- ✅ 간단한 초기화 방식 사용

### 3. 프록시가 필요한 경우

프록시가 꼭 필요하다면 환경 변수로 설정:

**Windows CMD:**
```cmd
set HTTP_PROXY=http://user:pass@proxy:port
set HTTPS_PROXY=http://user:pass@proxy:port
```

**Windows PowerShell:**
```powershell
$env:HTTP_PROXY="http://user:pass@proxy:port"
$env:HTTPS_PROXY="http://user:pass@proxy:port"
```

### 4. 테스트

간단한 테스트 스크립트 실행:

```bash
python test_simple.py
```

또는 전체 테스트:

```bash
python example_usage.py
```

