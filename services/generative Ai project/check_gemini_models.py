"""
사용 가능한 Gemini 모델 목록 확인
"""
import os
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        exit(1)
    
    genai.configure(api_key=api_key)
    
    print("="*60)
    print("사용 가능한 Gemini 모델 목록")
    print("="*60)
    
    models = genai.list_models()
    print("\n사용 가능한 모델들:")
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"  ✅ {model.name}")
            if hasattr(model, 'display_name'):
                print(f"     이름: {model.display_name}")
            print(f"     메서드: {model.supported_generation_methods}")
            print()
    
    print("\n추천 모델:")
    print("  - gemini-2.0-flash (최신, 무료, 추천!)")
    print("  - gemini-2.5-flash-lite (더 가벼움)")
    print("  - gemini-pro (안정적, 구버전)")
    
except Exception as e:
    print(f"❌ 오류: {e}")

