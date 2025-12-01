# main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Dict
import os
import uuid

from modules.module_a_speech import analyze_speech
from modules.module_b_sound import analyze_sound, analyze_sound_from_file
from modules.module_c_fusion import fuse_situation

# 영상 → 오디오 추출을 위한 라이브러리
try:
    # moviepy 2.x는 video.io에서 VideoFileClip을 import
    from moviepy.video.io.VideoFileClip import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        # moviepy 1.x 호환성 (구버전)
        from moviepy.editor import VideoFileClip
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False
        # 서버 시작 시에만 경고 출력 (매번 출력하지 않도록)
        import sys
        if sys.argv[0].endswith('uvicorn') or 'main.py' in sys.argv[0]:
            print("⚠️  moviepy가 설치되지 않았습니다. 영상 분석 기능을 사용하려면 설치하세요: pip install moviepy")


app = FastAPI(title="Emergency Assistant (Local MVP)")

# CORS 설정 (웹 브라우저에서 API 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 임시 파일 저장 폴더
TEMP_DIR = "temp_media"
os.makedirs(TEMP_DIR, exist_ok=True)


# ==========================================
# 유틸리티 함수
# ==========================================
def extract_audio_from_video(video_path: str) -> str:
    """
    mp4 등 영상 파일에서 오디오 트랙만 추출하여 WAV 파일로 저장.
    
    Input: 영상 파일 경로
    Output: 추출된 오디오 WAV 파일 경로
    """
    if not MOVIEPY_AVAILABLE:
        raise ImportError("moviepy가 설치되지 않았습니다. pip install moviepy")
    
    audio_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}.wav")
    
    clip = VideoFileClip(video_path)
    # B 모듈이 기대하는 샘플링 레이트(16000)로 맞춤
    clip.audio.write_audiofile(
        audio_path,
        fps=16000,
        codec="pcm_s16le",
        verbose=False,
        logger=None,
    )
    clip.close()
    
    return audio_path


def run_stt_on_wav(wav_path: str) -> str:
    """
    오디오 파일에서 음성을 텍스트로 변환 (STT).
    
    Module A의 Whisper 모델을 사용하여 STT 수행.
    """
    try:
        # 경로를 절대 경로로 변환하고 정규화
        wav_path = os.path.abspath(wav_path)
        # Windows 경로 구분자를 정규화 (백슬래시 → 슬래시로 변환)
        wav_path_normalized = wav_path.replace('\\', '/')
        
        # 파일 존재 여부 확인
        if not os.path.exists(wav_path):
            print(f"❌ STT 오류: 오디오 파일을 찾을 수 없습니다. 경로: {wav_path}")
            return "음성을 인식할 수 없습니다."
        
        # 파일 크기 확인
        file_size = os.path.getsize(wav_path)
        print(f"✅ STT 시작: {wav_path} (파일 크기: {file_size} bytes)")
        
        # 파일이 비어있는지 확인
        if file_size == 0:
            print("❌ STT 오류: 오디오 파일이 비어있습니다.")
            return "음성을 인식할 수 없습니다."
        
        import whisper
        # Whisper 모델 로드 (small 모델 사용, 필요시 base/tiny로 변경 가능)
        print("🔄 Whisper 모델 로드 중...")
        model = whisper.load_model("small")
        print("✅ Whisper 모델 로드 완료")
        
        # transcribe 호출 전에 파일 존재 재확인
        if not os.path.exists(wav_path):
            print(f"❌ STT 오류: transcribe 호출 전 파일이 사라졌습니다. 경로: {wav_path}")
            return "음성을 인식할 수 없습니다."
        
        print(f"🔄 음성 인식 중... (파일: {wav_path})")
        
        # Whisper transcribe는 내부적으로 ffmpeg를 사용하는데, 
        # Windows에서 경로 문제가 발생할 수 있으므로 여러 방법 시도
        result = None
        last_error = None
        
        # 방법 1: 원본 절대 경로 사용 (Windows 백슬래시)
        try:
            print(f"   시도 1: 절대 경로 (백슬래시)")
            result = model.transcribe(wav_path, language="ko")
            print(f"   ✅ 성공!")
        except (FileNotFoundError, OSError) as e1:
            last_error = e1
            print(f"   ❌ 실패: {e1}")
            
            # 방법 2: 정규화된 경로 사용 (슬래시)
            try:
                print(f"   시도 2: 정규화된 경로 (슬래시)")
                result = model.transcribe(wav_path_normalized, language="ko")
                print(f"   ✅ 성공!")
            except (FileNotFoundError, OSError) as e2:
                last_error = e2
                print(f"   ❌ 실패: {e2}")
                
                # 방법 3: 상대 경로로 변환 시도
                try:
                    rel_path = os.path.relpath(wav_path)
                    print(f"   시도 3: 상대 경로")
                    result = model.transcribe(rel_path, language="ko")
                    print(f"   ✅ 성공!")
                except (FileNotFoundError, OSError) as e3:
                    last_error = e3
                    print(f"   ❌ 실패: {e3}")
                    raise FileNotFoundError(f"모든 경로 형식 시도 실패. 마지막 오류: {e3}")
        
        if result is None:
            raise FileNotFoundError(f"STT transcribe 실패: {last_error}")
        
        text = result.get("text", "").strip()
        
        if not text:
            # STT 실패 시 기본 텍스트 반환
            print("⚠️  STT 결과가 비어있습니다.")
            return "음성을 인식할 수 없습니다."
        
        print(f"✅ STT 완료: {text[:50]}...")  # 처음 50자만 출력
        return text
    except ImportError:
        # whisper가 설치되지 않은 경우 더미 텍스트 반환
        print("⚠️  whisper가 설치되지 않았습니다. STT 기능을 사용하려면: pip install openai-whisper")
        return "할머니가 갑자기 쓰러져서 숨을 안 쉬어요..."
    except FileNotFoundError as e:
        # 파일을 찾을 수 없는 경우
        print(f"❌ STT 오류: 파일을 찾을 수 없습니다. 경로: {wav_path}")
        print(f"   상세 오류: {e}")
        return "음성을 인식할 수 없습니다."
    except Exception as e:
        # 기타 오류 발생 시
        print(f"⚠️  STT 오류 발생: {e}")
        print(f"   오류 타입: {type(e).__name__}")
        import traceback
        print(f"   상세 오류:\n{traceback.format_exc()}")
        return "음성을 인식할 수 없습니다."


