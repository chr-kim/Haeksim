# backend/api/evaluation.py

import json
from fastapi import APIRouter, HTTPException, status
from schemas.evaluation import EvaluationRequest, EvaluationResponse
from services import evaluation_service
from utils.llm_evaluator import get_gemini_evaluation

router = APIRouter()

@router.post("", response_model=EvaluationResponse)
async def evaluate_user_answer(request: EvaluationRequest):
    """
    사용자의 답변을 받아 RAG 검색 후, LLM으로 최종 평가를 수행합니다.
    """
    
    # 1. 서비스 계층을 호출하여 RAG 검색 수행
    expert_explanation = await evaluation_service.get_relevant_passage(request.user_reasoning)
    
    if "오류" in expert_explanation or "찾을 수 없습니다" in expert_explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관련 해설을 찾는 데 실패했습니다."
        )
    
    # 2. Gemini에게 보낼 최종 프롬프트 구성
    prompt = f"""
당신은 수능 국어 영역 전문가입니다. 아래의 '전문가 해설'을 절대적인 기준으로 삼아,
'학생의 답변'을 채점하고 결과를 반드시 JSON 형식으로 반환해 주세요.

[전문가 해설]
{expert_explanation}

[학생의 답변]
- 문제 ID: {request.problem_id}
- 선택한 답: {request.user_answer_id}번
- 선택 근거: {request.user_reasoning}

[평가 기준]
- 이해의 정확성: 학생의 근거가 전문가 해설의 핵심 내용과 일치하는가?
- 논리적 연결성: 그 근거를 바탕으로 답안을 선택한 과정이 타당한가?

[출력할 JSON 형식]
{{
    "total_score": <총점(정수, 0-100)>,
    "feedbacks": [
        {{"criteria": "이해의 정확성", "score": <점수(정수)>, "comment": "<피드백 코멘트(문자열)>"}},
        {{"criteria": "논리적 연결성", "score": <점수(정수)>, "comment": "<피드백 코멘트(문자열)>"}}
    ]
}}
"""

    try:
        # ✅ 3. 새 API 형식에 맞게 수정
        response = await get_gemini_evaluation(prompt)
        
        # response는 {'text': json_string, 'usage': usage_obj} 형태
        evaluation_data = json.loads(response["text"])
        
        # ✅ 4. 토큰 사용량 로깅 (운영 관리용)
        usage = response["usage"]
        print(f"📊 평가 토큰 사용량:")
        print(f"   입력 토큰: {getattr(usage, 'prompt_token_count', 'N/A')}")
        print(f"   출력 토큰: {getattr(usage, 'candidates_token_count', 'N/A')}")
        print(f"   총 토큰: {getattr(usage, 'total_token_count', 'N/A')}")
        
        return EvaluationResponse(**evaluation_data)
        
    except KeyError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"API 응답 구조 오류: {str(e)}"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"JSON 파싱 오류: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"LLM 평가 중 오류 발생: {str(e)}"
        )
