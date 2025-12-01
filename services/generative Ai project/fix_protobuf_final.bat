@echo off
echo ========================================
echo protobuf 버전 충돌 최종 해결
echo ========================================
echo.

echo [1/2] protobuf 5.x 설치 중...
pip install "protobuf>=5.0,<6.0"

echo.
echo [2/2] google-generativeai 설치 중...
pip install google-generativeai

echo.
echo ========================================
echo 완료!
echo ========================================
echo.
echo 참고: mediapipe와의 충돌 경고가 나올 수 있지만,
echo 이 프로젝트에서는 mediapipe를 사용하지 않으므로 문제없습니다.
echo.
echo 이제 다음 명령어로 테스트하세요:
echo   python example_gemini.py
echo.
pause