class EmergencyAnalyzeRequest(BaseModel):
    stt_text: str
    sound_event: str
    sound_confidence: float


class EmergencyAnalyzeResponse(BaseModel):
    situation: Dict
    guideline: str


class EmergencyAnalyzeVideoResponse(BaseModel):
    situation: Dict
    guideline: str


class QuestionRequest(BaseModel):
    question: str
    situation: Dict  # 현재 상황 정보


class QuestionResponse(BaseModel):
    answer: str


# 정적 파일 서빙 (HTML 파일)
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Emergency backend running"}

@app.get("/app")
def serve_app():
    """HTML 앱 제공"""
    return FileResponse("silversense_ai.html")

@app.get("/index")
def serve_index():
    """시작 페이지 제공"""
    return FileResponse("index.html")


@app.post("/api/emergency/analyze", response_model=EmergencyAnalyzeResponse)
def analyze_emergency(req: EmergencyAnalyzeRequest):
    """
    외부에서 호출하는 메인 API.
    
    Process Flow:
    1. A-Module: analyze_speech(stt_text)
    2. B-Module: analyze_sound(sound_event, confidence)
    3. C-Module: fuse_situation(speech, sound)
    4. 상황 ID에 따라 간단한 도움말 생성 (추후 Gemini Flash-Lite로 대체)
    """
    # 1. A 모듈 (음성 분석)
    speech_result = analyze_speech(req.stt_text)

    # 2. B 모듈 (사운드 분석)
    sound_result = analyze_sound(req.sound_event, req.sound_confidence)

    # 3. C 모듈 (퓨전) - Gemini를 사용한 상황 분석
    situation = fuse_situation(
        speech=speech_result,
        sound=sound_result,
        source="realtime"
    )

    # 4. 상황에 따른 안내문 생성 (RAG 사용)
    try:
        from services.rag_client import generate_guideline_from_situation
        guideline = generate_guideline_from_situation(situation)
    except ImportError:
        # RAG가 없으면 기본 안내문 사용
        if situation.get("situation_id") == "S2":
            guideline = "지금 즉시 119에 신고하고, 심폐소생술이 가능한 사람을 찾으세요."
        elif situation.get("situation_id") in ["S1", "S3", "S5", "S6", "S7"]:
            guideline = "환자를 편안히 앉히고 통증이 심해지면 즉시 119에 신고하세요."
        else:
            guideline = "증상을 관찰하고 악화되면 바로 119에 신고하세요."

    return EmergencyAnalyzeResponse(
        situation=situation,
        guideline=guideline,
    )


# python-multipart가 설치되어 있는지 확인
try:
    import multipart
    MULTIPART_AVAILABLE = True
except ImportError:
    MULTIPART_AVAILABLE = False


