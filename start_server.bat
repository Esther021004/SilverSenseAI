@echo off
echo ========================================
echo Emergency Assistant 서버 시작
echo ========================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

echo [서버 시작 중...]
echo.
echo 서버가 시작되면 브라우저에서 다음 주소로 접속하세요:
echo   http://localhost:8000/docs
echo.
echo 서버를 종료하려면 Ctrl + C를 누르세요.
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause

