# modules/module_a_speech.py
# A-Module — Speech Analyzer
# 독립 모듈: 다른 모듈과 import 금지

from typing import Dict
import sys
from pathlib import Path

# Module A의 intent_rules.py import
# module_A 폴더를 경로에 추가
module_a_path = Path(__file__).parent / "module_A"
if str(module_a_path) not in sys.path:
    sys.path.insert(0, str(module_a_path))

try:
    from intent_rules import map_intent
except ImportError:
    # Module A가 없을 경우를 대비한 fallback
    def map_intent(text: str) -> str:
        return "unknown"


def analyze_speech(stt_text: str) -> Dict:
    """
    A 모듈: 신고자 음성(STT 텍스트)을 분석해서
    재난 분류, 긴급도, 감정 등을 추출.
    
    Module A의 intent_rules.py를 사용하여 Intent 분류 후,
    Intent를 기존 출력 형식으로 변환.
    
    Input: STT 텍스트
    Output: 의료적 의미 태그 dict
    
    {
        "disaster_large": str,      # 예: "구급", "구조", "화재"
        "disaster_medium": str,      # 예: "심정지", "흉통", "낙상" 등
        "urgency_level": str,        # "상", "중", "하"
        "sentiment": str,            # "불안/걱정" 등
        "raw_text": str              # 원본 STT 텍스트
    }
    """
    
    # 1. Module A의 intent_rules로 Intent 분류
    intent = map_intent(stt_text)
    
    # 2. Intent → 기존 출력 형식 매핑
    intent_to_output = {
        # 교통사고
        "traffic_accident": {
            "disaster_large": "구조",
            "disaster_medium": "교통사고",
            "urgency_level": "상",
            "sentiment": "불안/걱정",
        },
        # 화재
        "fire": {
            "disaster_large": "화재",
            "disaster_medium": "화재",
            "urgency_level": "상",
            "sentiment": "불안/걱정",
        },
        # 심정지
        "cardiac_arrest": {
            "disaster_large": "구급",
            "disaster_medium": "심정지",
            "urgency_level": "상",
            "sentiment": "불안/걱정",
        },
        # 호흡곤란
        "breathing_difficulty": {
            "disaster_large": "구급",
            "disaster_medium": "호흡곤란",
            "urgency_level": "상",
            "sentiment": "불안/걱정",
        },
        # 흉통
        "chest_pain": {
            "disaster_large": "구급",
            "disaster_medium": "흉통",
            "urgency_level": "중",
            "sentiment": "불안/걱정",
        },
        # 의식소실
        "unconscious": {
            "disaster_large": "구급",
            "disaster_medium": "의식소실",
            "urgency_level": "상",
            "sentiment": "불안/걱정",
        },
        # 발작
        "seizure": {
            "disaster_large": "구급",
            "disaster_medium": "발작",
            "urgency_level": "상",
            "sentiment": "불안/걱정",
        },
        # 낙상
        "falling": {
            "disaster_large": "구급",
            "disaster_medium": "낙상",
            "urgency_level": "중",
            "sentiment": "불안/걱정",
        },
        # 출혈
        "bleeding": {
            "disaster_large": "구급",
            "disaster_medium": "출혈",
            "urgency_level": "중",
            "sentiment": "불안/걱정",
        },
        # 현기증
        "dizziness": {
            "disaster_large": "구급",
            "disaster_medium": "현기증",
            "urgency_level": "하",
            "sentiment": "불안/걱정",
        },
        # 폭행
        "assault": {
            "disaster_large": "구조",
            "disaster_medium": "폭행",
            "urgency_level": "상",
            "sentiment": "불안/걱정",
        },
    }
    
    # 3. Intent에 해당하는 출력 형식 가져오기 (없으면 기본값)
    output = intent_to_output.get(intent, {
        "disaster_large": "구급",
        "disaster_medium": None,
        "urgency_level": "하",
        "sentiment": "불안/걱정",
    })
    
    # 4. 최종 결과 반환
    return {
        "disaster_large": output["disaster_large"],
        "disaster_medium": output["disaster_medium"],
        "urgency_level": output["urgency_level"],
        "sentiment": output["sentiment"],
        "raw_text": stt_text,
    }
