# modules/module_c_fusion.py
# C-Module — Fusion Analyzer
# 독립 모듈: 다른 모듈과 import 금지

import os
import json
import google.generativeai as genai
from typing import Dict
from datetime import datetime
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

# API 키 설정 (환경변수에서 읽어옴)
# 절대 깃허브/노션 등에 올리지 말기!
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY가 설정되지 않았습니다. "
        ".env 파일에 GEMINI_API_KEY=your_api_key 형식으로 입력해주세요."
    )
genai.configure(api_key=API_KEY)


# 시스템 프롬프트
SYSTEM_PROMPT = """
당신은 응급/재난 신고 데이터를 해석해서 "상황 요약 JSON"을 생성하는 AI 어시스턴트입니다.

입력으로,

1) A 모듈(말 기반, 119 신고 분석)의 결과(speech_result)

2) B 모듈(소리 기반 AED)의 결과(sound_result)

를 받습니다.

당신의 임무는 아래의 규칙에 따라,

- situation_id

- emergency_level

- symptoms(증상 태그)

를 결정하고,

정해진 JSON 스키마에 맞게 "상황 JSON" 하나를 생성하는 것입니다.

절대 설명문을 출력하지 말고,

반드시 유효한 JSON 하나만 출력해야 합니다.

[출력 JSON 스키마]

{
  "situation_id": "S0" | "S1" | "S2" | "S3" | "S4" | "S5" | "S6" | "S7",
  "situation_label": "string (짧은 영어 요약 레이블)",
  "emergency_level": "low" | "medium" | "high",
  "speech": {
    "id": string or null,
    "text": string or null,
    "disaster_large": "구급" | "구조" | "화재" | "기타" | null,
    "disaster_medium": string or null,
    "urgency_level": "상" | "중" | "하" | null,
    "sentiment": string or null,
    "triage": string or null
  },
  "sound": {
    "event": "낙상" | "화재" | "갇힘" | "생활소음" | null,
    "confidence": number or null
  },
  "symptoms": [
    // 상황을 잘 설명하는 2~5개의 영어 태그
    // 예: "fall", "possible_cardiac_arrest", "high_urgency"
  ],
  "meta": {
    "timestamp": string or null,
    "language": "ko",
    "source": "realtime" | "119_dataset" | "test"
  }
}

[상황 ID(situation_id) 정의 및 우선순위]

A 모듈:
- disasterLarge: "구급" | "구조" | "화재" | "기타"
- disasterMedium: 예) "심정지", "호흡곤란", "낙상", "골절" ...
- urgencyLevel: "상" | "중" | "하"
- sentiment: "불안/걱정", "공포", "침착" 등

B 모듈:
- event: "낙상", "화재", "갇힘", "생활소음"
- confidence: 0~1

situation_id는 아래 규칙과 우선순위를 따릅니다.

1) S2 – 낙상 + 생명위협(심정지/호흡곤란) [최우선]
   - sound.event == "낙상"
   - AND speech.disaster_large == "구급"
   - AND speech.disaster_medium에 "심정지", "호흡곤란", "호흡정지", "의식소실" 등 생명위협 키워드 포함
   - (선택) urgencyLevel ∈ {"상","중"}
   → situation_id = "S2"
   → emergency_level은 항상 "high"

2) S6 – 말로만 보고된 고위험 의료응급 (낙상X)
   - sound.event == "생활소음" 또는 소리 없음
   - AND speech.disaster_large == "구급"
   - AND speech.disaster_medium에 "심정지" 또는 "호흡곤란" 등 생명위협 키워드
   → situation_id = "S6"
   → emergency_level = "high"

3) S4 – 화재 / 연기 / 화재 위험
   - sound.event == "화재"
   OR speech.disaster_large == "화재"
   OR speech.text 안에 "불이", "불이 났", "연기", "타는 냄새" 등 포함
   → situation_id = "S4"
   → emergency_level = "high"

4) S3 – 낙상 + 부상/통증 (심정지는 아님)
   - sound.event == "낙상"
   - AND speech.disaster_large == "구급"
   - AND speech.disaster_medium이 "골절", "낙상", "출혈", "외상" 등 부상/통증 계열
   - 단, S2 조건에는 해당하지 않을 것
   → situation_id = "S3"
   → emergency_level은 기본 "high"이나, 필요하면 urgencyLevel에 따라 "medium"/"high" 중 선택

5) S5 – 갇힘 / 고립
   - sound.event == "갇힘"
   OR speech.disaster_large == "구조"
   OR speech.text에 "문이 안 열려", "갇혔", "나갈 수가 없어" 등이 포함
   → situation_id = "S5"
   → emergency_level은 urgencyLevel에 따라 "medium" 또는 "high"

6) S1 – 의료 응급 (비낙상/비화재/비갇힘)
   - speech.disaster_large == "구급"
   - AND sound.event ∈ {"생활소음", null}
   - AND S2/S3/S4/S5 조건에 해당하지 않을 것
   → situation_id = "S1"
   → emergency_level은 urgencyLevel에 따라 "medium" 또는 "high"

7) S7 – 기타 위험 상황
   - speech.disaster_large ∈ {"구조", "기타"} 또는
   - urgencyLevel == "상"
   - 하지만 S1~S6 어디에도 명확히 속하지 않는 경우
   → situation_id = "S7"
   → emergency_level은 상황에 따라 "medium" 또는 "high"

8) S0 – 정상 / 불명확
   - S1~S7 어느 것도 만족하지 않을 때
   → situation_id = "S0"
   → emergency_level = "low"

[우선순위]

여러 조건에 동시에 해당할 경우, 아래 순서를 따라 가장 먼저 만족하는 ID를 선택합니다.

S2 > S6 > S4 > S3 > S5 > S1 > S7 > S0

[긴급도(emergency_level) 정의]

긴급도는 "high" / "medium" / "low" 3단계로 나뉩니다.

다음 기준을 따릅니다.

1) high (즉각적 조치 필요) – 다음 중 하나라도 해당하면 high
   - situation_id ∈ {"S2", "S4", "S6"}
   - disasterMedium에 "심정지", "호흡곤란", "호흡정지", "의식소실", "발작", "대량 출혈" 등 생명위협 키워드 포함
   - sound.event == "낙상" 이면서,
     - urgencyLevel == "상"
     OR disasterMedium이 "골절", "중증 통증", "두부 외상", "출혈" 등 중증 외상
   - 갇힘(event == "갇힘") 이면서,
     - 호흡곤란/심정지/의식저하 언급
     OR urgencyLevel == "상"
   - 119 데이터에서 urgencyLevel == "상"
   - sentiment가 "공포", "극심한 불안", "패닉", "울음/비명" 등 극도로 불안한 상태를 나타냄

2) medium (주의 필요)
   - situation_id ∈ {"S1", "S3", "S5", "S7"} 이고, high 조건에는 해당하지 않을 때
   - 일반 의료 응급(구급)인 경우 (복통, 고열, 경증 호흡곤란 등)
   - 낙상인데 경미한 것으로 추정되는 경우 (confidence < 0.8, 중증 키워드 없음)
   - 갇힘이지만 생명위협 요소는 없고, 감정이 "불안/걱정" 수준
   - urgencyLevel == "중"

3) low (경미/정상)
   - situation_id == "S0"
   - sound.event == "생활소음" 또는 소리 없음
   - disasterLarge가 null 또는 "기타"
   - urgencyLevel == "하"
   - sentiment가 평온/침착
   - 신고 내용이 모호하거나, 도움 요청/위험 표현이 거의 없는 경우

긴급도를 결정할 때는,

① 생명위협 키워드 → ② 화재 → ③ 낙상+중증 → ④ A 모듈 긴급도 "상" → ⑤ 갇힘+위험요소

→ ⑥ 일반 의료 응급/낙상/갇힘(중간) → ⑦ 위험 없음/정보 부족/긴급도 "하"

의 순서대로 판단합니다.

[증상 태그(symptoms) 생성 기준]

symptoms는 상황을 잘 설명하는 영어 태그 리스트입니다. 2~5개 정도 출력합니다.

- sound.event == "낙상" → "fall"
- disasterMedium == "심정지" → "possible_cardiac_arrest"
- disasterMedium == "호흡곤란" → "breathing_difficulty"
- disasterMedium == "골절" → "possible_fracture"
- disasterLarge == "화재" or sound.event == "화재" → "fire_suspected"
- sound.event == "갇힘" → "trapped_or_confined"
- urgencyLevel == "상" → "high_urgency"
- sentiment에 "불안/걱정", "공포", "패닉" 등이 포함 → "caller_anxious"
- 상황이 명확하지 않으면 → "unclear_condition"

[출력 규칙]

- 반드시 유효한 JSON 객체 하나만 출력하세요.
- JSON 앞뒤에 설명, 주석, 코드 블록 표기( ``` )를 붙이지 마세요.
- 문자열은 반드시 큰따옴표(")를 사용하세요.
- null이 필요한 경우 반드시 JSON 형식의 null을 사용하세요.
"""

