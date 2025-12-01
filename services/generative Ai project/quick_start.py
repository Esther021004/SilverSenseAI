"""
빠른 시작 스크립트
RAG 시스템을 처음 사용하는 사용자를 위한 간단한 예제
"""
import os
from pathlib import Path

def check_environment():
    """환경 설정 확인"""
    print("="*60)
    print("환경 설정 확인")
    print("="*60)
    
    # .env 파일 확인
    if not Path(".env").exists():
        print("\n⚠️  .env 파일이 없습니다.")
        print("   .env 파일을 생성하고 OPENAI_API_KEY를 설정하세요.")
        print("   예시: OPENAI_API_KEY=sk-...")
        return False
    
    # OpenAI API 키 확인
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY를 추가하세요.")
        return False
    
    print("✅ 환경 설정 완료")
    return True

def check_documents():
    """문서 확인"""
    print("\n" + "="*60)
    print("문서 확인")
    print("="*60)
    
    doc_dir = Path("document")
    if not doc_dir.exists():
        print(f"\n⚠️  {doc_dir} 디렉토리가 없습니다.")
        return False
    
    pdf_files = list(doc_dir.glob("*.pdf"))
    hwp_files = list(doc_dir.glob("*.hwp"))
    
    total_files = len(pdf_files) + len(hwp_files)
    
    if total_files == 0:
        print(f"\n⚠️  {doc_dir} 디렉토리에 문서가 없습니다.")
        return False
    
    print(f"\n✅ 발견된 문서: {total_files}개")
    print(f"   - PDF: {len(pdf_files)}개")
    print(f"   - HWP: {len(hwp_files)}개")
    return True

def check_vectorstore():
    """벡터 스토어 확인"""
    print("\n" + "="*60)
    print("벡터 스토어 확인")
    print("="*60)
    
    vectorstore_dir = Path("./chroma_db")
    if vectorstore_dir.exists():
        print("\n✅ 벡터 스토어가 이미 구축되어 있습니다.")
        return True
    else:
        print("\n⚠️  벡터 스토어가 아직 구축되지 않았습니다.")
        print("   다음 명령어로 벡터 스토어를 구축하세요:")
        print("   python build_vectorstore.py")
        return False

def main():
    """메인 함수"""
    print("\n" + "="*60)
    print("RAG 시스템 빠른 시작 가이드")
    print("="*60)
    
    # 1. 환경 설정 확인
    env_ok = check_environment()
    if not env_ok:
        print("\n❌ 환경 설정을 완료한 후 다시 실행하세요.")
        return
    
    # 2. 문서 확인
    doc_ok = check_documents()
    if not doc_ok:
        print("\n❌ document 디렉토리에 문서를 추가한 후 다시 실행하세요.")
        return
    
    # 3. 벡터 스토어 확인
    vectorstore_ok = check_vectorstore()
    
    print("\n" + "="*60)
    print("다음 단계")
    print("="*60)
    
    if not vectorstore_ok:
        print("\n1️⃣  벡터 스토어 구축:")
        print("   python build_vectorstore.py")
        print("\n2️⃣  예제 실행:")
        print("   python example_usage.py")
    else:
        print("\n✅ 모든 설정이 완료되었습니다!")
        print("\n다음 명령어로 예제를 실행하세요:")
        print("   python example_usage.py")
        
        # 간단한 테스트 실행 여부 확인
        response = input("\n지금 바로 간단한 테스트를 실행하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            run_simple_test()

def run_simple_test():
    """간단한 테스트 실행"""
    print("\n" + "="*60)
    print("간단한 테스트 실행")
    print("="*60)
    
    try:
        from rag.rag_system import RAGSystem
        
        print("\n[시스템 초기화 중...]")
        rag_system = RAGSystem(
            document_dir="document",
            persist_directory="./chroma_db",
            rebuild_vectorstore=False
        )
        print("✅ 초기화 완료")
        
        # 테스트 상황
        situation_info = {
            "disasterLarge": "구급",
            "disasterMedium": "낙상",
            "urgencyLevel": "긴급",
            "sentiment": "불안",
            "triage": "적색"
        }
        
        print("\n[응급 지침 생성 중...]")
        result = rag_system.generate_guideline(
            situation_info,
            additional_context="쓰러진 상태"
        )
        
        print("\n" + "="*60)
        print("생성된 응급 지침")
        print("="*60)
        print(f"\n재난 유형: {result['disaster_type']}")
        print(f"심각도: {result['urgency_level']}")
        print(f"\n지침:\n{result['guideline']}")
        print(f"\n신고 메시지: {result['report_message']}")
        
        print("\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n자세한 오류를 확인하려면 example_usage.py를 실행하세요.")

if __name__ == "__main__":
    main()

