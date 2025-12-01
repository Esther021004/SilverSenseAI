# 🔧 protobuf 버전 충돌 해결

## 문제

- `mediapipe`는 `protobuf<5` 요구
- `grpcio-status`, `opentelemetry-proto`는 `protobuf>=5.0` 요구
- 충돌 발생!

## 해결책

**이 프로젝트에서는 `mediapipe`를 사용하지 않으므로 `protobuf 5.x`를 사용합니다.**

### 실행

```bash
fix_protobuf_final.bat
```

### 또는 수동 실행

```bash
pip install "protobuf>=5.0,<6.0"
pip install google-generativeai
```

---

## 경고 무시

`mediapipe`와의 충돌 경고가 나올 수 있지만, 이 프로젝트에서는 `mediapipe`를 사용하지 않으므로 **문제없습니다**.

---

## 확인

설치 후 테스트:

```bash
python example_gemini.py
```

---

## 만약 mediapipe를 사용한다면?

만약 나중에 `mediapipe`가 필요하다면:

```bash
pip install "protobuf>=4.25.3,<5"
```

하지만 이 경우 다른 패키지들과 충돌할 수 있습니다.

