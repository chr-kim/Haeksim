# backend/core/security.py

from passlib.context import CryptContext

# 비밀번호 해싱을 위한 암호화 방식을 설정합니다. bcrypt가 가장 널리 쓰입니다.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """입력된 비밀번호와 해시된 비밀번호를 비교하여 일치하는지 확인합니다."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """입력된 비밀번호를 해시 처리하여 반환합니다."""
    return pwd_context.hash(password)