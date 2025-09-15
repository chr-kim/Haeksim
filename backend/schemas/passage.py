# backend/schemas/passage.py

from pydantic import BaseModel
from typing import Union, List
from typing_extensions import Literal

# 프론트엔드로부터 받을 요청 데이터 형식
class PassageGenerateRequest(BaseModel):
    difficulty: str
    topic: str
    features: str
    passageLength: int

# 지문요약용 응답
class PassageOnlyResponse(BaseModel):
    passage: str

# 선지분석용 응답
class PassageChoicesResponse(BaseModel):
    passage: str
    choices: List[str]

# 기본 문제생성용 응답
class PassageGenerateResponse(BaseModel):
    problem_id: int

# ✅ 통합 응답 타입 (Union 사용)
PassageResponse = Union[PassageOnlyResponse, PassageChoicesResponse, PassageGenerateResponse]
