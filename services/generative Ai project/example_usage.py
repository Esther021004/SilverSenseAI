"""
RAG 시스템 사용 예제
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# RAG 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from rag.rag_system import RAGSystem

def main():
    """사용 예제"""
    load_dotenv()
    
    # OpenAI API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   .env 파일을 생성하고 OPENAI_API_KEY를 설정하세요.")
        return
    
    print("="*60)
    print("RAG 기반 응급 지침 생성 시스템")
    print("="*60)
    
    # RAG 시스템 초기화
    print("\n[시스템 초기화 중...]")
    rag_system = RAGSystem(
        document_dir="document",
        persist_directory="./chroma_db",
        rebuild_vectorstore=False  # 이미 구축했다면 False
    )
    print("✅ 초기화 완료\n")
    
    # 예제 1: 낙상 사고
    print("="*60)
    print("예제 1: 낙상 사고")
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
    
    # 예제 2: 화재 발생
    print("\n" + "="*60)
    print("예제 2: 화재 발생")
    print("="*60)
    situation_2 = {
        "disasterLarge": "재난",
        "disasterMedium": "화재",
        "urgencyLevel": "긴급",
        "sentiment": "공포",
        "triage": "적색"
    }
    
    result_2 = rag_system.generate_guideline(
        situation_2,
        additional_context="연기가 보이고 불길이 번지고 있음"
    )
    
    print(f"\n재난 유형: {result_2['disaster_type']}")
    print(f"심각도: {result_2['urgency_level']}")
    print(f"\n지침:\n{result_2['guideline']}")
    print(f"\n신고 메시지: {result_2['report_message']}")
    print(f"\n참고 출처: {len(result_2['sources'])}개")
    for i, source in enumerate(result_2['sources'], 1):
        print(f"  {i}. {Path(source['source']).name} (페이지 {source.get('page', '?')})")
    
    # 예제 3: 호흡곤란
    print("\n" + "="*60)
    print("예제 3: 호흡곤란")
    print("="*60)
    situation_3 = {
        "disasterLarge": "구급",
        "disasterMedium": "호흡곤란",
        "urgencyLevel": "긴급",
        "sentiment": "공포",
        "triage": "적색"
    }
    
    result_3 = rag_system.generate_guideline(
        situation_3,
        additional_context="가슴 통증과 함께 숨이 가쁨"
    )
    
    print(f"\n재난 유형: {result_3['disaster_type']}")
    print(f"심각도: {result_3['urgency_level']}")
    print(f"\n지침:\n{result_3['guideline']}")
    print(f"\n신고 메시지: {result_3['report_message']}")
    print(f"\n참고 출처: {len(result_3['sources'])}개")
    for i, source in enumerate(result_3['sources'], 1):
        print(f"  {i}. {Path(source['source']).name} (페이지 {source.get('page', '?')})")
    
    print("\n" + "="*60)
    print("예제 실행 완료!")
    print("="*60)

if __name__ == "__main__":
    main()

