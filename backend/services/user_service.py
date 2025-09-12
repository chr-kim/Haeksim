# backend/services/user_service.py
from sqlalchemy.future import select
from core.db import database
from models.user import users
from schemas.user import UserCreate
from auth.security import get_password_hash, verify_password # ✨ 1. verify_password를 import 목록에 추가합니다.

async def create_new_user(user: UserCreate):
    """
    새로운 사용자를 생성합니다. (기존 함수)
    """
    # 중복 확인
    query = select(users).where((users.c.username == user.username) | (users.c.email == user.email))
    existing_user = await database.fetch_one(query)
    if existing_user:
        return None

    # 비밀번호 해싱 및 사용자 생성
    hashed_password = get_password_hash(user.password)
    query = users.insert().values(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    last_record_id = await database.execute(query)
    return {**user.dict(), "id": last_record_id}

# ✨ 2. 아래의 사용자 인증 함수 전체를 추가합니다.
async def authenticate_user(username: str, password: str):
    """
    사용자 이름과 비밀번호로 사용자를 인증합니다.
    성공 시 사용자 정보를, 실패 시 None을 반환합니다.
    """
    query = select(users).where(users.c.username == username)
    user = await database.fetch_one(query)
    
    # 사용자가 존재하지 않거나 비밀번호가 틀리면 None을 반환합니다.
    if not user or not verify_password(password, user.hashed_password):
        return None
        
    # 인증 성공 시, 사용자 정보를 반환합니다.
    return user