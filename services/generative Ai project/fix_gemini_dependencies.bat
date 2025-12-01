@echo off
echo ========================================
echo Gemini 패키지 버전 충돌 해결
echo ========================================
echo.

echo [1/4] 오래된 langchain-core 제거 중...
pip uninstall -y langchain-core

echo.
echo [2/4] 최신 langchain-core 설치 중...
pip install "langchain-core>=1.1.0"

echo.
echo [3/4] protobuf 버전 조정 중...
pip install "protobuf>=4.25.3,<5"

echo.
echo [4/4] Gemini 패키지 재설치 중...
pip install langchain-google-genai google-generativeai

echo.
echo ========================================
echo 완료!
echo ========================================
echo.
echo 이제 다음 명령어로 테스트하세요:
echo   python example_gemini.py
echo.
pause

