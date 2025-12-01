"""
RAG 시스템 통합 모듈
모든 구성 요소를 통합하여 사용하기 쉽게 만든 메인 클래스
"""
import os
from pathlib import Path
from typing import Dict, Optional, List
import logging

from .document_loader import DocumentLoader
from .text_splitter import KoreanTextSplitter
from .embedding_store import EmbeddingStore
from .guideline_generator import GuidelineGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGSystem:
    """통합 RAG 시스템 클래스"""
    
    def __init__(
        self,
        document_dir: str = "document",
        persist_directory: str = "./chroma_db",
        embedding_model_name: str = "jhgan/ko-sroberta-multitask",
        llm_model: str = "gemini-2.0-flash",  # 기본값을 Gemini로 변경 (무료, 최신)
        use_openai_embedding: bool = False,
        api_key: Optional[str] = None,
        rebuild_vectorstore: bool = False
    ):
        """
        RAG 시스템 초기화
        
        Args:
            document_dir: 문서가 있는 디렉토리
            persist_directory: 벡터 DB 저장 경로
            embedding_model_name: 임베딩 모델명
            llm_model: LLM 모델명
                - OpenAI: "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"
                - Gemini: "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-pro" (무료)
            use_openai_embedding: OpenAI 임베딩 사용 여부
            api_key: API 키 (OpenAI 또는 Google API 키 - 모델에 따라 자동 선택)
            rebuild_vectorstore: 벡터 스토어 재구축 여부
        """
        self.document_dir = document_dir
        self.persist_directory = persist_directory
        
        # 모델 타입 감지
        is_gemini = llm_model.lower().startswith("gemini")
        
        # API 키 설정
        if not api_key:
            if is_gemini:
                api_key = os.getenv("GOOGLE_API_KEY")
            else:
                api_key = os.getenv("OPENAI_API_KEY")
        
        # 문서 로더 초기화
        self.document_loader = DocumentLoader(document_dir=document_dir)
        
        # 텍스트 분할기 초기화
        self.text_splitter = KoreanTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # 임베딩 스토어 초기화
        # OpenAI 임베딩을 사용하는 경우에만 API 키 필요
        embedding_api_key = None
        if use_openai_embedding:
            if not api_key and not is_gemini:
                embedding_api_key = os.getenv("OPENAI_API_KEY")
            elif not is_gemini:
                embedding_api_key = api_key
        
        self.embedding_store = EmbeddingStore(
            model_name=embedding_model_name,
            persist_directory=persist_directory,
            use_openai=use_openai_embedding,
            openai_api_key=embedding_api_key
        )
        
        # 벡터 스토어 로딩 또는 생성
        if rebuild_vectorstore or not Path(persist_directory).exists():
            logger.info("벡터 스토어 생성 중...")
            self._build_vectorstore()
        else:
            logger.info("기존 벡터 스토어 로딩 중...")
            try:
                self.embedding_store.load_vectorstore()
            except FileNotFoundError:
                logger.warning("벡터 스토어를 찾을 수 없습니다. 새로 생성합니다.")
                self._build_vectorstore()
        
        # 지침 생성기 초기화
        self.guideline_generator = GuidelineGenerator(
            embedding_store=self.embedding_store,
            llm_model=llm_model,
            api_key=api_key
        )
        
        logger.info("RAG 시스템 초기화 완료")
    
    def _build_vectorstore(self):
        """벡터 스토어 구축"""
        # 문서 로딩
        logger.info("문서 로딩 중...")
        documents = self.document_loader.load_all_documents()
        
        if not documents:
            raise ValueError("로딩된 문서가 없습니다. document 디렉토리를 확인하세요.")
        
        # 텍스트 분할
        logger.info("텍스트 분할 중...")
        split_documents = self.text_splitter.split_documents(documents)
        
        # 벡터 스토어 생성
        logger.info("벡터 스토어 생성 중...")
        self.embedding_store.create_vectorstore(split_documents)
    
    def generate_guideline(
        self,
        situation_info: Dict,
        additional_context: str = "",
        use_context_aware_search: bool = False,
        chat_history: Optional[List] = None
    ) -> Dict:
        """
        응급 지침 생성
        
        Args:
            situation_info: 상황 정보 딕셔너리
                예: {
                    "disasterLarge": "구급",
                    "disasterMedium": "낙상",
                    "urgencyLevel": "긴급",
                    "sentiment": "불안",
                    "triage": "적색"
                }
            additional_context: 추가 상황 설명
            use_context_aware_search: 대화 맥락 고려 검색 사용 여부
            chat_history: 대화 히스토리
        
        Returns:
            생성된 지침 딕셔너리
        """
        return self.guideline_generator.generate_guideline(
            situation_info=situation_info,
            additional_context=additional_context,
            use_context_aware_search=use_context_aware_search,
            chat_history=chat_history
        )
    
    def search_documents(self, query: str, k: int = 4) -> List:
        """문서 검색 (디버깅 및 테스트용)"""
        return self.embedding_store.similarity_search(query, k=k)
    
    def rebuild_vectorstore(self):
        """벡터 스토어 재구축"""
        logger.info("벡터 스토어 재구축 시작...")
        self._build_vectorstore()
        logger.info("벡터 스토어 재구축 완료")


if __name__ == "__main__":
    # 테스트
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # RAG 시스템 초기화
    rag_system = RAGSystem(
        rebuild_vectorstore=True  # 처음 실행 시 True로 설정
    )
    
    # 테스트 상황
    situation_info = {
        "disasterLarge": "구급",
        "disasterMedium": "낙상",
        "urgencyLevel": "긴급",
        "sentiment": "불안",
        "triage": "적색"
    }
    
    # 지침 생성
    result = rag_system.generate_guideline(
        situation_info,
        additional_context="쓰러진 상태에서 숨을 못 쉬고 있음"
    )
    
    print("\n" + "="*50)
    print("생성된 응급 지침")
    print("="*50)
    print(f"\n재난 유형: {result['disaster_type']}")
    print(f"심각도: {result['urgency_level']}")
    print(f"\n지침:\n{result['guideline']}")
    print(f"\n신고 메시지: {result['report_message']}")
    print(f"\n참고 출처: {len(result['sources'])}개")
    for i, source in enumerate(result['sources'], 1):
        print(f"  {i}. {Path(source['source']).name} (페이지 {source.get('page', '?')})")

