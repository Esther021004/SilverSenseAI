# services/rag_client.py
# RAG 클라이언트 - 상황 JSON을 기반으로 안내문 생성

import os
import sys
from pathlib import Path
from typing import Dict, Optional
import logging

# RAG 모듈 경로 추가 (폴더 이름에 공백이 있어서 sys.path 사용)
RAG_PROJECT_DIR = Path(__file__).parent / "generative Ai project"
if str(RAG_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_PROJECT_DIR))

try:
    from rag.rag_system import RAGSystem
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    RAGSystem = None  # 타입 힌트를 위한 더미 값
    logging.warning(f"RAG 시스템을 불러올 수 없습니다: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 싱글톤 패턴: RAG 시스템을 한 번만 초기화
_rag_system: Optional[object] = None  # RAGSystem이 없을 수 있으므로 object로 변경


def _get_rag_system():
    """RAG 시스템 싱글톤 인스턴스 반환"""
    global _rag_system
    
    if not RAG_AVAILABLE or RAGSystem is None:
        return None
    
    if _rag_system is None:
        if RAGSystem is None:
            logger.error("RAGSystem 클래스를 불러올 수 없습니다.")
            return None
        
        try:
            # RAG 시스템 초기화
            # 문서 디렉토리와 벡터 DB 경로를 RAG 프로젝트 폴더 기준으로 설정
            document_dir = str(RAG_PROJECT_DIR / "document")
            persist_directory = str(RAG_PROJECT_DIR / "chroma_db")
            
            # 경로 확인
            if not Path(document_dir).exists():
                logger.error(f"문서 디렉토리가 없습니다: {document_dir}")
                return None
            
            # API 키는 환경변수에서 가져오기 (GEMINI_API_KEY 또는 GOOGLE_API_KEY)
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY 또는 GOOGLE_API_KEY가 설정되지 않았습니다.")
                return None
            
            logger.info(f"RAG 시스템 초기화 중... (문서: {document_dir}, 벡터DB: {persist_directory})")
            _rag_system = RAGSystem(
                document_dir=document_dir,
                persist_directory=persist_directory,
                llm_model="gemini-2.0-flash",  # Gemini 사용 (무료)
                api_key=api_key,
                rebuild_vectorstore=False  # 기존 벡터 스토어 사용
            )
            logger.info("RAG 시스템 초기화 완료")
        except Exception as e:
            logger.error(f"RAG 시스템 초기화 실패: {e}")
            import traceback
            logger.error(f"상세 오류:\n{traceback.format_exc()}")
            return None
    
    return _rag_system


def _convert_situation_to_rag_format(situation: Dict) -> Dict:
    """
    C 모듈의 situation 출력을 RAG가 기대하는 형식으로 변환
    
    C 모듈 출력 형식 (두 가지 가능):
    1. Gemini가 SYSTEM_PROMPT를 따르는 경우:
       {
           "speech": {
               "disaster_large": "구급",      # snake_case, 직접
               "disaster_medium": "심정지",
               "urgency_level": "상",
               ...
           }
       }
    
    2. speech_result를 그대로 넣는 경우:
       {
           "speech": {
               "labels": {
                   "disasterLarge": "구급",   # camelCase, labels 안
                   "disasterMedium": "심정지",
                   "urgencyLevel": "상",
                   ...
               }
           }
       }
    
    RAG 입력 형식:
    {
        "disasterLarge": "구급",      # camelCase
        "disasterMedium": "심정지",
        "urgencyLevel": "상",
        "sentiment": "불안/걱정",
        "triage": null
    }
    """
    speech = situation.get("speech", {})
    if not isinstance(speech, dict):
        speech = {}
    
    # 1순위: speech.labels에서 찾기 (camelCase)
    labels = speech.get("labels", {})
    
    # 2순위: speech에서 직접 찾기 (snake_case → camelCase 변환)
    speech_direct = {
        "disasterLarge": speech.get("disaster_large"),
        "disasterMedium": speech.get("disaster_medium"),
        "urgencyLevel": speech.get("urgency_level"),
        "sentiment": speech.get("sentiment"),
        "triage": speech.get("triage"),
    }
    
    # RAG 입력 형식으로 변환 (우선순위: labels > speech 직접)
    rag_input = {
        "disasterLarge": (
            labels.get("disasterLarge") or 
            speech_direct.get("disasterLarge")
        ),
        "disasterMedium": (
            labels.get("disasterMedium") or 
            speech_direct.get("disasterMedium")
        ),
        "urgencyLevel": (
            labels.get("urgencyLevel") or 
            speech_direct.get("urgencyLevel")
        ),
        "sentiment": (
            labels.get("sentiment") or 
            speech_direct.get("sentiment")
        ),
        "triage": (
            labels.get("triage") if "triage" in labels else 
            speech_direct.get("triage")
        ),
    }
    
    # None 값 처리
    for key, value in rag_input.items():
        if value is None:
            rag_input[key] = "알 수 없음" if key != "triage" else None
    
    # situation_id, emergency_level, symptoms, sound_event 추가 (RAG에서 활용)
    rag_input["situation_id"] = situation.get("situation_id", "S0")
    rag_input["emergency_level"] = situation.get("emergency_level", "low")
    rag_input["symptoms"] = situation.get("symptoms", [])
    
    # sound 정보 추가
    sound = situation.get("sound", {})
    if isinstance(sound, dict):
        rag_input["sound_event"] = sound.get("event", "없음")
        rag_input["sound_confidence"] = sound.get("confidence", None)
    else:
        rag_input["sound_event"] = "없음"
        rag_input["sound_confidence"] = None
    
    return rag_input


def _build_comprehensive_context(situation: Dict) -> str:
    """
    C 모듈의 전체 situation JSON에서 모든 정보를 추출하여
    RAG 시스템에 전달할 포괄적인 컨텍스트 문자열 생성
    
    situation JSON의 모든 필드를 활용:
    - situation_id, situation_label, emergency_level
    - symptoms (증상 태그)
    - speech (음성 분석 결과)
    - sound (사운드 분석 결과)
    - meta (메타데이터)
    """
    context_parts = []
    
    # 1. 상황 식별 정보 (구체적인 설명 포함)
    situation_id = situation.get("situation_id", "")
    situation_label = situation.get("situation_label", "")
    emergency_level = situation.get("emergency_level", "")
    
    # situation_id에 따른 구체적 설명
    situation_descriptions = {
        "S0": "정상 또는 불명확한 상황",
        "S1": "의료 응급 상황 (비낙상/비화재)",
        "S2": "낙상과 함께 생명위협 요소가 있는 긴급 상황 (심정지/호흡곤란 가능성)",
        "S3": "낙상과 함께 부상/통증이 있는 상황 (골절/외상 가능성)",
        "S4": "화재 또는 연기 관련 긴급 상황",
        "S5": "갇힘 또는 고립 상황",
        "S6": "말로만 보고된 고위험 의료 응급 상황 (낙상 없음)",
        "S7": "기타 위험 상황"
    }
    
    if situation_id:
        situation_desc = situation_descriptions.get(situation_id, situation_id)
        context_parts.append(f"상황: {situation_desc} (ID: {situation_id})")
    if situation_label:
        context_parts.append(f"상황 상세: {situation_label}")
    if emergency_level:
        emergency_descriptions = {
            "high": "긴급 (즉각 조치 필요)",
            "medium": "보통 (주의 필요)",
            "low": "경미 (관찰 필요)"
        }
        emergency_desc = emergency_descriptions.get(emergency_level, emergency_level)
        context_parts.append(f"긴급도: {emergency_desc}")
    
    # 2. 증상 정보 (symptoms) - 구체적으로 설명
    symptoms = situation.get("symptoms", [])
    if symptoms:
        symptom_map = {
            "fall": "낙상 발생",
            "possible_cardiac_arrest": "심정지 가능성 (생명위협)",
            "breathing_difficulty": "호흡곤란",
            "possible_fracture": "골절 가능성",
            "fire_suspected": "화재 의심",
            "trapped_or_confined": "갇힘 또는 고립",
            "high_urgency": "고위험 상황",
            "caller_anxious": "신고자 불안 상태",
            "unclear_condition": "상황 불명확",
            "not_breathing": "호흡 정지 (생명위협)",
            "chest_pain": "흉통"
        }
        
        korean_symptoms = [symptom_map.get(s, s) for s in symptoms]
        if korean_symptoms:
            context_parts.append(f"주요 증상: {', '.join(korean_symptoms)}")
            
            # 생명위협 증상이 있는지 확인
            life_threatening = ["possible_cardiac_arrest", "not_breathing", "breathing_difficulty"]
            if any(s in symptoms for s in life_threatening):
                context_parts.append("⚠️ 생명위협 요소 포함: 즉각적인 응급 조치 필요")
    
    # 3. 음성 분석 정보 (speech) - 구체적으로 설명
    speech = situation.get("speech", {})
    if isinstance(speech, dict):
        # speech에서 직접 정보 추출 (disaster_large 형식)
        disaster_large = speech.get("disaster_large") or speech.get("labels", {}).get("disasterLarge")
        disaster_medium = speech.get("disaster_medium") or speech.get("labels", {}).get("disasterMedium")
        urgency_level = speech.get("urgency_level") or speech.get("labels", {}).get("urgencyLevel")
        sentiment = speech.get("sentiment") or speech.get("labels", {}).get("sentiment")
        
        if disaster_large:
            disaster_descriptions = {
                "구급": "의료 응급 상황",
                "구조": "구조가 필요한 상황",
                "화재": "화재 관련 상황",
                "기타": "기타 상황"
            }
            disaster_desc = disaster_descriptions.get(disaster_large, disaster_large)
            context_parts.append(f"재난 유형(대분류): {disaster_desc}")
        if disaster_medium:
            context_parts.append(f"재난 유형(중분류): {disaster_medium}")
        if urgency_level:
            urgency_descriptions = {
                "상": "긴급 (상급)",
                "중": "보통 (중급)",
                "하": "경미 (하급)"
            }
            urgency_desc = urgency_descriptions.get(urgency_level, urgency_level)
            context_parts.append(f"음성 분석 긴급도: {urgency_desc}")
        if sentiment:
            context_parts.append(f"신고자 감정 상태: {sentiment}")
        
        # 원본 STT 텍스트 (중요한 정보)
        speech_text = speech.get("text") or speech.get("raw_text")
        if speech_text:
            context_parts.append(f"실제 신고 내용: \"{speech_text}\"")
    
    # 4. 사운드 분석 정보 (sound) - 구체적으로 설명
    sound = situation.get("sound", {})
    if isinstance(sound, dict):
        event = sound.get("event")
        confidence = sound.get("confidence")
        
        if event:
            event_descriptions = {
                "낙상": "낙상 사운드 감지됨",
                "화재": "화재 관련 사운드 감지됨",
                "갇힘": "갇힘 관련 사운드 감지됨",
                "생활소음": "일반 생활소음 (위험 없음)"
            }
            event_desc = event_descriptions.get(event, f"사운드 이벤트: {event}")
            context_parts.append(event_desc)
        if confidence is not None:
            if confidence >= 0.8:
                confidence_desc = f"높은 신뢰도 ({confidence:.2f})"
            elif confidence >= 0.5:
                confidence_desc = f"보통 신뢰도 ({confidence:.2f})"
            else:
                confidence_desc = f"낮은 신뢰도 ({confidence:.2f})"
            context_parts.append(f"사운드 감지 신뢰도: {confidence_desc}")
    
    # 5. 메타데이터 (선택적)
    meta = situation.get("meta", {})
    if isinstance(meta, dict) and meta.get("source"):
        context_parts.append(f"데이터 출처: {meta.get('source')}")
    
    # 모든 정보를 하나의 문자열로 결합
    comprehensive_context = ". ".join(context_parts) if context_parts else "상황 정보 없음"
    
    logger.debug(f"생성된 포괄적 컨텍스트: {comprehensive_context[:200]}...")
    
    return comprehensive_context


def generate_guideline_from_situation(situation: Dict) -> str:
    """
    Situation JSON을 기반으로 RAG/LLM에 요청하여
    한국어 응급 대처 지침 문장을 생성.
    
    Input: situation dict (C 모듈 출력 - 전체 situation JSON)
    Output: guideline string (한국어 안내문)
    
    C 모듈의 전체 situation JSON을 RAG 시스템에 전달하여
    모든 정보(situation_id, emergency_level, symptoms, speech, sound 등)를 활용합니다.
    """
    # RAG 시스템 가져오기
    rag_system = _get_rag_system()
    
    if rag_system is None:
        # RAG가 없으면 기본 안내문 사용 (혼자 있는 노인이 스스로 대처할 수 있는 방안)
        logger.warning("RAG 시스템을 사용할 수 없어 기본 안내문을 반환합니다.")
        situation_id = situation.get("situation_id", "S0")
        emergency_level = situation.get("emergency_level", "low")
        
        if situation_id == "S2" or emergency_level == "high":
            return "**1단계:** 가능한 한 편안한 자세를 취하세요. 무리하게 움직이지 마세요. 전화기가 가까이 있다면 천천히 기어가서 119에 전화하세요.\n\n**2단계:** 119에 전화가 연결되면 \"혼자 있는데 응급 상황입니다. 주소는 [주소]입니다\"라고 말하세요. 가능하면 문을 열어두세요."
        elif situation_id in ["S1", "S3", "S5", "S6", "S7"]:
            return "**1단계:** 가능하면 편안한 자세를 취하세요. 통증이 심해지면 무리하지 마세요.\n\n**2단계:** 즉시 119에 전화하세요. \"혼자 있는데 응급 상황입니다. 주소는 [주소]입니다\"라고 말하세요."
        else:
            return "**1단계:** 증상을 관찰하세요. 악화되는지 확인하세요.\n\n**2단계:** 증상이 악화되면 바로 119에 전화하세요. \"혼자 있는데 증상이 악화되고 있습니다\"라고 말하세요."
    
    try:
        # C 모듈의 전체 situation JSON에서 RAG가 필요한 정보 추출
        # situation_info: RAG 시스템이 기대하는 기본 형식 (disasterLarge, disasterMedium 등)
        situation_info = _convert_situation_to_rag_format(situation)
        
        # additional_context: situation JSON의 모든 추가 정보를 포함
        # - situation_id, emergency_level, symptoms, situation_label 등
        additional_context = _build_comprehensive_context(situation)
        
        # situation JSON 정보를 situation_info에 추가 (프롬프트에 직접 포함되도록)
        situation_info["situation_id"] = situation.get("situation_id", "S0")
        situation_info["emergency_level"] = situation.get("emergency_level", "low")
        situation_info["situation_label"] = situation.get("situation_label", "")
        situation_info["symptoms"] = situation.get("symptoms", [])
        
        # sound 정보 추가
        sound = situation.get("sound", {})
        if isinstance(sound, dict):
            situation_info["sound_event"] = sound.get("event", "없음")
            situation_info["sound_confidence"] = sound.get("confidence", "없음")
        else:
            situation_info["sound_event"] = "없음"
            situation_info["sound_confidence"] = "없음"
        
        # RAG로 지침 생성 (전체 situation 정보 활용)
        situation_id = situation.get("situation_id", "S0")
        emergency_level = situation.get("emergency_level", "low")
        logger.info(f"RAG 지침 생성 중... (situation_id: {situation_id}, emergency_level: {emergency_level})")
        
        result = rag_system.generate_guideline(
            situation_info=situation_info,
            additional_context=additional_context
        )
        
        # 결과에서 guideline 텍스트 추출
        guideline = result.get("guideline", "")
        
        if not guideline:
            # guideline이 비어있으면 report_message 사용
            guideline = result.get("report_message", "응급 상황입니다. 즉시 119에 신고하세요.")
        
        logger.info("RAG 지침 생성 완료")
        return guideline
        
    except Exception as e:
        logger.error(f"RAG 지침 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
        # 오류 발생 시 기본 안내문 반환 (혼자 있는 노인이 스스로 대처할 수 있는 방안)
        situation_id = situation.get("situation_id", "S0")
        emergency_level = situation.get("emergency_level", "low")
        
        if situation_id == "S2" or emergency_level == "high":
            return "**1단계:** 가능한 한 편안한 자세를 취하세요. 무리하게 움직이지 마세요. 전화기가 가까이 있다면 천천히 기어가서 119에 전화하세요.\n\n**2단계:** 119에 전화가 연결되면 \"혼자 있는데 응급 상황입니다. 주소는 [주소]입니다\"라고 말하세요. 가능하면 문을 열어두세요."
        elif situation_id in ["S1", "S3", "S5", "S6", "S7"]:
            return "**1단계:** 가능하면 편안한 자세를 취하세요. 통증이 심해지면 무리하지 마세요.\n\n**2단계:** 즉시 119에 전화하세요. \"혼자 있는데 응급 상황입니다. 주소는 [주소]입니다\"라고 말하세요."
        else:
            return "**1단계:** 증상을 관찰하세요. 악화되는지 확인하세요.\n\n**2단계:** 증상이 악화되면 바로 119에 전화하세요. \"혼자 있는데 증상이 악화되고 있습니다\"라고 말하세요."

