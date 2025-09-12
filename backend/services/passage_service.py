# backend/services/passage_service.py
import json
from core.db import database
from models.problem import problems
from schemas.passage import PassageGenerateRequest
from utils.llm_evaluator import get_gemini_evaluation # Gemini 호출 함수 재활용

async def generate_and_save_passage(request: PassageGenerateRequest):
    # 1. Gemini에게 전달할 상세한 프롬프트를 구성합니다.
    prompt = f"""
    당신은 수능 국어 영역 출제위원입니다.
    다음 조건에 맞춰 비문학 지문 1개와 5지선다형 문제 1개를 생성해주세요.
    - 난이도: {request.difficulty}
    - 주제: {request.topic}
    - 지문 길이: 약 {request.length}자

    결과는 반드시 다음 JSON 형식으로만 반환해주세요:
    {{
      "passage": "생성된 지문 내용...",
      "question": "생성된 문제 내용...",
      "choices": [
        {{"id": 1, "text": "선택지 1 내용..."}},
        {{"id": 2, "text": "선택지 2 내용..."}},
        {{"id": 3, "text": "선택지 3 내용..."}},
        {{"id": 4, "text": "선택지 4 내용..."}},
        {{"id": 5, "text": "선택지 5 내용..."}}
      ],
      "answer": <정답_선택지_ID(정수)>,
      "explanation": "문제에 대한 상세한 해설..."
    }}
    """

    try:
        # 2. Gemini API를 호출하여 문제 데이터를 생성합니다.
        response_text = await get_gemini_evaluation(prompt)
        problem_data = json.loads(response_text)

        # 3. 생성된 데이터를 DB에 저장합니다.
        query = problems.insert().values(
            passage=problem_data["passage"],
            question=problem_data["question"],
            choices=json.dumps(problem_data["choices"]), # list를 JSON 문자열로 변환하여 저장
            answer=problem_data["answer"],
            explanation=problem_data["explanation"]
        )
        last_record_id = await database.execute(query)
        return {"problem_id": last_record_id}

    except Exception as e:
        # 오류 발생 시 None 반환 (API 계층에서 처리)
        print(f"Error during passage generation: {e}")
        return None