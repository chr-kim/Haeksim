import json
from fastapi import FastAPI, HTTPException
from schemas import EvaluationRequest, EvaluationResponse
from utils.llm_evaluator import get_gemini_evaluation # 1. Gemini 평가 함수를 가져옵니다.

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_answer(request: EvaluationRequest):
    # TODO: 2. DB나 JSON 파일에서 문제의 정답과 해설 데이터를 조회하는 로직
    # 이 부분은 나중에 parser.py와 연결됩니다.
    problem_id = request.problem_id
    correct_answer = "이 문제의 정답과 전문가 해설 내용입니다..." # 임시 데이터

    # 3. Gemini에게 전달할 상세한 프롬프트를 구성합니다.
    prompt = f"""
    당신은 수능 국어 영역 전문가입니다. 아래의 '평가 기준'에 따라 학생의 답변을 채점하고,
    결과를 반드시 JSON 형식으로 반환해 주세요.

    [문제의 정답 및 해설]
    {correct_answer}

    [학생이 제출한 답변]
    - 선택 답안: {request.user_answer_id}번
    - 선택 근거: {request.user_reasoning}

    [평가 기준]
    1. 이해의 정확성: 학생이 제시한 근거가 지문의 핵심 내용과 일치하는가?
    2. 논리적 연결성: 그 근거를 바탕으로 답안을 선택한 과정이 타당한가?

    [출력할 JSON 형식]
    {{
      "total_score": <총점(정수)>,
      "feedbacks": [
        {{
          "criteria": "이해의 정확성",
          "score": <점수(정수)>,
          "comment": "<피드백 코멘트(문자열)>"
        }},
        {{
          "criteria": "논리적 연결성",
          "score": <점수(정수)>,
          "comment": "<피드백 코멘트(문자열)>"
        }}
      ]
    }}
    """

    try:
        # 4. 구성된 프롬프트로 Gemini API를 호출합니다.
        gemini_response_text = await get_gemini_evaluation(prompt)
        
        # 5. Gemini가 반환한 JSON 문자열을 파이썬 딕셔너리로 변환합니다.
        evaluation_data = json.loads(gemini_response_text)

        # 6. Pydantic 모델을 사용하여 응답 데이터의 유효성을 검증하고 반환합니다.
        return EvaluationResponse(**evaluation_data)

    except Exception as e:
        # API 호출 실패 또는 JSON 파싱 오류 시 에러를 반환합니다.
        raise HTTPException(status_code=500, detail=f"LLM 평가 중 오류 발생: {str(e)}")
