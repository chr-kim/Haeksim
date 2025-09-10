from pydantic import BaseModel, Field
from typing import List

class EvaluationRequest(BaseModel):
    problem_id: int
    user_answer_id: int
    user_reasoning: str = Field(..., max_length=1000)

class EvaluationFeedback(BaseModel):
    criteria: str  # 예: "이해의 정확성"
    score: int = Field(..., ge=0, le=100)
    comment: str

class EvaluationResponse(BaseModel):
    total_score: int
    feedbacks: List[EvaluationFeedback]
