# backend/services/passage_service.py

import json
from core.db import database
from models.problem import problems
from schemas.passage import PassageGenerateRequest
from utils.llm_evaluator import get_gemini_evaluation

async def generate_and_save_passage(request: PassageGenerateRequest):
    """
    요청(request)에 따라 적절한 프롬프트를 생성하고,
    Gemini API를 호출하여 지문과 문제를 생성한 후 결과를 반환하거나 DB에 저장합니다.
    """
    # features에 따라 다른 프롬프트 구성
    if request.features == "지문요약 핵심파악":
        prompt = f"""
당신은 수능 국어 영역 출제위원입니다.
다음 조건에 맞춰 비문학 지문을 생성해주세요.

- 난이도: {request.difficulty}
- 주제: {request.topic}
- 지문 길이: 약 {request.passageLength}자

결과는 반드시 다음 JSON 형식으로만 반환해주세요:
{{
    "passage": "생성된 지문 내용..."
}}
"""
    elif request.features == "선지 분석 & 논리 평가":
        prompt = f"""
당신은 수능 국어 영역 출제위원입니다.
다음 조건에 맞춰 비문학 지문과 4개의 선택지를 생성해주세요.

- 난이도: {request.difficulty}
- 주제: {request.topic}
- 지문 길이: 약 {request.passageLength}자

결과는 반드시 다음 JSON 형식으로만 반환해주세요:
{{
    "passage": "생성된 지문 내용...",
    "choices": [
        "선택지 1 내용",
        "선택지 2 내용",
        "선택지 3 내용",
        "선택지 4 내용"
    ]
}}
"""
    else:
        prompt = f"""
당신은 수능 국어 영역 출제위원입니다.
다음 조건에 맞춰 비문학 지문 1개와 5지선다형 문제 1개를 생성해주세요.

- 난이도: {request.difficulty}
- 주제: {request.topic}
- 특징: {request.features}
- 지문 길이: 약 {request.passageLength}자

결과는 반드시 다음 JSON 형식으로만 반환해주세요.
{{
    "passage": "생성된 지문 내용...",
    "question": "문제 내용...",
    "choices": [
        "선택지 1 내용",
        "선택지 2 내용",
        "선택지 3 내용",
        "선택지 4 내용",
        "선택지 5 내용"
    ],
    "answer": 정답 번호 (예: 3),
    "explanation": "정답 해설..."
}}
"""

    try:
        # API 호출
        response = await get_gemini_evaluation(prompt)
        raw_text = response["text"]
        
        # JSON 파싱 전 정제 작업
        cleaned_text = clean_json_response(raw_text)
        
        # JSON 파싱
        problem_data = json.loads(cleaned_text)

        # 토큰 사용량 로깅
        usage = response["usage"]
        print(f"📊 지문 생성 토큰 사용량:")
        print(f"    입력 토큰: {getattr(usage, 'prompt_token_count', 'N/A')}")
        print(f"    출력 토큰: {getattr(usage, 'candidates_token_count', 'N/A')}")
        print(f"    총 토큰: {getattr(usage, 'total_token_count', 'N/A')}")

        # features에 따라 반환 양식 결정
        if request.features == "지문요약 핵심파악":
            if "passage" not in problem_data:
                raise ValueError("'passage' 키가 응답에 없습니다.")
            return {"passage": problem_data["passage"]}

        elif request.features == "선지 분석 & 논리 평가":
            if not all(key in problem_data for key in ["passage", "choices"]):
                raise ValueError("'passage' 또는 'choices' 키가 응답에 없습니다.")
            
            # choices 형식 변환
            choices_list = []
            if isinstance(problem_data["choices"], list):
                for choice in problem_data["choices"]:
                    if isinstance(choice, str):
                        choices_list.append(choice)
                    elif isinstance(choice, dict) and "text" in choice:
                        choices_list.append(choice["text"])
                    else:
                        choices_list.append(str(choice))
            
            return {
                "passage": problem_data["passage"],
                "choices": choices_list
            }

        else:
            # 기본: DB 저장 후 problem_id 반환
            query = problems.insert().values(
                passage=problem_data.get("passage", ""),
                question=problem_data.get("question", ""),
                choices=json.dumps(problem_data.get("choices", []), ensure_ascii=False),
                answer=problem_data.get("answer", 0),
                explanation=problem_data.get("explanation", "")
            )
            
            last_record_id = await database.execute(query)
            return {"problem_id": last_record_id}

    except KeyError as e:
        print(f"❌ API 응답 구조 오류: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        print(f"원본 텍스트: {raw_text[:200]}...")
        print(f"정제된 텍스트: {cleaned_text if 'cleaned_text' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"❌ Error during passage generation: {e}")
        return None

# ✅ 수정 및 개선된 JSON 정제 함수
def clean_json_response(text: str) -> str:
    """
    Gemini API 응답에서 불필요한 마크다운 코드 블록 등을 제거하여
    순수한 JSON 문자열만 추출합니다.
    """
    # 앞뒤 공백 제거
    text = text.strip()
    
    # 코드 블록 마크다운 제거 (예: ```json ... ```)
    if text.startswith("```json"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    
    if text.endswith("```"):
        text = text[:-3].strip()
    
    # 문자열에서 첫 '{'와 마지막 '}'를 찾아 그 사이의 내용만 추출
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        return text[start:end]
    except ValueError:
        # '{' 또는 '}'를 찾을 수 없는 경우, 원본 텍스트 반환
        return text