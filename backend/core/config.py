# backend/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# 데이터베이스 설정
DATABASE_URL = "sqlite:///./haeksim.db"

# API 키 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# JWT (로그인 토큰) 설정
SECRET_KEY = "your-very-secret-key"  # 실제 운영 시에는 외부에서 주입해야 합니다.
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30