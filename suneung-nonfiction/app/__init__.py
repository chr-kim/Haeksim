# app/__init__.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.generate import router as generate_router   # /api/v1/items/generate
from .routers.items import router as items_router         # DB 버전
from .routers.auth import router as auth_router
from .routers.analysis import router as analysis_router
from app.routers.chat import router as chat_router
from app.routers.rag_similar import router as rag_router
from .routers import summary

def create_app() -> FastAPI:
    app = FastAPI(title="Reading QA API", version="1.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000",
                       "http://127.0.0.1:3000",],
        allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
    )
    app.include_router(auth_router,    prefix="")         # /auth/*
    app.include_router(generate_router, prefix="/api/v1") # /api/v1/items/generate
    app.include_router(items_router,   prefix="/api/v1")  # /api/v1/items, /submit
    app.include_router(analysis_router)
    app.include_router(chat_router)
    app.include_router(rag_router)
    app.include_router(summary.router)
    return app

app = create_app()
