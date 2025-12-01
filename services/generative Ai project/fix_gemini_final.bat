@echo off
echo ========================================
echo Gemini 최종 설정 (langchain-community 사용)
echo ========================================
echo.

echo [1/3] langchain-google-genai 제거 중...
pip uninstall -y langchain-google-genai

echo.
echo [2/3] protobuf 버전 조정 중...
pip install "protobuf>=4.25.3,<5"

echo.
echo [3/3] google-generativeai 설치 중...
pip install google-generativeai

echo.
echo ========================================
echo 완료!
echo ========================================
echo.
echo langchain-community를 통해 Gemini를 사용합니다.
echo (langchain-core 1.x와 호환됨)
echo.
echo 이제 다음 명령어로 테스트하세요:
echo   python example_gemini.py
echo.
pause

