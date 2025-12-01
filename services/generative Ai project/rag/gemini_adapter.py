"""
Google Gemini를 LangChain과 호환되도록 래핑하는 어댑터
google-generativeai를 직접 사용
"""
import os
from typing import List, Optional, Any
import logging

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatGoogleGenerativeAI(BaseChatModel):
    """Google Gemini를 LangChain과 호환되도록 래핑"""
    
    model_name: str
    temperature: float
    google_api_key: Optional[str] = None
    _client: Any = None  # 내부 사용
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.3,
        google_api_key: Optional[str] = None
    ):
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai 패키지가 설치되지 않았습니다. "
                "pip install google-generativeai 로 설치하세요."
            )
        
        # API 키 설정
        if not google_api_key:
            google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY 또는 GEMINI_API_KEY 환경변수가 필요합니다.\n"
                "또는 google_api_key 파라미터로 제공하세요."
            )
        
        # Gemini 클라이언트 먼저 초기화 (API 키 설정)
        genai.configure(api_key=google_api_key)
        
        # Pydantic 모델 초기화 (필수 필드 전달)
        # BaseChatModel은 Pydantic이므로 키워드 인자로 전달
        super().__init__(
            model_name=model,
            temperature=temperature,
            google_api_key=google_api_key
        )
        
        # Gemini 모델 클라이언트 생성
        try:
            self._client = genai.GenerativeModel(model)
            logger.info(f"Gemini 모델 초기화: {model} (temperature={temperature})")
        except Exception as e:
            logger.error(f"Gemini 모델 '{model}' 초기화 실패: {e}")
            logger.info("사용 가능한 모델 확인 중...")
            # 사용 가능한 모델 목록 출력
            try:
                models = genai.list_models()
                available = [m.name.split('/')[-1] for m in models if 'generateContent' in m.supported_generation_methods]
                logger.info(f"사용 가능한 모델: {available}")
                logger.info("기본 모델 'gemini-2.0-flash'로 변경 시도...")
                # 사용 가능한 최신 모델 시도
                fallback_models = ["gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-pro"]
                for fallback_model in fallback_models:
                    try:
                        self._client = genai.GenerativeModel(fallback_model)
                        self.model_name = fallback_model
                        logger.info(f"✅ 모델 '{fallback_model}'로 성공적으로 변경됨")
                        break
                    except Exception:
                        continue
                else:
                    raise ValueError(f"사용 가능한 Gemini 모델을 찾을 수 없습니다.")
            except Exception as e2:
                raise ValueError(
                    f"Gemini 모델을 초기화할 수 없습니다: {e}\n"
                    f"사용 가능한 모델명을 확인하세요: python check_gemini_models.py"
                )
    
    @property
    def _llm_type(self) -> str:
        return "google_generative_ai"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> ChatResult:
        """메시지 생성"""
        # LangChain 메시지를 Gemini 형식으로 변환
        prompt_parts = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                prompt_parts.append(f"시스템: {msg.content}")
            elif isinstance(msg, HumanMessage):
                prompt_parts.append(msg.content)
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"어시스턴트: {msg.content}")
            else:
                prompt_parts.append(str(msg.content))
        
        full_prompt = "\n".join(prompt_parts)
        
        # Gemini 호출
        generation_config = genai.types.GenerationConfig(
            temperature=self.temperature
        )
        if stop:
            generation_config.stop_sequences = stop
        
        try:
            response = self._client.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            # 응답 텍스트 추출
            if hasattr(response, 'text') and response.text:
                text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                text = response.candidates[0].content.parts[0].text
            else:
                raise ValueError("Gemini API에서 응답을 받을 수 없습니다.")
        except Exception as e:
            logger.error(f"Gemini API 호출 오류: {e}")
            raise
        
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=text))]
        )
    
    def invoke(self, input, **kwargs):
        """단순 호출 인터페이스"""
        # ChatPromptTemplate의 format_messages 결과를 처리
        if isinstance(input, list):
            messages = input
        elif isinstance(input, BaseMessage):
            messages = [input]
        else:
            # 문자열인 경우
            messages = [HumanMessage(content=str(input))]
        
        result = self._generate(messages, **kwargs)
        return result.generations[0].message
    
    async def _agenerate(self, messages, **kwargs):
        """비동기 생성 (선택적)"""
        return self._generate(messages, **kwargs)

