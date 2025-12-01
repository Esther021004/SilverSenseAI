@echo off
echo ========================================
echo LangChain 패키지 버전 충돌 해결
echo ========================================
echo.

echo [1/2] 구버전 LangChain 패키지 제거 중...
pip uninstall -y langchain langchain-community langchain-classic langchain-text-splitters

echo.
echo [2/2] 최신 버전 패키지 설치 중...
pip install -r requirements.txt

echo.
echo ========================================
echo 완료!
echo ========================================
echo.
echo 이제 다음 명령어로 테스트하세요:
echo   python example_usage.py
echo.
pause

