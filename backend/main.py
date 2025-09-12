# backend/main.py
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api import auth, evaluation, passage  # ✨ 1. 평가(evaluation) API 라우터를 새로 import 합니다.
from core.db import database, engine, metadata
import logging
from models import user, problem #  models/problem.py를 import하여 테이블을 인식

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✨ 2. 데이터베이스 테이블 생성
# 애플리케이션 시작 전에 명시적으로 테이블을 생성합니다.
metadata.create_all(bind=engine)

# ✨ 2. models/problem.py를 import하여 테이블을 인식시킵니다.

metadata.create_all(bind=engine)

# FastAPI 앱 생성
app = FastAPI(title="Welcome to Haeksim Project API!")

# ✨ [추가할 디버깅 코드] 422 오류의 상세 내용을 로그로 출력합니다.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 오류의 상세 내용을 터미널에 출력합니다.
    logging.error(f"Validation error for request to {request.url}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 서비스에서는 프론트엔드 주소만 허용해야 합니다.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ✨ passage 라우터를 앱에 포함시킵니다.
app.include_router(passage.router, prefix="/passages", tags=["Passage Generation"])

# --- 루트 엔드포인트 ---
@app.get("/")
def read_root():
    return {"message": "Welcome to Haeksim API"}