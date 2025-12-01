# FFmpeg 설치 가이드 (Windows)

Whisper는 내부적으로 FFmpeg를 사용하여 오디오 파일을 처리합니다. FFmpeg가 설치되어 있지 않으면 STT 기능이 작동하지 않을 수 있습니다.

## 방법 1: Chocolatey 사용 (추천 - 가장 간단)

### 1단계: Chocolatey 설치 확인
```cmd
choco --version
```

### 2단계: Chocolatey가 없으면 설치
PowerShell을 **관리자 권한**으로 실행 후:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### 3단계: FFmpeg 설치
```cmd
choco install ffmpeg
```

---

## 방법 2: 직접 다운로드 및 설치

### 1단계: FFmpeg 다운로드
1. https://ffmpeg.org/download.html 접속
2. **Windows builds** 클릭
3. **Windows builds from gyan.dev** 또는 **Windows builds from BtbN** 선택
4. **ffmpeg-release-essentials.zip** 다운로드

### 2단계: 압축 해제
1. 다운로드한 zip 파일을 압축 해제
2. 예: `C:\ffmpeg` 폴더에 압축 해제

### 3단계: 환경 변수 설정

#### 방법 A: GUI로 설정
1. **시작 메뉴** → **시스템 환경 변수 편집** 검색
2. **환경 변수** 버튼 클릭
3. **시스템 변수** 섹션에서 **Path** 선택 → **편집** 클릭
4. **새로 만들기** 클릭
5. FFmpeg의 `bin` 폴더 경로 입력:
   ```
   C:\ffmpeg\bin
   ```
   (실제 압축 해제한 경로에 맞게 수정)
6. **확인** 클릭하여 모든 창 닫기

#### 방법 B: 명령 프롬프트로 설정 (관리자 권한)
```cmd
setx /M PATH "%PATH%;C:\ffmpeg\bin"
```
(실제 압축 해제한 경로에 맞게 수정)

### 4단계: 새 터미널에서 확인
**기존 터미널을 닫고 새 터미널을 열어야** 환경 변수가 적용됩니다.

```cmd
ffmpeg -version
```

**성공 시 출력 예시:**
```
ffmpeg version 6.1.1 Copyright (c) 2000-2023 the FFmpeg developers
...
```

---

## 방법 3: winget 사용 (Windows 10/11)

### 1단계: winget 확인
```cmd
winget --version
```

### 2단계: FFmpeg 설치
```cmd
winget install ffmpeg
```

---

## 설치 확인

### 1. 새 터미널 열기
**중요**: 환경 변수 변경 후에는 **새 터미널을 열어야** 적용됩니다.

### 2. FFmpeg 버전 확인
```cmd
ffmpeg -version
```

**성공 시:**
```
ffmpeg version 6.1.1 ...
```

**실패 시:**
```
'ffmpeg'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램, 또는 배치 파일이 아닙니다.
```

---

## 문제 해결

### 문제 1: "ffmpeg를 찾을 수 없습니다"

**해결:**
1. 환경 변수 설정이 제대로 되었는지 확인
2. **새 터미널**을 열었는지 확인 (기존 터미널은 환경 변수 변경이 반영되지 않음)
3. FFmpeg의 `bin` 폴더 경로가 정확한지 확인

### 문제 2: Chocolatey 설치 실패

**해결:**
- PowerShell을 **관리자 권한**으로 실행
- 실행 정책 확인:
  ```powershell
  Get-ExecutionPolicy
  ```
- 제한된 경우:
  ```powershell
  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### 문제 3: winget을 찾을 수 없음

**해결:**
- Windows 10 버전 1809 이상 또는 Windows 11 필요
- Microsoft Store에서 "App Installer" 업데이트

---

## 빠른 설치 (추천 순서)

1. **Chocolatey 사용** (가장 간단)
   ```cmd
   choco install ffmpeg
   ```

2. **winget 사용** (Windows 10/11)
   ```cmd
   winget install ffmpeg
   ```

3. **직접 다운로드** (위의 방법 2)

---

## 설치 후 확인

FFmpeg 설치 후:
1. **새 터미널** 열기
2. `ffmpeg -version` 실행
3. 서버 재시작
4. STT 기능 테스트

---

## 참고

- FFmpeg는 오픈소스 멀티미디어 프레임워크입니다
- Whisper는 FFmpeg를 사용하여 다양한 오디오 형식을 처리합니다
- 설치 후 시스템 재시작이 필요할 수 있습니다 (일반적으로는 새 터미널만 열면 됨)

