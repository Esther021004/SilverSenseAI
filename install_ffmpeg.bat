@echo off
echo ========================================
echo FFmpeg 설치 도우미
echo ========================================
echo.

echo [1단계] winget으로 설치 시도...
winget install ffmpeg
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ FFmpeg 설치 완료!
    echo.
    echo 새 터미널을 열고 다음 명령어로 확인하세요:
    echo   ffmpeg -version
    pause
    exit /b 0
)

echo.
echo [2단계] winget 설치 실패. Chocolatey로 시도...
choco install ffmpeg -y
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ FFmpeg 설치 완료!
    echo.
    echo 새 터미널을 열고 다음 명령어로 확인하세요:
    echo   ffmpeg -version
    pause
    exit /b 0
)

echo.
echo ⚠️  자동 설치 실패
echo.
echo 수동 설치 방법:
echo 1. https://www.gyan.dev/ffmpeg/builds/ 접속
echo 2. ffmpeg-release-essentials.zip 다운로드
echo 3. C:\ffmpeg 에 압축 해제
echo 4. 환경 변수 Path에 C:\ffmpeg\bin 추가
echo 5. 새 터미널에서 ffmpeg -version 확인
echo.
pause

