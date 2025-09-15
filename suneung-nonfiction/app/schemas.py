from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# /items/generate 요청
class GenerateReq(BaseModel):
    mode: str
    difficulty: str = Field(..., description="기초|보통|어려움")
    topic: str = Field(..., description="과학기술|인문|사회|예술/문학|시사")
    target_chars: int = Field(..., ge=200, le=2000)

# 내부 저장용(정답 포함)
class ChoiceInternal(BaseModel):
    index: int
    text: str
    evidence_sent_ids: List[int]
    evidence_diag: Dict[str, Any] = {}
    verify_label: str
    verify_notes: str = ""
    is_correct: bool

class ItemInternal(BaseModel):
    id: str
    db_key: str
    title: str
    question: str
    generated_passage: str
    sentences: List[Dict[str, Any]]
    quality: Dict[str, Any]
    rag_eval: Dict[str, Any] = {}
    topic: str
    difficulty: str

# 프런트 공개용(정답 제외)
class ChoicePublic(BaseModel):
    index: int
    text: str

class ItemPublic(BaseModel):
    id: str
    title: str
    question: str
    generated_passage: str
    sentences: List[Dict[str, Any]]
    quality: Dict[str, Any]
    rag_eval: Dict[str, Any] = {}
    topic: str
    difficulty: str
    choices: List[ChoicePublic]

# 저장/제출
class SaveItemReq(BaseModel):
    payload: Dict[str, Any]
    tags: List[str] = []
    author: Optional[str] = None

class SubmitReq(BaseModel):
    choice_index: int

class SubmitRes(BaseModel):
    correct: bool
    explain: str
    evidence_sent_ids: List[int]
