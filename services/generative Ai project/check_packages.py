"""
필요한 패키지가 모두 설치되었는지 확인하는 스크립트
"""
import sys

required_packages = [
    "pypdf",
    "pdfplumber",
    "langchain",
    "langchain_community",
    "langchain_openai",
    "chromadb",
    "sentence_transformers",
    "numpy",
    "dotenv"
]

print("="*60)
print("패키지 설치 확인")
print("="*60)
print()

missing_packages = []

for package in required_packages:
    try:
        if package == "dotenv":
            __import__("dotenv")
        else:
            __import__(package)
        print(f"✅ {package}")
    except ImportError:
        print(f"❌ {package} - 설치 필요")
        missing_packages.append(package)

print()
print("="*60)

if missing_packages:
    print(f"❌ {len(missing_packages)}개 패키지가 누락되었습니다:")
    print()
    print("다음 명령어로 설치하세요:")
    print(f"pip install {' '.join(missing_packages)}")
    sys.exit(1)
else:
    print("✅ 모든 패키지가 설치되어 있습니다!")
    print()
    print("다음 명령어로 벡터 스토어를 구축하세요:")
    print("python build_vectorstore.py")

