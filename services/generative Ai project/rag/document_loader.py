"""
문서 로딩 모듈
PDF, HWP 등 다양한 형식의 문서를 로딩하는 기능 제공
"""
import os
from typing import List, Dict
from pathlib import Path
import logging

# PDF 처리
from pypdf import PdfReader
import pdfplumber

# LangChain 문서 로더
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentLoader:
    """다양한 형식의 문서를 로딩하는 클래스"""
    
    def __init__(self, document_dir: str = "document"):
        self.document_dir = Path(document_dir)
        
    def load_pdf_with_pypdf(self, file_path: Path) -> List[Document]:
        """PyPDF를 사용한 PDF 로딩"""
        try:
            reader = PdfReader(str(file_path))
            documents = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": str(file_path),
                            "page": i + 1,
                            "type": "pdf"
                        }
                    )
                    documents.append(doc)
            logger.info(f"PyPDF로 {file_path.name} 로딩 완료: {len(documents)} 페이지")
            return documents
        except Exception as e:
            logger.error(f"PyPDF 로딩 실패 {file_path.name}: {e}")
            return []
    
    def load_pdf_with_pdfplumber(self, file_path: Path) -> List[Document]:
        """PDFPlumber를 사용한 PDF 로딩 (더 정확한 텍스트 추출)"""
        try:
            documents = []
            with pdfplumber.open(str(file_path)) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text.strip():
                        doc = Document(
                            page_content=text,
                            metadata={
                                "source": str(file_path),
                                "page": i + 1,
                                "type": "pdf"
                            }
                        )
                        documents.append(doc)
            logger.info(f"PDFPlumber로 {file_path.name} 로딩 완료: {len(documents)} 페이지")
            return documents
        except Exception as e:
            logger.error(f"PDFPlumber 로딩 실패 {file_path.name}: {e}")
            return []
    
    def load_pdf_with_langchain(self, file_path: Path) -> List[Document]:
        """LangChain PyPDFLoader 사용"""
        try:
            loader = PyPDFLoader(str(file_path))
            documents = loader.load()
            logger.info(f"LangChain으로 {file_path.name} 로딩 완료: {len(documents)} 페이지")
            return documents
        except Exception as e:
            logger.error(f"LangChain PDF 로딩 실패 {file_path.name}: {e}")
            return []
    
    def load_single_pdf(self, file_path: Path) -> List[Document]:
        """단일 PDF 파일 로딩 (여러 방법 시도)"""
        # 먼저 PDFPlumber 시도 (한국어 처리에 더 나음)
        documents = self.load_pdf_with_pdfplumber(file_path)
        if documents:
            return documents
        
        # 실패 시 LangChain 로더 시도
        documents = self.load_pdf_with_langchain(file_path)
        if documents:
            return documents
        
        # 마지막으로 PyPDF 시도
        documents = self.load_pdf_with_pypdf(file_path)
        return documents
    
    def load_hwp_file(self, file_path: Path) -> List[Document]:
        """HWP 파일 로딩 (기본적인 처리)"""
        try:
            # HWP 파일은 복잡하므로, 기본적으로 텍스트 추출 시도
            # 완전한 HWP 지원을 위해서는 pyhwp 또는 다른 라이브러리 필요
            logger.warning(f"HWP 파일 {file_path.name}은 현재 기본 처리만 지원됩니다.")
            # TODO: HWP 파일 완전 지원을 위한 추가 구현 필요
            return []
        except Exception as e:
            logger.error(f"HWP 로딩 실패 {file_path.name}: {e}")
            return []
    
    def load_all_documents(self) -> List[Document]:
        """document 디렉토리의 모든 문서 로딩"""
        all_documents = []
        
        if not self.document_dir.exists():
            logger.error(f"문서 디렉토리가 없습니다: {self.document_dir}")
            return all_documents
        
        # PDF 파일 찾기
        pdf_files = list(self.document_dir.glob("*.pdf"))
        logger.info(f"발견된 PDF 파일 수: {len(pdf_files)}")
        
        # HWP 파일 찾기
        hwp_files = list(self.document_dir.glob("*.hwp"))
        logger.info(f"발견된 HWP 파일 수: {len(hwp_files)}")
        
        # PDF 파일 로딩
        for pdf_file in pdf_files:
            documents = self.load_single_pdf(pdf_file)
            all_documents.extend(documents)
        
        # HWP 파일 로딩
        for hwp_file in hwp_files:
            documents = self.load_hwp_file(hwp_file)
            all_documents.extend(documents)
        
        logger.info(f"총 로딩된 문서 수: {len(all_documents)}")
        return all_documents


if __name__ == "__main__":
    # 테스트
    loader = DocumentLoader()
    documents = loader.load_all_documents()
    print(f"\n로딩 완료: {len(documents)}개 문서 청크")
    if documents:
        print(f"\n첫 번째 문서 샘플:")
        print(f"소스: {documents[0].metadata['source']}")
        print(f"내용 (처음 200자): {documents[0].page_content[:200]}...")

