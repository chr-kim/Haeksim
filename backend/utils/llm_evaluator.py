# utils/llm_evaluator.py

import os
import logging
from google import genai  # 최신 공식 라이브러리
from google.genai import types
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)

# Google API 키 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ✅ 클라이언트 초기화 (새 라이브러리 방식)
if not GOOGLE_API_KEY:
    logger.error("❌ GOOGLE_API_KEY가 설정되지 않았습니다.")
    client = None
else:
    client = genai.Client(api_key=GOOGLE_API_KEY)

# 디버깅 정보 출력
print(f"🔑 API Key loaded: {'Yes' if GOOGLE_API_KEY else 'No'}")
print(f"🔑 API Key length: {len(GOOGLE_API_KEY) if GOOGLE_API_KEY else 0}")
print(f"🔑 API Key starts with: {GOOGLE_API_KEY[:10] if GOOGLE_API_KEY else 'None'}...")

# ✅ 새 라이브러리용 설정 구조체
generation_config = types.GenerateContentConfig(
    response_mime_type="application/json",
    temperature=0.7,  # 창의성과 일관성 균형
    max_output_tokens=2048,  # 충분한 응답 길이
    top_p=0.8,  # 응답 품질 제어
    top_k=40   # 토큰 선택 다양성 제어
)

async def get_gemini_evaluation(prompt: str) -> dict:
    """
    Gemini API를 호출하여 평가 결과(text)와 토큰 사용량(usage)을 함께 반환합니다.
    
    Args:
        prompt (str): LLM에게 보낼 평가 요청 프롬프트
        
    Returns:
        dict: {'text': JSON 문자열, 'usage': 토큰 사용량 객체}를 포함한 딕셔너리
        
    Raises:
        Exception: API 호출 실패 시 발생
    """
    
    if client is None:
        raise ValueError("Gemini 클라이언트가 초기화되지 않았습니다. API 키를 확인해주세요.")
    
    try:
        logger.info("🤖 Gemini API 호출 시작...")
        logger.debug(f"📝 프롬프트 길이: {len(prompt)} 문자")
        
        # ✅ 새 라이브러리 방식으로 비동기 API 호출
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",  # 가성비 최적 모델
            contents=prompt,
            config=generation_config
        )
        
        # 응답 텍스트 검증
        if not response or not response.text:
            logger.error("❌ Gemini API에서 빈 응답을 받았습니다.")
            raise ValueError("API에서 빈 응답을 반환했습니다.")
        
        logger.info("✅ Gemini API 호출 성공")
        logger.debug(f"📄 응답 길이: {len(response.text)} 문자")
        logger.debug(f"📊 토큰 사용량: {response.usage_metadata}")
        
        # ✨ 핵심 기능: 응답 텍스트와 토큰 사용량 함께 반환
        return {
            "text": response.text,
            "usage": response.usage_metadata
        }
        
    except Exception as e:
        logger.error(f"❌ API 호출 중 오류 발생: {str(e)}")
        
        # 상세한 오류 정보 로깅
        if "API_KEY_INVALID" in str(e):
            logger.error("🔑 API 키가 유효하지 않습니다. Google AI Studio에서 새 키를 발급받아 주세요.")
        elif "QUOTA_EXCEEDED" in str(e):
            logger.error("📊 API 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요.")
        elif "MODEL_NOT_FOUND" in str(e):
            logger.error("🔍 모델을 찾을 수 없습니다. 모델명을 확인해주세요.")
        
        raise e

# 선택적: 다른 모델로 쉽게 교체 가능한 함수들
def get_model_for_simple_tasks():
    """간단한 작업용 모델 (더 저렴)"""
    simple_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.3,  # 더 일관된 응답
    )
    return "gemini-2.5-flash-lite", simple_config

def get_model_for_complex_tasks():
    """복잡한 작업용 모델 (더 정확)"""
    complex_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.8,  # 더 창의적인 응답
    )
    return "gemini-2.5-flash", complex_config  # Flash-Lite보다 성능이 좋지만 비쌈

# API 키 상태 확인 함수
def check_api_key_status():
    """API 키 상태를 확인하는 헬퍼 함수"""
    if not GOOGLE_API_KEY:
        return False, "GOOGLE_API_KEY 환경변수가 설정되지 않았습니다."
    
    if len(GOOGLE_API_KEY) < 30:
        return False, "API 키가 너무 짧습니다. 올바른 키인지 확인해주세요."
    
    return True, "API 키가 올바르게 설정되었습니다."

# 새 라이브러리 설정 확인 함수
def check_new_library_setup():
    """새 라이브러리 설정 상태 확인"""
    try:
        # 간단한 테스트 클라이언트 생성
        test_client = genai.Client(api_key=GOOGLE_API_KEY)
        logger.info("✅ 새 google-genai 라이브러리 설정 완료")
        return True
    except Exception as e:
        logger.error(f"❌ 새 라이브러리 설정 오류: {str(e)}")
        return False
