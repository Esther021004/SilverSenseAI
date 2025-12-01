"""
Gemini 모델 사용 예제
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# RAG 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from rag.rag_system import RAGSystem

def main():
    """Gemini 사용 예제"""
    load_dotenv()
    
    # Google API 키 확인
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   .env 파일을 생성하고 GOOGLE_API_KEY를 설정하세요.")
        print("   API 키 발급: https://makersuite.google.com/app/apikey")
        return
    
    print("="*60)
    print("Gemini 기반 응급 지침 생성 시스템 (무료!)")
    print("="*60)
    
    # RAG 시스템 초기화 (Gemini 사용)
    print("\n[시스템 초기화 중...]")
    rag_system = RAGSystem(
        document_dir="document",
        persist_directory="./chroma_db",
        llm_model="gemini-2.0-flash",  # Gemini 모델 사용 (무료, 최신)
        rebuild_vectorstore=False
    )
    print("✅ 초기화 완료\n")
    
    # 예제 1: 낙상 사고
    print("="*60)
    print("예제 1: 낙상 사고 (Gemini 사용)")
    print("="*60)
    situation_1 = {
        "disasterLarge": "구급",
        "disasterMedium": "낙상",
        "urgencyLevel": "긴급",
        "sentiment": "불안",
        "triage": "적색"
    }
    
    result_1 = rag_system.generate_guideline(
        situation_1,
        additional_context="쓰러진 상태에서 숨을 못 쉬고 있음"
    )
    
    print(f"\n재난 유형: {result_1['disaster_type']}")
    print(f"심각도: {result_1['urgency_level']}")
    print(f"\n지침:\n{result_1['guideline']}")
    print(f"\n신고 메시지: {result_1['report_message']}")
    print(f"\n참고 출처: {len(result_1['sources'])}개")
    for i, source in enumerate(result_1['sources'], 1):
        print(f"  {i}. {Path(source['source']).name} (페이지 {source.get('page', '?')})")
    
    print("\n" + "="*60)
    print("✅ Gemini 사용 예제 완료!")
    print("="*60)
    print("\n💡 Gemini는 무료이며 한국어 처리도 우수합니다!")

if __name__ == "__main__":
    main()

