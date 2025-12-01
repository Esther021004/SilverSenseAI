"""
임베딩 및 벡터 스토어 모듈
문서를 임베딩하고 벡터 DB에 저장하여 검색 가능하게 만듦
"""
import os
from pathlib import Path
from typing import List, Optional
import logging

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingStore:
    """임베딩 및 벡터 스토어 관리 클래스"""
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers",
        model_name: str = "jhgan/ko-sroberta-multitask",
        persist_directory: str = "./chroma_db",
        use_openai: bool = False,
        openai_api_key: Optional[str] = None
    ):
        """
        Args:
            embedding_model: 사용할 임베딩 모델 타입
            model_name: HuggingFace 모델 이름 (한국어 최적화)
            persist_directory: 벡터 DB 저장 경로
            use_openai: OpenAI 임베딩 사용 여부
            openai_api_key: OpenAI API 키 (use_openai=True일 때 필요)
        """
        self.persist_directory = persist_directory
        self.use_openai = use_openai
        
        # 임베딩 모델 초기화
        if use_openai:
            if not openai_api_key:
                openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OpenAI API 키가 필요합니다. 환경변수 OPENAI_API_KEY를 설정하거나 파라미터로 제공하세요.")
            self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
            logger.info("OpenAI 임베딩 모델 사용")
        else:
            # 한국어 특화 임베딩 모델
            # jhgan/ko-sroberta-multitask: 한국어 문장 임베딩에 특화
            # 다른 옵션: "jhgan/ko-sbert-multitask", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'},  # GPU 사용 시 'cuda'로 변경
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info(f"로컬 임베딩 모델 사용: {model_name}")
        
        self.vectorstore = None
    
    def create_vectorstore(
        self,
        documents: List[Document],
        collection_name: str = "emergency_guidelines"
    ) -> Chroma:
        """문서로부터 벡터 스토어 생성"""
        logger.info(f"벡터 스토어 생성 중... (문서 수: {len(documents)})")
        
        # Chroma 벡터 스토어 생성
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name=collection_name
        )
        
        logger.info(f"벡터 스토어 생성 완료: {self.persist_directory}")
        return self.vectorstore
    
    def load_vectorstore(self, collection_name: str = "emergency_guidelines") -> Chroma:
        """저장된 벡터 스토어 로딩"""
        if not Path(self.persist_directory).exists():
            raise FileNotFoundError(f"벡터 스토어가 없습니다: {self.persist_directory}")
        
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name=collection_name
        )
        
        logger.info(f"벡터 스토어 로딩 완료: {self.persist_directory}")
        return self.vectorstore
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """기존 벡터 스토어에 문서 추가"""
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다. 먼저 create_vectorstore() 또는 load_vectorstore()를 호출하세요.")
        
        ids = self.vectorstore.add_documents(documents)
        logger.info(f"문서 추가 완료: {len(ids)}개")
        return ids
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None
    ) -> List[Document]:
        """유사도 기반 문서 검색"""
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다.")
        
        return self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter
        )
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None
    ) -> List[tuple]:
        """유사도 점수와 함께 문서 검색"""
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다.")
        
        return self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter
        )
    
    def get_retriever(self, k: int = 4, search_type: str = "similarity"):
        """LangChain Retriever 객체 반환"""
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다.")
        
        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )


if __name__ == "__main__":
    # 테스트
    from document_loader import DocumentLoader
    from text_splitter import KoreanTextSplitter
    
    # 문서 로딩
    loader = DocumentLoader()
    documents = loader.load_all_documents()
    
    # 텍스트 분할
    splitter = KoreanTextSplitter(chunk_size=500, chunk_overlap=100)
    split_docs = splitter.split_documents(documents)
    
    # 임베딩 및 벡터 스토어 생성
    embedding_store = EmbeddingStore()
    vectorstore = embedding_store.create_vectorstore(split_docs)
    
    # 검색 테스트
    query = "낙상 사고 발생 시 응급처치 방법"
    results = embedding_store.similarity_search(query, k=3)
    
    print(f"\n검색 쿼리: {query}")
    print(f"\n검색 결과: {len(results)}개")
    for i, doc in enumerate(results, 1):
        print(f"\n--- 결과 {i} ---")
        print(f"출처: {doc.metadata.get('source', 'Unknown')}")
        print(f"페이지: {doc.metadata.get('page', 'Unknown')}")
        print(f"내용: {doc.page_content[:200]}...")

