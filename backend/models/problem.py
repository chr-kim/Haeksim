# backend/models/problem.py
from sqlalchemy import Table, Column, Integer, String, Text, MetaData
from core.db import metadata

problems = Table(
    "problems",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("passage", Text, nullable=False),         # 지문
    Column("question", Text, nullable=False),        # 문제
    Column("choices", String, nullable=False),       # 선택지 (JSON 문자열로 저장)
    Column("answer", Integer, nullable=False),       # 정답 ID
    Column("explanation", Text, nullable=False),     # 해설
)