if MULTIPART_AVAILABLE:
    @app.post("/api/emergency/analyze-video", response_model=EmergencyAnalyzeVideoResponse)
    async def analyze_emergency_video(file: UploadFile = File(...)):
        """
        영상 파일 또는 오디오 파일을 업로드하여 응급 상황을 분석하는 API.
        
        지원 형식:
        - 영상: mp4, avi, mov 등 (moviepy가 지원하는 형식)
        - 오디오: wav, mp3 등 (직접 오디오 파일)
        
        Process Flow:
        1. 파일 업로드 및 임시 저장
        2. 영상인 경우 → 오디오 추출 (wav는 건너뜀)
        3. 오디오 → STT → A 모듈 (음성 분석)
        4. 오디오 → B 모듈 (사운드 분석)
        5. A+B → C 모듈 (퓨전) → 최종 situation JSON
        
        Input: mp4 영상 파일 또는 wav 오디오 파일
        Output: {
            "situation": {...},  # 최종 상황 분석 JSON
            "guideline": "..."    # 응급 대처 가이드라인
        }
        """
        video_path = None
        audio_path = None
        
        try:
            # 1. 업로드된 파일을 TEMP_DIR에 저장
            file_id = uuid.uuid4().hex
            file_ext = os.path.splitext(file.filename)[1] or ".mp4"
            uploaded_path = os.path.join(TEMP_DIR, f"{file_id}{file_ext}")
            
            file_bytes = await file.read()
            with open(uploaded_path, "wb") as f:
                f.write(file_bytes)
            
            # 2. 파일 형식 확인 및 오디오 추출/복사
            file_ext_lower = file_ext.lower()
            
            # 오디오 파일인 경우 (wav, mp3 등)
            if file_ext_lower in ['.wav', '.mp3', '.m4a', '.flac', '.ogg']:
                # 오디오 파일은 그대로 사용
                audio_path = uploaded_path
            else:
                # 영상 파일인 경우 → 오디오 추출
                if not MOVIEPY_AVAILABLE:
                    raise ImportError("moviepy가 설치되지 않았습니다. pip install moviepy")
                
                video_path = uploaded_path
                audio_path = extract_audio_from_video(video_path)
            
            # 3. 오디오로 STT 수행 → A 모듈
            stt_text = run_stt_on_wav(audio_path)
            speech_result = analyze_speech(stt_text)
            
            # 4. 오디오로 B 모듈 (AED CNN 모델)
            sound_full = analyze_sound_from_file(audio_path)
            
            # C 모듈이 기대하는 형태로 변환
            sound_result = {
                "event": sound_full.get("event", "생활소음"),
                "confidence": sound_full.get("confidence", 0.5),
            }
            
            # 5. C 모듈 (Fusion + Gemini)
            situation = fuse_situation(
                speech=speech_result,
                sound=sound_result,
                source="realtime"
            )
            
            # 6. 상황에 따른 안내문 생성 (RAG 사용)
            try:
                from services.rag_client import generate_guideline_from_situation
                guideline = generate_guideline_from_situation(situation)
            except ImportError:
                # RAG가 없으면 기본 안내문 사용
                if situation.get("situation_id") == "S2":
                    guideline = "지금 즉시 119에 신고하고, 심폐소생술이 가능한 사람을 찾으세요."
                elif situation.get("situation_id") in ["S1", "S3", "S5", "S6", "S7"]:
                    guideline = "환자를 편안히 앉히고 통증이 심해지면 즉시 119에 신고하세요."
                else:
                    guideline = "증상을 관찰하고 악화되면 바로 119에 신고하세요."
            
            return EmergencyAnalyzeVideoResponse(
                situation=situation,
                guideline=guideline,
            )
        
        except Exception as e:
            # 에러 발생 시 상세 정보 반환
            raise Exception(f"영상 분석 중 오류 발생: {str(e)}")
        
        finally:
            # 7. 임시 파일 정리
            for path in [video_path, audio_path]:
                if path and os.path.exists(path):
                    try:
                        # 원본 업로드 파일과 추출된 오디오 파일 모두 삭제
                        os.remove(path)
                    except Exception:
                        pass
else:
    # python-multipart가 없으면 엔드포인트를 등록하지 않음
    @app.post("/api/emergency/analyze-video")
    async def analyze_emergency_video_disabled():
        return {
            "error": "python-multipart가 설치되지 않았습니다.",
            "message": "영상 업로드 기능을 사용하려면 다음 명령어를 실행하세요: pip install python-multipart"
        }


