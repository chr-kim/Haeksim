from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Text, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from .db_sql import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submissions: Mapped[list["Submission"]] = relationship(back_populates="user")

class Item(Base):
    __tablename__ = "items"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # 기존 아이템 id 재사용
    db_key: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255))
    question: Mapped[str] = mapped_column(Text)
    generated_passage: Mapped[str] = mapped_column(Text)
    sentences_json: Mapped[str] = mapped_column(Text)
    quality_json: Mapped[Optional[str]] = mapped_column(Text)
    rag_eval_json: Mapped[Optional[str]] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(50))
    difficulty: Mapped[str] = mapped_column(String(20))
    choices: Mapped[list["Choice"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="item")

class Choice(Base):
    __tablename__ = "choices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[str] = mapped_column(String(64), ForeignKey("items.id", ondelete="CASCADE"), index=True)
    index: Mapped[int] = mapped_column(Integer)  # 0..n
    text: Mapped[str] = mapped_column(Text)
    evidence_sent_ids_json: Mapped[str] = mapped_column(Text)
    evidence_diag_json: Mapped[Optional[str]] = mapped_column(Text)
    verify_label: Mapped[Optional[str]] = mapped_column(String(32))
    verify_notes: Mapped[Optional[str]] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    item = relationship("Item", back_populates="choices")

class Summary(Base):
    __tablename__ = "summaries"
    id = Column(String, primary_key=True)                  # uuid 혹은 snowflake 문자열
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    passage = Column(Text, nullable=False)
    my_summary = Column(Text, nullable=False)
    scores_json = Column(Text, nullable=False, default="{}")        # {coverage,correctness,coherence,language,overall}
    pack_summary = Column(Text, nullable=True)                      # studyPack.summary
    key_points_json = Column(Text, nullable=False, default="[]")    # list[str]
    evaluated_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", backref="summaries")

class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[str] = mapped_column(String(64), ForeignKey("items.id", ondelete="CASCADE"), index=True)
    choice_index: Mapped[int] = mapped_column(Integer)
    correct: Mapped[bool] = mapped_column(Boolean)
    explain: Mapped[str] = mapped_column(Text)
    evidence_sent_ids_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="submissions")
    item = relationship("Item", back_populates="submissions")
