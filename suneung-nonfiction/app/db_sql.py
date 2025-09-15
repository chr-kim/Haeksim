# app/db_sql.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./app.db"  # 개발은 SQLite, 배포는 PostgreSQL 권장

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite만
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
