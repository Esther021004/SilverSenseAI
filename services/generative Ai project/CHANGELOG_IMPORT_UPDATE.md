# LangChain Import 경로 업데이트 내역

## 🔄 변경 사항

LangChain 0.1.x 이후로 모듈 경로가 변경되어 모든 파일의 import를 최신 버전에 맞게 수정했습니다.

### 수정된 Import 경로

#### 1. Document 클래스
- ❌ 구버전: `from langchain.schema import Document`
- ✅ 신버전: `from langchain_core.documents import Document`

**수정된 파일:**
- `rag/document_loader.py`
- `rag/text_splitter.py`
- `rag/embedding_store.py`
- `rag/guideline_generator.py`

#### 2. Prompt 관련
- ❌ 구버전: `from langchain.prompts import ChatPromptTemplate`
- ✅ 신버전: `from langchain_core.prompts import ChatPromptTemplate`

**수정된 파일:**
- `rag/guideline_generator.py`

#### 3. Text Splitter (호환성 처리)
- 최신 버전과 구버전 모두 지원하도록 수정
- 최신: `from langchain_text_splitters import RecursiveCharacterTextSplitter`
- 구버전: `from langchain.text_splitter import RecursiveCharacterTextSplitter`

**수정된 파일:**
- `rag/text_splitter.py`

### Requirements.txt 업데이트

- `langchain-text-splitters` 패키지 추가 (최신 버전용)
- 버전 고정을 유연하게 변경 (>= 사용)

---

## ✅ 테스트 필요

이제 다음 명령어로 정상 작동하는지 확인하세요:

```bash
# 1. 패키지 재설치 (최신 버전)
pip install -r requirements.txt

# 2. 벡터 스토어 구축
python build_vectorstore.py

# 3. 검색 테스트
python test_search_only.py
```

---

## 📝 참고

- `langchain.chains.history_aware_retriever`는 아직 `langchain` 패키지에 남아있어서 변경하지 않았습니다.
- 추가적인 import 오류가 발생하면 해당 부분도 수정이 필요할 수 있습니다.

