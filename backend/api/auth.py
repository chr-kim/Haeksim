# backend/api/auth.py
from fastapi import APIRouter, HTTPException, status
from schemas.user import UserCreate, UserPublic
from services import user_service

router = APIRouter()

@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate):
    user = await user_service.create_new_user(user=user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 사용자 이름 또는 이메일입니다.",
        )
    return user