# backend/schemas/user.py
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserPublic(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True # SQLAlchemy 모델과 호환되도록 설정

class Token(BaseModel):
    access_token: str
    token_type: str