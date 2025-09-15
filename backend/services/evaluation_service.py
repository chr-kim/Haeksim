# backend/services/evaluation_service.py
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from core.config import GOOGLE_API_KEY # OpenAI 대신 Google 키를 사용하도록 수정
from langchain_google_genai import GoogleGenerativeAIEmbeddings # Google 임베딩 모델 사용

# --- 서비스 초기화: 애플리케이션 시작 시 한 번만 실행되도록 ---

# 1. 데이터 경로 설정
#    우리가 1단계에서 복사해온 데이터의 경로입니다.
INDEX_PATH = "backend/data/faiss.index"
METADATA_PATH = "backend/data/metadata.jsonl" # 메타데이터 경로도 필요할 수 있습니다.

# 2. 임베딩 모델 로드
#    모델 담당은 OpenAI를 썼을 수 있지만, 우리는 Google 기반으로 통일합니다.
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)

# 3. FAISS Vector DB 로드
#    애플리케이션이 시작될 때 메모리에 상주하여, 요청마다 새로 로드하는 것을 방지합니다.
try:
    vector_db = FAISS.load_local(
        folder_path="backend/data", # 인덱스 파일이 있는 폴더
        embeddings=embeddings, 
        index_name="faiss", # 인덱스 파일 이름 (확장자 제외)
        allow_dangerous_deserialization=True # FAISS 로드 시 필요한 옵션
    )
    retriever = vector_db.as_retriever()
    print("✅ FAISS index loaded successfully.")
except Exception as e:
    print(f"❌ Error loading FAISS index: {e}")
    retriever = None

# --- 실제 서비스 함수 ---

async def get_relevant_passage(query: str) -> str:
    """
    사용자의 질문(query)과 가장 관련성 높은 지문 내용을 Vector DB에서 검색합니다.
    """
    if not retriever:
        return "Vector DB가 로드되지 않아 검색을 수행할 수 없습니다."
        
    try:
        # 4. retriever를 사용하여 관련 문서 검색
        retrieved_docs = retriever.invoke(query)
        
        if retrieved_docs:
            # 검색된 문서들 중 가장 관련성 높은 문서의 내용을 반환합니다.
            return retrieved_docs[0].page_content
        return "관련된 해설을 찾을 수 없습니다."
    except Exception as e:
        print(f"Error during retrieval: {e}")
        return "해설을 검색하는 중 오류가 발생했습니다."