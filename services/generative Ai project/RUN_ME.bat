@echo off
echo ========================================
echo RAG 시스템 벡터 스토어 구축
echo ========================================
echo.
echo 이 스크립트는 document 폴더의 PDF를 읽어서
echo 벡터 데이터베이스를 구축합니다.
echo.
echo 예상 시간: 5-15분
echo.
pause

python build_vectorstore.py

echo.
echo ========================================
echo 벡터 스토어 구축 완료!
echo ========================================
echo.
echo 다음 명령어로 검색 기능을 테스트하세요:
echo   python test_search_only.py
echo.
pause

