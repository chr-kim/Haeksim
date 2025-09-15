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
- 특징: {request.features}
- 지문 길이: 약 {request.passageLength}자

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
        # ✅ 2. 새 API 형식에 맞게 수정
        response = await get_gemini_evaluation(prompt)
        
        # response는 {'text': json_string, 'usage': usage_obj} 형태
        problem_data = json.loads(response["text"])  # text 키에서 JSON 문자열 추출
        
        # ✅ 3. 토큰 사용량 로깅 (운영 관리용)
        usage = response["usage"]
        print(f"📊 지문 생성 토큰 사용량:")
        print(f"   입력 토큰: {usage.prompt_token_count if hasattr(usage, 'prompt_token_count') else 'N/A'}")
        print(f"   출력 토큰: {usage.candidates_token_count if hasattr(usage, 'candidates_token_count') else 'N/A'}")
        print(f"   총 토큰: {usage.total_token_count if hasattr(usage, 'total_token_count') else 'N/A'}")
        
        # 4. 생성된 데이터를 DB에 저장합니다.
        query = problems.insert().values(
            passage=problem_data["passage"],
            question=problem_data["question"],
            choices=json.dumps(problem_data["choices"], ensure_ascii=False),  # 한글 지원
            answer=problem_data["answer"],
            explanation=problem_data["explanation"]
        )
        
        last_record_id = await database.execute(query)
        
        # ✅ 5. 토큰 사용량 정보도 함께 반환 (운영 관리용)
        return {
            "problem_id": last_record_id,
            "token_usage": {
                "prompt_tokens": getattr(usage, 'prompt_token_count', 0),
                "completion_tokens": getattr(usage, 'candidates_token_count', 0),
                "total_tokens": getattr(usage, 'total_token_count', 0)
            }
        }
        
    except KeyError as e:
        print(f"❌ API 응답 구조 오류: {e}")
        print(f"응답 내용: {response if 'response' in locals() else 'N/A'}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        print(f"응답 텍스트: {response.get('text', 'N/A') if 'response' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"❌ Error during passage generation: {e}")
        return None
