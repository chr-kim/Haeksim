# backend/schemas/evaluation.py
from pydantic import BaseModel, Field
from typing import List

# 평가 요청 시 프론트엔드로부터 받을 데이터 형식
class EvaluationRequest(BaseModel):
    problem_id: int
    user_answer_id: int
    user_reasoning: str = Field(..., max_length=1000)

# 평가 후 프론트엔드에게 반환할 데이터 형식
class EvaluationFeedback(BaseModel):
    criteria: str
    score: int = Field(..., ge=0, le=100)
    comment: str

class EvaluationResponse(BaseModel):
    total_score: int
    feedbacks: List[EvaluationFeedback]