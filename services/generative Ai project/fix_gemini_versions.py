"""
Gemini 패키지 버전 충돌 자동 해결 스크립트
"""
import subprocess
import sys

def run_command(cmd):
    """명령어 실행"""
    print(f"\n{'='*60}")
    print(f"실행: {cmd}")
    print('='*60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("경고:", result.stderr)
    return result.returncode == 0

def main():
    print("="*60)
    print("Gemini 패키지 버전 충돌 해결")
    print("="*60)
    
    steps = [
        ("오래된 langchain-core 제거", 'pip uninstall -y langchain-core'),
        ("최신 langchain-core 설치", 'pip install "langchain-core>=1.1.0,<2.0.0"'),
        ("protobuf 버전 조정", 'pip install "protobuf>=4.25.3,<5"'),
        ("Gemini 패키지 재설치", 'pip install langchain-google-genai google-generativeai')
    ]
    
    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {desc}...")
        if not run_command(cmd):
            print(f"❌ 실패: {desc}")
            response = input("계속 진행하시겠습니까? (y/n): ")
            if response.lower() != 'y':
                return
        else:
            print(f"✅ 완료: {desc}")
    
    print("\n" + "="*60)
    print("✅ 모든 단계 완료!")
    print("="*60)
    print("\n이제 다음 명령어로 테스트하세요:")
    print("  python example_gemini.py")

if __name__ == "__main__":
    main()

