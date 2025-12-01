# server.py
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import whisper
import uvicorn
import os

# -----------------------------
# 1) intent_rules.py에서 규칙 가져오기
# -----------------------------
from intent_rules import map_intent

app = FastAPI()

# -----------------------------
# 2) Whisper 모델 로드
# -----------------------------
model = whisper.load_model("small")   # 필요하면 medium 가능


# -----------------------------
# 텍스트 분류 API
# -----------------------------
class TextRequest(BaseModel):
    text: str

@app.post("/api/text_classify")
def classify_text(payload: TextRequest):
    intent = map_intent(payload.text)

    return {
        "type": "text",
        "raw_text": payload.text,
        "intent": intent,
        "severity": "medium"
    }


# -----------------------------
# 음성 → STT → Intent API
# -----------------------------
@app.post("/api/stt_speech")
async def speech_to_intent(file: UploadFile = File(...)):
    temp_path = "temp_upload.wav"

    # 파일 저장
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Whisper 변환
    result = model.transcribe(temp_path, language="ko")
    text = result.get("text", "").strip()

    # Intent 매핑
    intent = map_intent(text)

    # temp 파일 삭제
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return {
        "type": "speech",
        "raw_text": text,
        "intent": intent,
        "severity": "medium"
    }


# -----------------------------
# 서버 실행
# -----------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
