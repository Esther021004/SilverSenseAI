"""
RAG 기반 응급 지침 생성 모듈
상황 정보를 받아서 관련 지침을 검색하고 LLM으로 맞춤형 지침 생성
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.language_models import BaseChatModel

# OpenAI 지원
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

# Google Gemini 지원 (무료)
# google-generativeai를 직접 사용하는 어댑터 사용
try:
    from .gemini_adapter import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

from .embedding_store import EmbeddingStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GuidelineGenerator:
    """RAG 기반 응급 지침 생성기"""
    
    def __init__(
        self,
        embedding_store: EmbeddingStore,
        llm_model: str = "gemini-2.0-flash",  # 기본값을 Gemini로 변경 (무료, 최신)
        temperature: float = 0.3,
        api_key: Optional[str] = None
    ):
        """
        Args:
            embedding_store: EmbeddingStore 인스턴스
            llm_model: 사용할 LLM 모델명
                - OpenAI: "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"
                - Gemini: "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-pro" (무료)
            temperature: LLM temperature (낮을수록 일관성 높음)
            api_key: API 키 (OpenAI 또는 Google API 키)
        """
        self.embedding_store = embedding_store
        self.llm_model_name = llm_model.lower()
        
        # 모델 타입 감지 (gemini로 시작하면 Gemini, 그 외는 OpenAI)
        is_gemini = self.llm_model_name.startswith("gemini")
        
        # API 키 설정
        if is_gemini:
            # Gemini 사용
            if ChatGoogleGenerativeAI is None:
                raise ImportError(
                    "Gemini를 사용하려면 google-generativeai 패키지를 설치하세요:\n"
                    "pip install google-generativeai\n"
                    "또는: pip install langchain-google-genai"
                )
            
            if not api_key:
                api_key = os.getenv("GOOGLE_API_KEY")
            
            if not api_key:
                raise ValueError(
                    "Google API 키가 필요합니다. 환경변수 GOOGLE_API_KEY를 설정하거나 api_key 파라미터로 제공하세요.\n"
                    "API 키 발급: https://makersuite.google.com/app/apikey"
                )
            
            os.environ["GOOGLE_API_KEY"] = api_key
            
            # Gemini 모델 초기화
            self.llm = ChatGoogleGenerativeAI(
                model=llm_model,
                temperature=temperature,
                google_api_key=api_key
            )
            logger.info(f"Gemini 모델 사용: {llm_model} (무료)")
            
        else:
            # OpenAI 사용
            if ChatOpenAI is None:
                raise ImportError("OpenAI를 사용하려면 langchain-openai 패키지를 설치하세요: pip install langchain-openai")
            
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                raise ValueError(
                    "OpenAI API 키가 필요합니다. 환경변수 OPENAI_API_KEY를 설정하거나 api_key 파라미터로 제공하세요."
                )
            
            os.environ["OPENAI_API_KEY"] = api_key
            
            # OpenAI 모델 초기화
            self.llm = ChatOpenAI(
                model=llm_model,
                temperature=temperature
            )
            logger.info(f"OpenAI 모델 사용: {llm_model}")
        
        # Retriever 설정 (더 많은 문서 검색으로 컨텍스트 강화)
        self.retriever = self.embedding_store.get_retriever(k=6)
        
        # 프롬프트 템플릿 설정
        self._setup_prompts()
    
    def _setup_prompts(self):
        """프롬프트 템플릿 설정"""
        # 고령층 맞춤 지침 생성 프롬프트 (혼자 있는 노인이 스스로 대처)
        self.guideline_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 혼자 있는 고령층을 위한 응급 상황 대응 전문가입니다.
검색된 전문 문서의 지침을 반드시 참고하여, **혼자 있는 노인이 스스로 할 수 있는** 구체적이고 실용적인 응급 대처 방법을 안내하세요.

⚠️ 핵심 원칙: 다른 사람의 도움을 기대할 수 없는 상황입니다. 혼자서 할 수 있는 방법만 제시하세요.

🚨 가장 중요한 규칙: 긴급도(emergency_level)가 "high"인 경우, 1단계 첫 문장은 반드시 "지금 바로 119에 전화하세요."로 시작해야 합니다.

[긴급도별 우선순위 규칙 - 반드시 지켜야 함]

**emergency_level = "high"인 경우:**
- 1단계 첫 문장은 무조건 "지금 바로 119에 전화하세요." 또는 "지금 즉시 119에 전화하세요."
- 그 다음에 "전화 연결을 기다리면서 이렇게 하세요" 식으로 자세/환경 조정을 안내

**emergency_level = "medium" 또는 "low"인 경우:**
- 응급처치 후 119 신고 또는 증상 관찰 후 악화 시 신고

[상황 ID별 구체적 대응 가이드]

**S2 (낙상 + 생명위협, high)**: 
- 1단계 첫 문장: "지금 바로 119에 전화하세요. 전화를 걸 수 있으면 무조건 먼저 119를 누르세요."
- 전화가 손 닿는 거리에 없으면: "무리해서 일어나지 말고, 천천히 기어서 가까운 전화기를 향해 움직이세요."
- 가능한 한 편안한 자세 유지, 무리한 움직임 금지
- 119 신고 멘트: "혼자 있는데 쓰러져서 숨쉬기가 어렵습니다. 심정지 가능성이 있습니다. 주소는 [주소]입니다."

**S3 (낙상 + 부상, medium/high)**: 
- 움직임 최소화, 다친 부위를 움직이지 않기
- 전화기가 멀리 있으면: "무리해서 일어나지 말고, 가능한 범위에서 천천히 기어서 전화기 쪽으로 이동하세요."
- 119 신고 멘트: "혼자 있는데 넘어져서 [부위]가 아픕니다. 주소는 [주소]입니다."

**S4 (화재, high)**: 
- 1단계 첫 문장: "지금 바로 119에 전화하세요."
- 전화 연결을 기다리면서: 낮은 자세로 기어가기, 젖은 수건으로 코와 입 막기, 뜨거운 문 손잡이 확인
- 119 신고 멘트: "화재가 발생했습니다. 혼자 있습니다. 주소는 [주소]입니다."

**S5 (갇힘, medium/high)**: 
- emergency_level이 "high"면: 1단계 첫 문장은 "지금 바로 119에 전화하세요."
- emergency_level이 "medium"이면: 먼저 탈출 시도 후 119 신고
- 문 열기 시도 방법:
  * 문 손잡이를 여러 방향으로 돌려보세요 (위로, 아래로, 좌우로)
  * 문 아래쪽 틈새를 확인하고, 가능하면 얇은 카드나 열쇠로 문고리 밀어보기
  * 문이 밀리는지 당기는지 확인 (일부 문은 밀어야 열림)
- 창문이 있다면:
  * 창문 잠금 장치 확인 (레버, 손잡이 등)
  * 창문이 열리지 않으면 유리 깨기보다는 주변에 소리 지르기 우선
  * 창문이 열리면 주변에 도움 요청 (하지만 2층 이상이면 위험하니 조심)
- 전화 연결을 기다리면서:
  * 가능하면 문 근처나 창문 근처로 이동 (구조대가 찾기 쉽도록)
  * 주변에 소리 지르기 (벽을 두드리거나 큰 소리로 도움 요청)
  * 전화기 배터리가 부족하면 중요한 정보만 말하고 통화 시간 절약
- 119 신고 멘트: "혼자 있는데 [방/엘리베이터/지하실 등 구체적 위치]에 갇혔습니다. 문이 열리지 않습니다. 주소는 [주소]입니다."
- 통화 후:
  * 구조대가 도착할 때까지 문 근처에서 대기
  * 가능하면 문을 두드려서 위치를 알려주세요
  * 공기가 답답하면 창문 틈새나 문 틈새로 공기 순환 확인

**S6 (호흡곤란, high)**: 
- 1단계 첫 문장: "지금 숨쉬기 너무 힘들다면, 먼저 119에 전화하세요."
- 전화 연결을 기다리면서: 반좌위 자세, 옷 풀기, 심리적 안정
- 119 신고 멘트: "혼자 있는데 숨쉬기가 너무 어렵습니다. 주소는 [주소]입니다."

**S1 (의료 응급, medium)**: 
- 가슴이 아프고 숨쉬기 힘들면: 기대서 앉는 자세, 옷이 답답하면 윗단추와 허리 쪽 풀기
- 증상이 점점 심해지거나 5분 이상 줄어들지 않으면 119 신고
- 얼굴이 창백해지고 식은땀이 나거나, 정신이 멍해지면 바로 119 신고
- 119 신고 멘트: "혼자 있는데 가슴이 너무 아프고 숨쉬기가 조금 힘듭니다. 주소는 [주소]입니다."

**S0 (정상/불명확, low)**: 
- 증상 관찰, 악화 시 119 신고

상황 분석 결과 (반드시 이 정보를 모두 활용하세요):
- 상황 ID: {situation_id}
- 긴급도: {emergency_level}
- 재난 유형(대분류): {disaster_large}
- 재난 유형(중분류): {disaster_medium}
- 긴급도 레벨: {urgency_level}
- 감정 상태: {sentiment}
- 증상: {symptoms}
- 사운드 이벤트: {sound_event} (신뢰도: {sound_confidence})
- 추가 상황 정보: {additional_context}

검색된 전문 문서 지침 (반드시 참고하세요):
{context}"""),
            ("human", """위 상황 분석 결과와 검색된 전문 문서를 바탕으로, **혼자 있는 노인이 스스로 할 수 있는** 구체적이고 상황에 맞는 응급 대처 지침을 생성해주세요.

🚨 **중요: 위의 상황별 가이드는 참고용입니다. 반드시 다음을 지켜주세요:**

1. **가이드를 그대로 복사하지 마세요**: 
   - 위의 S2, S3, S4, S5 등 가이드는 "이런 식으로 작성하라"는 예시입니다.
   - 실제 상황({situation_id}, {emergency_level}, {symptoms})에 맞게 **새롭게** 지침을 생성하세요.
   - 검색된 전문 문서({context})의 구체적 방법을 적극 활용하세요.

2. **검색된 문서를 반드시 활용하세요**:
   - 검색된 문서에 구체적인 방법이 있으면 그 방법을 우선 사용하세요.
   - 문서의 내용을 그대로 복사하지 말고, 혼자 있는 노인이 할 수 있도록 **단순하고 실용적으로** 재작성하세요.
   - 문서에 없는 내용은 위 가이드를 참고하되, 상황에 맞게 구체화하세요.

3. **구체성과 실용성 강조**:
   - 추상적인 표현("가능하면", "시도하세요")보다 구체적인 행동("문 손잡이를 위로, 아래로, 좌우로 돌려보세요")을 제시하세요.
   - 각 단계마다 **실제로 할 수 있는 구체적 행동**을 2-3개 제시하세요.
   - 예: "문 열기" ❌ → "문 손잡이를 여러 방향으로 돌려보고, 문 틈새를 확인한 뒤 카드로 문고리를 밀어보세요" ✅

4. **긴급도 우선순위**: emergency_level이 "high"인 경우, 1단계 첫 문장은 무조건 "지금 바로 119에 전화하세요."로 시작

5. **문장 구조**: 
   - 한 단계에 문장 2개 이하
   - 각 문장은 짧게, 한 행동만 담기
   - 한 bullet = 한 행동

6. **전문 용어 최소화**: 
   - "쇼크 증상" 같은 전문 용어 대신 "얼굴이 창백해지고 식은땀이 나거나, 정신이 멍해지면" 같은 일상적 표현 사용
   - 괄호, 인용, 복잡한 설명 제거

7. **문서 번호/페이지 제거**: 
   - "문서 1", "페이지 40", "(문서 1 참고)" 같은 표현 절대 사용 금지
   - 검색된 문서의 내용은 활용하되, 출처는 언급하지 마세요

8. **상황별 맞춤**: 
   - 상황 ID({situation_id})와 증상({symptoms})에 맞는 구체적 지침
   - 재난 유형({disaster_medium})에 특화된 방법 제시
   - 사운드 이벤트({sound_event}) 반영
   - 추가 상황 정보({additional_context})를 반드시 고려하세요

9. **혼자서 가능한 방법만**: 다른 사람의 도움이 필요한 방법은 절대 포함하지 마세요

응답 형식 (템플릿):

[상황 요약 한 줄]
예: "지금은 불이 난 것으로 보이고, 연기 때문에 숨이 막힐 수 있는 위험한 상황입니다."

**1단계: 지금 당장 해야 할 일 (가장 중요한 한 줄)**
- emergency_level이 "high"면: "지금 바로 119에 전화하세요."
- emergency_level이 "medium/low"면: 구체적 응급처치 행동

**2단계: 119 연결을 기다리면서 할 일**
- 자세, 옷, 주변 환경, 대피 방향 등
- 한 bullet = 한 행동, 각 bullet은 1~2문장

**3단계: 119에 이렇게 말하세요**
- 신고 멘트 템플릿 (혼자 있는 상황 명시)

(선택) **4단계: 통화가 끝난 뒤 구조를 기다리는 동안 할 일**
- 움직이지 않기, 문 열어두기 등

예시 (S2: 낙상 + 심정지, high):
지금은 쓰러진 상태에서 숨쉬기가 어려운 위험한 상황입니다.

**1단계: 지금 당장 해야 할 일**
- 지금 바로 119에 전화하세요. 전화를 걸 수 있으면 무조건 먼저 119를 누르세요.

**2단계: 119 연결을 기다리면서 할 일**
- 무리해서 일어나지 말고, 가능한 한 편안한 자세를 유지하세요.
- 전화기가 손 닿는 거리에 없으면, 천천히 기어서 가까운 전화기를 향해 움직이세요.

**3단계: 119에 이렇게 말하세요**
- "혼자 있는데 쓰러져서 숨쉬기가 어렵습니다. 심정지 가능성이 있습니다. 주소는 [주소]입니다."

**4단계: 통화가 끝난 뒤**
- 가능하면 문을 열어두세요.
- 움직이지 말고 구조대를 기다리세요.

예시 (S4: 화재, high):
지금은 불이 난 것으로 보이고, 연기 때문에 숨이 막힐 수 있는 위험한 상황입니다.

**1단계: 지금 당장 해야 할 일**
- 지금 바로 119에 전화하세요.

**2단계: 119 연결을 기다리면서 할 일**
- 연기가 있다면 낮은 자세로 기어가세요.
- 가능하면 젖은 수건으로 코와 입을 막으세요.
- 문 손잡이를 만져보고 뜨겁지 않으면 문을 열어 대피로를 확보하세요.

**3단계: 119에 이렇게 말하세요**
- "화재가 발생했습니다. 혼자 있습니다. 주소는 [주소]입니다."

예시 (S1: 흉통, medium):
지금은 가슴이 아프고 숨쉬기가 조금 힘든 상황입니다.

**1단계: 지금 당장 해야 할 일**
- 가슴이 아프고 숨쉬기 힘들면, 기대서 앉는 자세를 취하세요.
- 옷이 답답하면 윗단추와 허리 쪽을 풀어 주세요.

**2단계: 증상이 악화되면**
- 증상이 점점 심해지거나 5분 이상 줄어들지 않으면 119에 전화하세요.
- 얼굴이 창백해지고 식은땀이 나거나, 정신이 멍해지면 바로 119에 전화하세요.

**3단계: 119에 이렇게 말하세요**
- "혼자 있는데 가슴이 너무 아프고 숨쉬기가 조금 힘듭니다. 주소는 [주소]입니다."

예시 (S5: 갇힘, medium/high):
지금은 문이나 공간에 갇혀서 나갈 수 없는 상황입니다.

**1단계: 지금 당장 해야 할 일**
- emergency_level이 "high"면: "지금 바로 119에 전화하세요."
- emergency_level이 "medium"이면: 먼저 문이나 창문을 열어보세요.
  * 문 손잡이를 여러 방향으로 돌려보세요 (위로, 아래로, 좌우로).
  * 문 아래쪽 틈새를 확인하고, 가능하면 얇은 카드나 열쇠로 문고리를 밀어보세요.
  * 문이 밀리는지 당기는지 확인해보세요 (일부 문은 밀어야 열립니다).

**2단계: 119 연결을 기다리면서 할 일**
- 창문이 있다면 창문 잠금 장치를 확인하고 열어보세요.
- 창문이 열리지 않으면 주변에 큰 소리로 도움을 요청하세요.
- 가능하면 문 근처나 창문 근처로 이동하세요 (구조대가 찾기 쉽도록).
- 벽을 두드리거나 큰 소리로 도움을 요청하세요.

**3단계: 119에 이렇게 말하세요**
- "혼자 있는데 [방/엘리베이터/지하실 등 구체적 위치]에 갇혔습니다. 문이 열리지 않습니다. 주소는 [주소]입니다."

**4단계: 통화가 끝난 뒤**
- 구조대가 도착할 때까지 문 근처에서 대기하세요.
- 가능하면 문을 두드려서 위치를 알려주세요.
- 공기가 답답하면 창문 틈새나 문 틈새로 공기 순환을 확인하세요.

""")
        ])
    
    def generate_guideline(
        self,
        situation_info: Dict,
        additional_context: str = "",
        use_context_aware_search: bool = False,
        chat_history: Optional[List] = None
    ) -> Dict:
        """
        상황 정보를 바탕으로 응급 지침 생성
        
        Args:
            situation_info: STT 구조화 결과 등 상황 정보 딕셔너리
                예: {
                    "disasterLarge": "구급",
                    "disasterMedium": "낙상",
                    "urgencyLevel": "긴급",
                    "sentiment": "불안",
                    "triage": "적색"
                }
            additional_context: 추가 상황 설명
            use_context_aware_search: 대화 맥락을 고려한 검색 사용 여부 (현재는 미사용)
            chat_history: 대화 히스토리 (현재는 미사용)
        
        Returns:
            {
                "guideline": "생성된 지침",
                "report_message": "신고 메시지",
                "sources": [검색된 문서 출처들],
                "steps": ["1단계", "2단계"]
            }
        """
        # 상황 정보 추출
        situation_id = situation_info.get("situation_id", "S0")
        emergency_level = situation_info.get("emergency_level", "low")
        disaster_type = situation_info.get("disasterMedium", situation_info.get("disasterLarge", "알 수 없음"))
        urgency_level = situation_info.get("urgencyLevel", "보통")
        sentiment = situation_info.get("sentiment", "중립")
        triage = situation_info.get("triage", "보통")
        symptoms = situation_info.get("symptoms", [])
        sound_event = situation_info.get("sound_event", "")
        
        # 검색 쿼리 생성 (situation_id와 symptoms를 활용한 구체적 키워드)
        search_query_parts = []
        
        # situation_id에 따른 핵심 키워드 추가 (더 구체적이고 다양한 키워드)
        situation_keywords = {
            "S2": ["낙상", "심정지", "호흡곤란", "호흡정지", "의식소실", "응급처치", "생명위협", "심폐소생술", "기도확보"],
            "S3": ["낙상", "골절", "부상", "외상", "골절응급처치", "출혈", "응급처치", "고정", "부목"],
            "S4": ["화재", "대피", "연기", "화상", "화재대피", "연기흡입", "응급처치", "소화", "대피로"],
            "S5": ["갇힘", "고립", "구조", "문열기", "탈출", "갇힘구조", "문고리", "창문열기", "구조요청", "응급구조", "갇힘상황", "문잠김", "방문열기", "탈출방법"],
            "S1": ["의료응급", disaster_type, "응급처치", "응급의료", "증상관찰"],
            "S6": ["의료응급", "심정지", "호흡곤란", "호흡곤란응급처치", "응급처치", "생명위협", "기도확보"],
            "S7": ["응급상황", disaster_type, "응급처치", "응급대처"],
            "S0": ["응급상황", "관찰", "대처", "증상관찰"]
        }
        search_query_parts.extend(situation_keywords.get(situation_id, [disaster_type]))
        
        # symptoms를 한국어로 변환하여 검색 키워드에 추가 (더 구체적인 키워드)
        symptom_keywords = {
            "fall": "낙상",
            "possible_cardiac_arrest": "심정지",
            "breathing_difficulty": "호흡곤란",
            "not_breathing": "호흡정지",
            "possible_fracture": "골절",
            "fire_suspected": "화재",
            "trapped_or_confined": "갇힘",
            "chest_pain": "흉통",
            "high_urgency": "고위험",
            "unclear_condition": "상황불명확"
        }
        
        # symptom에 따른 추가 관련 키워드 (더 풍부한 검색을 위해)
        symptom_related_keywords = {
            "trapped_or_confined": ["문열기", "탈출방법", "구조요청", "갇힘구조", "문고리", "창문열기", "문잠김", "방문열기", "엘리베이터고장", "지하실탈출"],
            "fall": ["낙상응급처치", "골절", "부상처치", "낙상대처"],
            "possible_cardiac_arrest": ["심정지응급처치", "심폐소생술", "기도확보", "심정지대처"],
            "breathing_difficulty": ["호흡곤란응급처치", "기도확보", "호흡보조", "호흡곤란대처"],
            "fire_suspected": ["화재대피", "연기흡입", "대피로", "화재대처"]
        }
        if symptoms and isinstance(symptoms, list):
            for symptom in symptoms:
                if symptom in symptom_keywords:
                    search_query_parts.append(symptom_keywords[symptom])
                # 관련 키워드도 추가 (더 풍부한 검색)
                if symptom in symptom_related_keywords:
                    search_query_parts.extend(symptom_related_keywords[symptom])
        
        # sound_event 추가
        if sound_event and sound_event != "없음" and sound_event not in search_query_parts:
            search_query_parts.append(sound_event)
        
        # disaster_type 추가 (중복 제거)
        if disaster_type and disaster_type != "알 수 없음" and disaster_type not in search_query_parts:
            search_query_parts.append(disaster_type)
        
        # 추가 컨텍스트에서 핵심 키워드 추출 (더 구체적으로)
        if additional_context:
            context_keywords = []
            if "숨" in additional_context or "호흡" in additional_context:
                context_keywords.extend(["호흡", "기도", "호흡곤란", "호흡응급처치"])
            if "쓰러" in additional_context or "낙상" in additional_context:
                context_keywords.extend(["낙상", "골절", "낙상응급처치", "부상처치"])
            if "화재" in additional_context or "불" in additional_context or "연기" in additional_context:
                context_keywords.extend(["화재", "대피", "화재대피", "연기흡입"])
            if "갇혔" in additional_context or "갇힘" in additional_context or "문" in additional_context or "열" in additional_context:
                context_keywords.extend(["갇힘", "구조", "갇힘구조", "문열기", "탈출", "구조요청", "문고리", "창문열기"])
            if "엘리베이터" in additional_context:
                context_keywords.extend(["엘리베이터", "엘리베이터고장", "엘리베이터구조"])
            if "지하실" in additional_context or "지하" in additional_context:
                context_keywords.extend(["지하실", "지하구조", "지하탈출"])
            
            for keyword in context_keywords:
                if keyword not in search_query_parts:
                    search_query_parts.append(keyword)
        
        # 공통 키워드 추가
        search_query_parts.extend([
            "응급처치",
            "고령층",
            "혼자",
            urgency_level if urgency_level else ""
        ])
        
        # 중복 제거 및 빈 문자열 제거
        search_query_parts = list(dict.fromkeys([p for p in search_query_parts if p]))
        
        search_query = " ".join(search_query_parts)
        
        # 검색 쿼리 로깅 (디버깅용)
        logger.info(f"검색 쿼리: {search_query}")
        
        # 문서 검색
        retrieved_docs = self.retriever.invoke(search_query)
        logger.info(f"검색된 문서 수: {len(retrieved_docs)}")
        
        # 검색된 문서들을 컨텍스트로 변환 (더 구조화된 형식)
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            content = doc.page_content.strip()
            
            # 문서 내용에서 문서 번호/페이지 참조 제거
            # "(문서 1)", "(페이지 40)", "[문서 1 참고]" 같은 패턴 제거
            import re
            content = re.sub(r'\(문서\s*\d+[^)]*\)', '', content)
            content = re.sub(r'\(페이지\s*\d+[^)]*\)', '', content)
            content = re.sub(r'\[문서\s*\d+[^\]]*\]', '', content)
            content = re.sub(r'문서\s*\d+', '', content)
            content = re.sub(r'페이지\s*\d+', '', content)
            content = re.sub(r'\s+', ' ', content).strip()  # 연속된 공백 제거
            
            # 문서 내용이 너무 길면 요약
            if len(content) > 500:
                content = content[:500] + "..."
            
            # 문서 번호/페이지 없이 내용만 추가
            context_parts.append(content)
        
        context = "\n\n---\n\n".join(context_parts)
        
        # 출처 정보 저장
        sources = [
            {
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", None)
            }
            for doc in retrieved_docs
        ]
        
        # situation JSON 정보 추출 (프롬프트에 포함)
        # situation_info에서 직접 추출 (rag_client.py에서 추가한 정보)
        situation_id = situation_info.get("situation_id", "S0")
        emergency_level = situation_info.get("emergency_level", "low")
        disaster_large = situation_info.get("disasterLarge", "알 수 없음")
        disaster_medium = disaster_type
        symptoms = situation_info.get("symptoms", [])
        sound_event = situation_info.get("sound_event", "없음")
        sound_confidence = situation_info.get("sound_confidence", "없음")
        
        # symptoms를 문자열로 변환
        if symptoms and isinstance(symptoms, list):
            symptom_map = {
                "fall": "낙상",
                "possible_cardiac_arrest": "심정지 가능성",
                "breathing_difficulty": "호흡곤란",
                "possible_fracture": "골절 가능성",
                "fire_suspected": "화재 의심",
                "trapped_or_confined": "갇힘",
                "high_urgency": "고위험",
                "caller_anxious": "신고자 불안",
                "unclear_condition": "상황 불명확",
                "not_breathing": "호흡 정지",
                "chest_pain": "흉통"
            }
            korean_symptoms = [symptom_map.get(s, s) for s in symptoms]
            symptoms_str = ", ".join(korean_symptoms) if korean_symptoms else "없음"
        else:
            symptoms_str = "없음"
        
        # sound_confidence를 문자열로 변환
        if isinstance(sound_confidence, (int, float)):
            sound_confidence_str = f"{sound_confidence:.2f}"
        else:
            sound_confidence_str = str(sound_confidence) if sound_confidence else "없음"
        
        # 지침 생성 (situation JSON 정보 모두 포함)
        prompt = self.guideline_prompt.format_messages(
            situation_id=situation_id,
            emergency_level=emergency_level,
            disaster_large=disaster_large,
            disaster_medium=disaster_medium,
            urgency_level=urgency_level,
            sentiment=sentiment,
            symptoms=symptoms_str,
            sound_event=sound_event,
            sound_confidence=sound_confidence_str,
            additional_context=additional_context or "없음",
            context=context if context.strip() else "관련 전문 문서를 찾지 못했습니다. 일반 응급처치 지침을 제공합니다."
        )
        
        response = self.llm.invoke(prompt)
        guideline_text = response.content
        
        # 지침 파싱 (단계별로 분리)
        steps = self._parse_guideline_steps(guideline_text)
        report_message = self._extract_report_message(guideline_text)
        
        return {
            "guideline": guideline_text,
            "report_message": report_message,
            "sources": sources,
            "steps": steps,
            "disaster_type": disaster_type,
            "urgency_level": urgency_level
        }
    
    def _parse_guideline_steps(self, guideline_text: str) -> List[str]:
        """생성된 지침에서 단계별로 파싱"""
        steps = []
        lines = guideline_text.split("\n")
        
        for line in lines:
            line = line.strip()
            if line and ("단계" in line or "1." in line or "2." in line):
                # "1단계:", "1.", "첫 번째" 등 패턴 추출
                if "단계:" in line:
                    steps.append(line.split("단계:", 1)[1].strip())
                elif line[0].isdigit() and "." in line:
                    steps.append(line.split(".", 1)[1].strip())
                elif line.startswith("-"):
                    steps.append(line[1:].strip())
        
        return steps if steps else [guideline_text]
    
    def _extract_report_message(self, guideline_text: str) -> str:
        """신고 메시지 추출"""
        lines = guideline_text.split("\n")
        for line in lines:
            if "신고 메시지" in line or "신고 시" in line:
                # "신고 메시지:" 이후 내용 추출
                if ":" in line:
                    return line.split(":", 1)[1].strip()
                return line
        return "응급 상황입니다. 즉시 도움이 필요합니다."


if __name__ == "__main__":
    # 테스트
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 벡터 스토어 로딩 (이미 생성되어 있다고 가정)
    embedding_store = EmbeddingStore()
    try:
        vectorstore = embedding_store.load_vectorstore()
    except FileNotFoundError:
        print("벡터 스토어가 없습니다. 먼저 벡터 스토어를 생성하세요.")
        exit(1)
    
    # 지침 생성기 초기화
    generator = GuidelineGenerator(embedding_store)
    
    # 테스트 상황
    situation_info = {
        "disasterLarge": "구급",
        "disasterMedium": "낙상",
        "urgencyLevel": "긴급",
        "sentiment": "불안",
        "triage": "적색"
    }
    
    result = generator.generate_guideline(
        situation_info,
        additional_context="쓰러진 상태에서 숨을 못 쉬고 있음"
    )
    
    print("\n=== 생성된 응급 지침 ===")
    print(f"\n재난 유형: {result['disaster_type']}")
    print(f"심각도: {result['urgency_level']}")
    print(f"\n지침:\n{result['guideline']}")
    print(f"\n신고 메시지: {result['report_message']}")
    print(f"\n출처: {len(result['sources'])}개")
