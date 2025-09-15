from pydantic import BaseModel, EmailStr
from typing import List

class SignUpReq(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginReq(BaseModel):
    username: str
    password: str

class TokenRes(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SubmissionRes(BaseModel):
    id: int
    item_id: str
    choice_index: int
    correct: bool
    explain: str
    evidence_sent_ids: List[int]
    created_at: str

class MeRes(BaseModel):
    id: int
    username: str
    email: EmailStr
    submissions: List[SubmissionRes] = []
