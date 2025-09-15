from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = "change-me-in-env"
ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MIN = 60 * 24

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)

def verify_password(pw: str, pw_hash: str) -> bool:
    return pwd_ctx.verify(pw, pw_hash)

def create_access_token(sub: str, minutes: int = ACCESS_TOKEN_EXPIRE_MIN) -> str:
    payload = {"sub": sub, "exp": datetime.utcnow() + timedelta(minutes=minutes)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGO)

def decode_access_token(token: str) -> str | None:
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        return data.get("sub")
    except JWTError:
        return None