# 질문-답변 API
@app.post("/api/emergency/ask", response_model=QuestionResponse)
def ask_question(req: QuestionRequest):
    """
    사용자의 질문에 답변하는 API.
    현재 상황 정보를 바탕으로 질문에 맞는 답변을 생성합니다.
    """
    try:
        import google.generativeai as genai
        from dotenv import load_dotenv
        import os
        import traceback
        
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
            return QuestionResponse(
                answer="죄송합니다. AI 답변 기능을 사용할 수 없습니다. API 키가 설정되지 않았습니다."
            )
        
        print(f"✅ API 키 확인 완료 (길이: {len(api_key)})")
        genai.configure(api_key=api_key)
        
        # 상황 정보 요약
        situation = req.situation
        situation_id = situation.get("situation_id", "S0")
        emergency_level = situation.get("emergency_level", "low")
        symptoms = situation.get("symptoms", [])
        
        # 프롬프트 구성
        prompt = f"""당신은 응급 상황에서 혼자 있는 노인을 도와주는 친절한 상담사입니다.

현재 상황:
- 상황 ID: {situation_id}
- 긴급도: {emergency_level}
- 증상: {', '.join(symptoms) if symptoms else '없음'}

사용자 질문: {req.question}

위 상황을 고려하여 사용자의 질문에 친절하고 명확하게 답변해주세요.
- 짧고 명확한 답변 (2-3문장)
- 혼자 있는 노인이 스스로 할 수 있는 방법만 제시
- 걱정을 덜어주는 따뜻한 톤
- 필요시 119 신고를 권장

답변만 출력하세요 (설명 없이):"""
        
        # 여러 모델 시도 (할당량 초과 시 대체 모델 사용)
        models_to_try = [
            'gemini-2.0-flash',  # 최신 모델 (1순위)
            'gemini-1.5-flash',  # 안정적인 무료 모델 (2순위)
            'gemini-1.5-pro'     # 대체 모델 (3순위)
        ]
        
        last_error = None
        for model_name in models_to_try:
            try:
                print(f"🔄 모델 시도: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                answer = response.text.strip()
                print(f"✅ 답변 생성 성공: {model_name}")
                return QuestionResponse(answer=answer)
            except Exception as e:
                error_str = str(e)
                last_error = e
                print(f"❌ 모델 {model_name} 오류: {error_str[:200]}")
                
                # 할당량 초과 오류가 아니면 다음 모델 시도하지 않음
                if '429' not in error_str and 'quota' not in error_str.lower():
                    print(f"⚠️  할당량 초과가 아닌 오류로 중단: {error_str[:100]}")
                    break
                # 할당량 초과면 다음 모델 시도
                print(f"⚠️  할당량 초과, 다음 모델 시도...")
                continue
        
        # 모든 모델 실패 시 오류 메시지 반환
        if last_error:
            error_str = str(last_error)
            print(f"❌ 모든 모델 실패. 마지막 오류: {error_str[:300]}")
            
            if '429' in error_str or 'quota' in error_str.lower():
                return QuestionResponse(
                    answer="죄송합니다. 현재 AI 서비스 사용량이 초과되었습니다. 잠시 후 다시 시도해주세요."
                )
            elif 'API key' in error_str or 'authentication' in error_str.lower():
                return QuestionResponse(
                    answer="죄송합니다. API 인증 오류가 발생했습니다. 관리자에게 문의해주세요."
                )
            elif 'network' in error_str.lower() or 'connection' in error_str.lower():
                return QuestionResponse(
                    answer="죄송합니다. 네트워크 연결 오류가 발생했습니다. 인터넷 연결을 확인해주세요."
                )
            else:
                # 개발 환경에서는 더 자세한 오류 정보 제공
                return QuestionResponse(
                    answer=f"죄송합니다. 답변 생성 중 오류가 발생했습니다. (오류: {error_str[:100]})"
                )
        else:
            return QuestionResponse(
                answer="죄송합니다. 답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            )
        
    except Exception as e:
        error_str = str(e)
        traceback_str = traceback.format_exc()
        print(f"❌ 예외 발생: {error_str}")
        print(f"📋 상세 오류:\n{traceback_str}")
        
        if '429' in error_str or 'quota' in error_str.lower():
            return QuestionResponse(
                answer="죄송합니다. 현재 AI 서비스 사용량이 초과되었습니다. 잠시 후 다시 시도해주세요."
            )
        elif 'API key' in error_str or 'authentication' in error_str.lower():
            return QuestionResponse(
                answer="죄송합니다. API 인증 오류가 발생했습니다. 관리자에게 문의해주세요."
            )
        else:
            return QuestionResponse(
                answer=f"죄송합니다. 답변 생성 중 오류가 발생했습니다. (오류: {error_str[:100]})"
            )

