# backend/main.py
from fastapi import FastAPI
from api import auth, evaluation  # ✨ 1. 평가(evaluation) API 라우터를 새로 import 합니다.
from core.db import database, engine, metadata
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✨ 2. 데이터베이스 테이블 생성
# 애플리케이션 시작 전에 명시적으로 테이블을 생성합니다.
metadata.create_all(bind=engine)

# FastAPI 앱 생성
app = FastAPI(title="Haeksim Project API")

# --- 이벤트 핸들러: 애플리케이션의 생명주기 관리 ---
@app.on_event("startup")
async def startup():
    logger.info("🚀 Application startup...")
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    logger.info("👋 Application shutdown...")
    await database.disconnect()

# --- 라우터 포함: 각 기능별 API 엔드포인트 연결 ---
# ✨ 3. 각 라우터를 앱에 포함시킵니다.
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(evaluation.router, prefix="/evaluation", tags=["Evaluation"])

# --- 루트 엔드포인트 ---
@app.get("/")
def read_root():
    return {"message": "Welcome to Haeksim API"}