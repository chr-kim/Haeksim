# main.py (정리된 최종 버전)
import json
import logging
import os
from fastapi import FastAPI, HTTPException
from schemas import EvaluationRequest, EvaluationResponse
from utils.llm_evaluator import get_gemini_evaluation
from utils.parser import parse_exam_pdf, debug_pdf_content

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI()

# PDF 파일 매핑 설정
PDF_FILE_MAPPING = {
    # 더 넓은 범위로 확장 (실제 문제 번호에 맞게)
    range(1, 300): ("data/test_2017_2022.pdf", 0, 124),  # 전체 124페이지 스캔
}

# 파싱된 데이터 캐시
parsed_problems_cache = {}

def get_pdf_file_info(problem_id: int) -> tuple:
    """problem_id에 해당하는 PDF 파일 정보 반환"""
    for id_range, (file_path, start_page, end_page) in PDF_FILE_MAPPING.items():
        if problem_id in id_range:
            return file_path, start_page, end_page
    return None, None, None

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 PDF 파일 상태 확인"""
    pdf_file = "data/test_2017_2022.pdf"
    logger.info("🚀 Starting application...")
    logger.info("📋 Checking PDF files...")
    
    # PDF 디버깅 실행
    debug_pdf_content(pdf_file)

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_answer(request: EvaluationRequest):
    logger.info(f"📝 Evaluation request: problem_id={request.problem_id}")
    
    problem_id = request.problem_id
    
    if problem_id not in parsed_problems_cache:
        # 파일 매핑 정보 가져오기
        file_path, start_page, end_page = get_pdf_file_info(problem_id)
        
        if not file_path:
            logger.error(f"❌ No PDF mapping found for problem_id: {problem_id}")
            raise HTTPException(status_code=404, detail="해당 문제 ID에 대한 PDF 파일을 찾을 수 없습니다.")
        
        logger.info(f"📄 Using PDF: {file_path}, pages: {start_page}-{end_page}")
        
        # 파서에 추가 정보 전달
        parsed_data = parse_exam_pdf(file_path, problem_id, start_page, end_page)
        
        if not parsed_data:
            logger.error(f"❌ Failed to parse PDF for problem_id: {problem_id}")
            raise HTTPException(status_code=404, detail="해당 문제의 PDF를 찾거나 파싱할 수 없습니다.")
        
        parsed_problems_cache[problem_id] = parsed_data
        logger.info(f"✅ Successfully cached problem {problem_id}")
    
    problem_data = parsed_problems_cache[problem_id]
    expert_explanation = problem_data["expert_explanation"]
    
    # LLM 프롬프트 구성
    prompt = f"""
    당신은 수능 국어 영역 전문가입니다. 아래의 '평가 기준'에 따라 학생의 답변을 채점하고,
    결과를 반드시 JSON 형식으로 반환해 주세요.

    [문제의 정답 및 해설]
    {expert_explanation}

    [학생이 제출한 답변]
    - 선택 답안: {request.user_answer_id}번
    - 선택 근거: {request.user_reasoning}

    [평가 기준과 JSON 출력 형식]
    {{
        "total_score": 85,
        "feedbacks": [
            {{
                "criteria": "이해의 정확성",
                "score": 90,
                "comment": "지문의 핵심 내용을 정확히 파악했습니다."
            }}
        ]
    }}
    """
    
    try:
        logger.info("🤖 Calling Gemini API...")
        # LLM 평가 모듈 호출
        gemini_response_text = await get_gemini_evaluation(prompt)
        evaluation_data = json.loads(gemini_response_text)
        
        logger.info(f"✅ Evaluation completed for problem {problem_id}")
        return EvaluationResponse(**evaluation_data)
        
    except Exception as e:
        logger.error(f"❌ LLM evaluation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM 평가 중 오류 발생: {str(e)}")
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 설정 확인"""
    from utils.parser import debug_pdf_content
    from utils.llm_evaluator import check_new_library_setup
    
    logger.info("🚀 Starting application...")
    logger.info("📋 Checking PDF files...")
    
    # PDF 디버깅
    pdf_file = "data/test_2017_2022.pdf"
    debug_pdf_content(pdf_file)
    
    # 새 라이브러리 설정 확인
    logger.info("🔧 Checking new google-genai library...")
    if check_new_library_setup():
        logger.info("✅ 새 라이브러리 준비 완료")
    else:
        logger.warning("⚠️ 새 라이브러리 설정에 문제가 있습니다")
# 헬스 체크 엔드포인트 추가
@app.get("/")
async def root():
    return {"message": "문제 풀이 평가 시스템이 정상 작동 중입니다."}
