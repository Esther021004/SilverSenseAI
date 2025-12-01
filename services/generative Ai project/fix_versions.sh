# LangChain 패키지 버전 충돌 해결 스크립트

echo "구버전 LangChain 패키지 제거 중..."
pip uninstall -y langchain langchain-community langchain-classic langchain-text-splitters

echo ""
echo "최신 버전 패키지 설치 중..."
pip install -r requirements.txt

echo ""
echo "완료! 이제 python example_usage.py 를 실행해보세요."