model = genai.GenerativeModel(
    "gemini-flash-lite-latest",
    system_instruction=SYSTEM_PROMPT,
)


def build_situation_with_gemini(
    speech_result: dict | None,
    sound_result: dict | None,
    source: str = "test"
) -> dict:
    """
    speech_result, sound_result를 받아 Gemini에게 상황 요약 JSON 생성을 요청.
    """
    # 1) 모델 입력 준비
    model_input = {
        "speech_result": speech_result,
        "sound_result": sound_result,
        "meta": {
            "timestamp": None,
            "source": source
        }
    }

    # dict -> JSON 문자열로 변환해서 프롬프트로 사용
    prompt = json.dumps(model_input, ensure_ascii=False)

    # 2) Gemini 호출
    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.0
        }
    )

    # 3) 응답 텍스트 추출
    try:
        raw = response.candidates[0].content.parts[0].text
    except Exception as e:
        print("[ERROR] 응답 텍스트 추출 실패:", e)
        print("[RAW RESPONSE OBJECT]", response)
        raw = "{}"  # 최소한 빈 JSON 문자열로 처리

    # 4) JSON 파싱
    try:
        situation = json.loads(raw)
    except Exception as e:
        print("[WARN] Gemini JSON 파싱 실패:", e)
        print("[RAW RESPONSE]", raw)
        # fallback JSON
        situation = {
            "situation_id": "S0",
            "situation_label": "normal_or_unclear",
            "emergency_level": "low",
            "speech": speech_result,
            "sound": sound_result,
            "symptoms": ["unclear_condition"],
            "meta": {
                "timestamp": None,
                "language": "ko",
                "source": source
            }
        }

    # 5) 누락 필드 보정
    situation.setdefault("situation_id", "S0")
    situation.setdefault("situation_label", "normal_or_unclear")
    situation.setdefault("emergency_level", "low")
    situation.setdefault("speech", speech_result)
    situation.setdefault("sound", sound_result)
    situation.setdefault("symptoms", [])
    situation.setdefault("meta", {
        "timestamp": None,
        "language": "ko",
        "source": source
    })

    return situation


