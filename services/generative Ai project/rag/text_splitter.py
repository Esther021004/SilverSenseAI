"""
텍스트 분할 모듈
문서를 의미 있는 청크로 나누는 기능 제공
"""
from typing import List
from langchain_core.documents import Document
try:
    # 최신 버전 (langchain-text-splitters 패키지)
    from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
except ImportError:
    # 구버전 호환
    from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KoreanTextSplitter:
    """한국어 문서에 특화된 텍스트 분할기"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        """
        Args:
            chunk_size: 각 청크의 최대 문자 수
            chunk_overlap: 청크 간 겹치는 문자 수
            separators: 텍스트 분할에 사용할 구분자 리스트
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 한국어 문서에 적합한 구분자 순서
        if separators is None:
            separators = [
                "\n\n",      # 문단 구분
                "\n",        # 줄바꿈
                ". ",        # 문장 구분
                "。",        # 일본식 문장 구분
                " ",         # 공백
                ""           # 문자 단위
            ]
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """문서 리스트를 청크로 분할"""
        split_docs = self.text_splitter.split_documents(documents)
        logger.info(f"문서 분할 완료: {len(documents)}개 → {len(split_docs)}개 청크")
        return split_docs
    
    def split_text(self, text: str) -> List[str]:
        """텍스트를 청크로 분할"""
        return self.text_splitter.split_text(text)


if __name__ == "__main__":
    # 테스트
    test_doc = Document(
        page_content="""
        응급처치 지침
        
        낙상 사고 발생 시:
        1. 환자를 움직이지 마세요
        2. 의식 상태를 확인하세요
        3. 119에 신고하세요
        
        화재 발생 시:
        1. 즉시 대피하세요
        2. 연기가 있다면 낮은 자세로 이동하세요
        3. 화재 경보기를 작동시키세요
        """,
        metadata={"source": "test.pdf", "page": 1}
    )
    
    splitter = KoreanTextSplitter(chunk_size=100, chunk_overlap=20)
    split_docs = splitter.split_documents([test_doc])
    
    print(f"분할된 청크 수: {len(split_docs)}")
    for i, doc in enumerate(split_docs):
        print(f"\n청크 {i+1}:")
        print(doc.page_content[:100] + "...")

