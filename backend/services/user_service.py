# backend/services/user_service.py
from sqlalchemy.future import select
from core.db import database
from models.user import users
from schemas.user import UserCreate
from core.security import get_password_hash

async def create_new_user(user: UserCreate):
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