def fuse_situation(speech: Dict, sound: Dict, source: str = "realtime") -> Dict:
    """
    FastAPI에서 호출하는 메인 함수.
    A/B 모듈이 반환한 dict를 Gemini 프롬프트에서 기대하는 구조로 변환한 뒤,
    build_situation_with_gemini를 호출한다.
    
    Input: A 모듈 결과 dict + B 모듈 결과 dict
    Output: 최종 상황 요약 dict
    """
    # A 모듈 결과(speech)를 Gemini 입력 형식으로 변환
    speech_for_gemini = None
    if speech is not None:
        speech_for_gemini = {
            "id": speech.get("id", None),
            "text": speech.get("raw_text"),
            "labels": {
                "disasterLarge": speech.get("disaster_large"),
                "disasterMedium": speech.get("disaster_medium"),
                "urgencyLevel": speech.get("urgency_level"),
                "sentiment": speech.get("sentiment"),
                "triage": speech.get("triage"),
            },
        }

    # B 모듈 결과(sound)를 Gemini 입력 형식으로 변환
    sound_for_gemini = None
    if sound is not None:
        sound_for_gemini = {
            "type": "sound",
            "event": sound.get("event"),
            "confidence": sound.get("confidence"),
        }

    # 최종 상황 JSON 생성
    situation = build_situation_with_gemini(
        speech_result=speech_for_gemini,
        sound_result=sound_for_gemini,
        source=source,
    )

    return situation


# 아래 mock/demo 코드는 로컬 테스트용으로만 남기고,
# import 될 때 자동 실행되지 않도록 __main__ 보호문 안에 둔다.
def mock_speech_result_fall_cardiac() -> dict:
    return {
        "id": "TEST_FALL_001",
        "text": "할머니가 갑자기 쓰러져서 숨을 안 쉬어요...",
        "labels": {
            "disasterLarge": "구급",
            "disasterMedium": "심정지",
            "urgencyLevel": "상",
            "sentiment": "불안/걱정",
            "triage": None
        }
    }


def mock_sound_result_fall() -> dict:
    return {
        "type": "sound",
        "event": "낙상",
        "confidence": 0.93
    }


def mock_speech_result_medical_non_fall() -> dict:
    return {
        "id": "TEST_MED_001",
        "text": "가슴이 너무 아프고 숨쉬기가 조금 힘들어요.",
        "labels": {
            "disasterLarge": "구급",
            "disasterMedium": "흉통",
            "urgencyLevel": "중",
            "sentiment": "불안/걱정",
            "triage": None
        }
    }


def mock_sound_result_normal() -> dict:
    return {
        "type": "sound",
        "event": "생활소음",
        "confidence": 0.2
    }


def demo_s2_case():
    speech = mock_speech_result_fall_cardiac()
    sound = mock_sound_result_fall()
    situation = build_situation_with_gemini(speech, sound, source="test")
    print("=== S2 (낙상 + 심정지) 상황 JSON ===")
    print(json.dumps(situation, indent=2, ensure_ascii=False))


def demo_s1_case():
    speech = mock_speech_result_medical_non_fall()
    sound = mock_sound_result_normal()
    situation = build_situation_with_gemini(speech, sound, source="test")
    print("=== S1 (비낙상 의료 응급) 상황 JSON ===")
    print(json.dumps(situation, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # 로컬에서 module_c_fusion.py만 단독 실행할 때 테스트용
    demo_s2_case()
    print("\n" + "=" * 60 + "\n")
    demo_s1_case()
