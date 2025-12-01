# 🚀 서버 시작 가이드

## FastAPI 서버 실행 방법

### 1단계: 터미널 열기
- 명령 프롬프트(cmd) 또는 PowerShell 열기

### 2단계: 프로젝트 폴더로 이동
```cmd
cd C:\Users\esthe\emergency-assistant
```

### 3단계: 가상환경 활성화
```cmd
venv\Scripts\activate
```

**성공하면 프롬프트 앞에 `(venv)`가 표시됩니다:**
```
(venv) C:\Users\esthe\emergency-assistant>
```

### 4단계: 서버 실행
```cmd
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**성공하면 다음과 같은 메시지가 나타납니다:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 5단계: 서버 확인
브라우저에서 다음 주소로 접속:
```
http://localhost:8000/docs
```

Swagger UI가 보이면 성공!

---

## 빠른 실행 (배치 파일)

`start_server.bat` 파일을 만들었습니다. 더블클릭하면 자동으로 실행됩니다!

---

## 문제 해결

### "uvicorn을 찾을 수 없습니다" 오류
```cmd
pip install uvicorn[standard]
```

### "모듈을 찾을 수 없습니다" 오류
```cmd
pip install -r requirements.txt
```

### 포트가 이미 사용 중
다른 프로그램이 8000 포트를 사용 중일 수 있습니다.
- 다른 포트 사용: `uvicorn main:app --port 8080`
- 또는 해당 프로그램 종료

---

## 서버 종료
터미널에서 `Ctrl + C` 누르기

