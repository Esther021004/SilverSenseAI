"""
벡터 스토어 구축 스크립트
문서를 로딩하고 벡터 DB를 생성하는 스크립트
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# RAG 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from rag.document_loader import DocumentLoader
from rag.text_splitter import KoreanTextSplitter
from rag.embedding_store import EmbeddingStore

def main():
    """벡터 스토어 구축"""
    load_dotenv()
    
    print("="*60)
    print("벡터 스토어 구축 시작")
    print("="*60)
    
    # 1. 문서 로딩
    print("\n[1/3] 문서 로딩 중...")
    loader = DocumentLoader(document_dir="document")
    documents = loader.load_all_documents()
    
    if not documents:
        print("❌ 로딩된 문서가 없습니다. document 디렉토리를 확인하세요.")
        return
    
    print(f"✅ {len(documents)}개 문서 페이지 로딩 완료")
    
    # 2. 텍스트 분할
    print("\n[2/3] 텍스트 분할 중...")
    splitter = KoreanTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    split_documents = splitter.split_documents(documents)
    print(f"✅ {len(split_documents)}개 청크로 분할 완료")
    
    # 3. 벡터 스토어 생성
    print("\n[3/3] 벡터 스토어 생성 중...")
    print("(임베딩 모델 다운로드가 필요할 수 있습니다. 시간이 걸릴 수 있습니다.)")
    
    embedding_store = EmbeddingStore(
        persist_directory="./chroma_db"
    )
    vectorstore = embedding_store.create_vectorstore(split_documents)
    
    print(f"✅ 벡터 스토어 생성 완료: ./chroma_db")
    
    # 검색 테스트
    print("\n" + "="*60)
    print("검색 테스트")
    print("="*60)
    
    test_queries = [
        "낙상 사고 응급처치",
        "화재 발생 시 대응",
        "호흡곤란 증상"
    ]
    
    for query in test_queries:
        print(f"\n검색 쿼리: {query}")
        results = embedding_store.similarity_search(query, k=2)
        print(f"검색 결과: {len(results)}개")
        for i, doc in enumerate(results, 1):
            print(f"  {i}. {Path(doc.metadata['source']).name} (페이지 {doc.metadata.get('page', '?')})")
            print(f"     {doc.page_content[:100]}...")
    
    print("\n" + "="*60)
    print("벡터 스토어 구축 완료!")
    print("="*60)

if __name__ == "__main__":
    main()

