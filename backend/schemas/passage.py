# backend/schemas/passage.py
from pydantic import BaseModel

# 프론트엔드로부터 받을 요청 데이터 형식
class PassageGenerateRequest(BaseModel):
    difficulty: str
    topic: str
    features: str
    passageLength: int

# 프론트엔드에게 반환할 응답 데이터 형식
class PassageGenerateResponse(BaseModel):
    problem_id: int