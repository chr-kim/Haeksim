# backend/models/user.py
from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData
from sqlalchemy.sql import func
from core.db import metadata  # db.py는 바로 다음에 만듭니다.

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, unique=True, index=True, nullable=False),
    Column("email", String, unique=True, index=True, nullable=False),
    Column("hashed_password", String, nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)