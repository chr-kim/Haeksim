# backend/services/evaluation_service.py

import os
import json
import faiss
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings # Google 임베딩 모델 사용
from core.config import GOOGLE_API_KEY

# --- 서비스 초기화: 애플리케이션 시작 시 한 번만 실행되도록 ---

# 1. 데이터 경로 설정
# 모델 폴더에서 복사해온 실제 데이터 경로입니다.
FAISS_INDEX_PATH = "/app/data/passages.faiss"  # 실제 FAISS 인덱스 파일
METADATA_PATH = "/app/data/meta.json"          # 메타데이터 JSON 파일

# 또는 현재 파일 기준 상대경로 (더 안전한 방법)
def get_data_path():
    """현재 파일 위치 기준으로 data 디렉토리 경로 반환"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # /app/services/evaluation_service.py -> /app/data
    return os.path.join(os.path.dirname(current_dir), "data")

DATA_DIR = get_data_path()
FAISS_INDEX_PATH_ALT = os.path.join(DATA_DIR, "passages.faiss")
METADATA_PATH_ALT = os.path.join(DATA_DIR, "meta.json")

# 2. 임베딩 모델 로드
# Google 기반으로 통일하여 사용합니다.
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)

# 3. 전역 변수 초기화
faiss_index = None
metadata_list = None

# 4. FAISS Vector DB와 메타데이터 직접 로드
# PKL 파일 없이 FAISS 인덱스와 메타데이터를 각각 로드합니다.
def load_faiss_index_and_metadata():
    """FAISS 인덱스와 메타데이터를 직접 로드하는 함수"""
    global faiss_index, metadata_list
    
    # 여러 경로 시도
    possible_paths = [
        ("/app/data/passages.faiss", "/app/data/meta.json"),
        (FAISS_INDEX_PATH_ALT, METADATA_PATH_ALT),
        ("backend/data/passages.faiss", "backend/data/meta.json"),
        ("data/passages.faiss", "data/meta.json")
    ]
    
    print("🔍 FAISS 인덱스 파일 경로 탐색 중...")
    
    for faiss_path, meta_path in possible_paths:
        print(f"   시도 중: {faiss_path}")
        
        if os.path.exists(faiss_path) and os.path.exists(meta_path):
            try:
                # FAISS 인덱스 로드
                faiss_index = faiss.read_index(faiss_path)
                
                # 메타데이터 로드
                with open(meta_path, "r", encoding="utf-8") as f:
                    metadata_list = json.load(f)
                
                print(f"✅ FAISS 인덱스 로드 성공: {faiss_index.ntotal}개 벡터")
                print(f"✅ 메타데이터 로드 성공: {len(metadata_list)}개 문서")
                print(f"📁 사용된 경로: {faiss_path}")
                print("✅ FAISS Vector DB 초기화 완료 - 검색 서비스 준비됨")
                
                return  # 성공하면 함수 종료
                
            except Exception as e:
                print(f"❌ 파일은 존재하지만 로드 실패: {e}")
                continue
        else:
            print(f"   ❌ 파일 없음")
    
    # 모든 경로 실패
    print("❌ 모든 경로에서 FAISS 인덱스를 찾을 수 없습니다.")
    print("⚠️ FAISS 또는 메타데이터 로드 실패 - 기본 해설 모드로 동작")
    faiss_index, metadata_list = None, None

# 애플리케이션 시작 시 인덱스 로드 실행
load_faiss_index_and_metadata()

# --- 실제 서비스 함수 ---

async def get_relevant_passage(query: str) -> str:
    """
    사용자의 질문(query)과 가장 관련성 높은 지문 내용을 Vector DB에서 검색합니다.
    PKL 파일 없이 직접 FAISS 인덱스를 사용하여 검색을 수행합니다.
    
    Args:
        query (str): 사용자의 질문 또는 검색어
        
    Returns:
        str: 검색된 관련 지문 내용 또는 기본 메시지
    """
    
    # Vector DB 로드 상태 확인
    if faiss_index is None or metadata_list is None:
        return """
        Vector DB가 로드되지 않아 기본 해설을 제공합니다.
        
        수능 국어 비문학 문제 해설:
        학생의 답변을 종합적으로 평가하여 정확한 피드백을 제공합니다.
        지문의 핵심 내용과 논리적 추론 과정을 중심으로 평가합니다.
        """
    
    try:
        # 1. 쿼리를 임베딩 벡터로 변환
        query_vector = embeddings.embed_query(query)
        query_array = np.array([query_vector], dtype=np.float32)
        
        # 2. FAISS를 사용하여 유사한 문서 검색 (상위 3개)
        k = 3  # 검색할 문서 개수
        distances, indices = faiss_index.search(query_array, k)
        
        # 3. 검색 결과에서 관련 문서 추출
        retrieved_passages = []
        for i, idx in enumerate(indices[0]):
            # 유효한 인덱스인지 확인
            if idx >= 0 and idx < len(metadata_list):
                doc_data = metadata_list[idx]
                
                # 문서에서 텍스트 내용 추출 (다양한 키 형태 지원)
                text_content = doc_data.get("text", doc_data.get("content", doc_data.get("passage", "")))
                
                if text_content:
                    # 텍스트 길이 제한 (너무 긴 경우 500자로 제한)
                    limited_text = text_content[:500] + "..." if len(text_content) > 500 else text_content
                    retrieved_passages.append(limited_text)
                    
                    # 검색 품질을 위한 디버그 정보 (개발용)
                    print(f"📄 검색된 문서 {i+1}: 유사도 점수 {distances[0][i]:.4f}")
        
        # 4. 검색 결과가 있으면 포맷팅하여 반환
        if retrieved_passages:
            combined_content = "\n\n=== 관련 해설 ===\n\n".join(retrieved_passages)
            return f"벡터 검색 결과:\n\n{combined_content}"
        else:
            return "관련된 해설을 찾을 수 없습니다. 기본 평가 기준에 따라 답변을 평가하겠습니다."
            
    except Exception as e:
        print(f"Error during retrieval: {e}")
        return f"해설을 검색하는 중 오류가 발생했습니다: {str(e)}"

# --- 추가 유틸리티 함수 ---

def get_vector_db_status():
    """Vector DB 상태 확인용 함수 (디버깅/모니터링용)"""
    status = {
        "faiss_loaded": faiss_index is not None,
        "metadata_loaded": metadata_list is not None,
        "vector_count": faiss_index.ntotal if faiss_index else 0,
        "document_count": len(metadata_list) if metadata_list else 0
    }
    return status

def reload_vector_db():
    """Vector DB 재로드 함수 (필요시 사용)"""
    print("🔄 Vector DB 재로드 중...")
    load_faiss_index_and_metadata()
