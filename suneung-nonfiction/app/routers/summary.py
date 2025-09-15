# app/routers/summary.py
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Literal

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from openai import OpenAI
from sqlalchemy.orm import Session
from uuid import uuid4

from ..db_sql import get_db, Base, engine
from ..models import Summary, User
from .auth import get_current_user  # 현재 로그인 사용자 확인용

router = APIRouter(prefix="/api/v1/summary", tags=["summary"])

# 새 모델 반영(여러 번 호출돼도 안전)
Base.metadata.create_all(bind=engine)

# ---------- Schemas ----------

class ScorePayload(BaseModel):
    coverage: int = Field(ge=0, le=100, default=0)
    correctness: int = Field(ge=0, le=100, default=0)
    coherence: int = Field(ge=0, le=100, default=0)
    language: int = Field(ge=0, le=100, default=0)
    overall: int = Field(ge=0, le=100, default=0)

class AnalyzeRequest(BaseModel):
    passage: str
    summary: str

class AnalyzeResponse(BaseModel):
    scores: ScorePayload
    summary_feedback: str
    missing_points: List[str] = Field(default_factory=list)
    hallucinations: List[str] = Field(default_factory=list)

class SaveRequest(BaseModel):
    title: str
    passage: str
    my_summary: str
    scores: ScorePayload
    pack_summary: Optional[str] = ""
    key_points: Optional[List[str]] = []
    evaluated_feedback: Optional[str] = ""

class SaveResponse(BaseModel):
    ok: bool
    id: str

class SavedSummary(BaseModel):
    id: str
    title: str
    passage: str
    my_summary: str
    scores: ScorePayload
    pack_summary: Optional[str] = ""
    key_points: List[str] = Field(default_factory=list)
    evaluated_feedback: Optional[str] = ""
    created_at: str

# --- Chat schemas ---
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    passage: str
    summary: str
    messages: List[ChatMessage] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str


# ---------- LLM helpers (평가/채팅) ----------

def _analysis_messages_ko(passage: str, summary: str):
    system = (
        "당신은 한국어 글쓰기 평가 전문가입니다. "
        "아래 루브릭에 따라 학생의 요약을 평가하세요. "
        "출력은 반드시 UTF-8의 순수 JSON만 반환하세요(설명/마크다운 금지). "
        "모든 점수는 0~100 사이의 정수입니다. "
        "종합 점수(overall)는 다음 공식을 따릅니다: "
        "overall = round(0.4*coverage + 0.3*correctness + 0.2*coherence + 0.1*language)"
    )
    user = f"""
[지문]
{passage}

[학생 요약]
{summary}

[평가 기준]
- coverage(40%): 본문 핵심 내용을 빠짐없이 담았는가
- correctness(30%): 사실 왜곡/과장 없이 본문 의미를 정확히 반영했는가
- coherence(20%): 문장/문단 흐름과 연결이 논리적인가
- language(10%): 간결성, 문법·표현의 자연스러움(한국어)

[출력(JSON 스키마)]
{{
  "scores": {{
    "coverage": 0,
    "correctness": 0,
    "coherence": 0,
    "language": 0,
    "overall": 0
  }},
  "summary_feedback": "학생에게 줄 짧은 한국어 피드백(2~4문장)",
  "missing_points": ["요약에서 빠진 핵심 포인트(있으면 1~3개)"],
  "hallucinations": ["본문에 없는 내용/과장(있으면 1~3개)"]
}}

주의:
- 점수는 반드시 0~100 정수.
- overall은 위 공식을 그대로 계산.
- JSON 외 텍스트를 절대 출력하지 말 것.
"""
    return system, user


def _clamp_int_0_100(x) -> int:
    try:
        v = float(x)
        if 0 <= v <= 1:
            v *= 100
        return max(0, min(100, int(round(v))))
    except Exception:
        return 0


def _call_llm_for_analysis(passage: str, summary: str) -> AnalyzeResponse:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)
    system, user = _analysis_messages_ko(passage, summary)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)

        s = data.get("scores", {}) or {}
        coverage = _clamp_int_0_100(s.get("coverage"))
        correctness = _clamp_int_0_100(s.get("correctness"))
        coherence = _clamp_int_0_100(s.get("coherence"))
        language = _clamp_int_0_100(s.get("language"))

        overall_raw = s.get("overall")
        overall = _clamp_int_0_100(overall_raw) if overall_raw is not None else 0
        calc_overall = int(round(0.4 * coverage + 0.3 * correctness + 0.2 * coherence + 0.1 * language))
        if overall != calc_overall:
            overall = calc_overall

        feedback = str(data.get("summary_feedback", "")).strip()
        missing_points = data.get("missing_points") or []
        hallucinations = data.get("hallucinations") or []

        return AnalyzeResponse(
            scores=ScorePayload(
                coverage=coverage,
                correctness=correctness,
                coherence=coherence,
                language=language,
                overall=overall,
            ),
            summary_feedback=feedback or "평가 결과가 비어 있습니다.",
            missing_points=list(missing_points),
            hallucinations=list(hallucinations),
        )
    except Exception as e:
        safe_len = min(len(summary), 500)
        approx_overall = int(round(60 + (safe_len / 500) * 40))
        return AnalyzeResponse(
            scores=ScorePayload(overall=approx_overall),
            summary_feedback=f"샘플 평가(폴백): LLM 오류로 임시 점수를 표시합니다. ({e})",
            missing_points=[],
            hallucinations=[],
        )


def _build_tutor_messages_ko(passage: str, summary: str, turns: List[ChatMessage]):
    system = (
        "당신은 친절하고 정확한 한국어 학습 코치입니다. "
        "답변은 반드시 한국어로만 하세요. "
        "항상 아래에 제공된 지문과 학생 요약을 근거로 답하세요. "
        "지문과 무관한 질문이면 해당 맥락 안에서만 답할 수 있음을 정중히 알리고, "
        "질문을 지문과 연결하는 방법을 간단히 제안하세요. "
        "답변은 2~4문장의 짧은 단락을 선호하고, 필요할 때 지문의 직접 인용 또는 바꿔 말하기를 사용하세요."
    )

    context = (
        f"[지문]\n{passage}\n\n"
        f"[학생 요약]\n{summary}\n\n"
        "위 맥락만 사용해 답하세요."
    )

    msgs: List[Dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "system", "content": context},
    ]
    for m in turns:
        role = "user" if m.role == "user" else "assistant"
        msgs.append({"role": role, "content": m.content})
    return msgs


def _call_llm_chat(passage: str, summary: str, messages: List[ChatMessage]) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)
    msgs = _build_tutor_messages_ko(passage, summary, messages)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=msgs,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"죄송해요. 답변 생성 중 오류가 발생했어요. 잠시 후 다시 시도해 주세요. (오류: {e})"


# ---------- Routes ----------

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_summary(body: AnalyzeRequest):
    """지문/요약을 LLM으로 평가하여 점수/피드백 반환."""
    return _call_llm_for_analysis(body.passage, body.summary)


@router.post("/save", response_model=SaveResponse)
def save_summary_result(
    body: SaveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),   # 현재 로그인 사용자
):
    """
    결과물 저장(DB). 사용자별로 구분 저장됩니다.
    이전 파일 저장(jsonl) 방식은 제거.
    """
    rec_id = uuid4().hex
    row = Summary(
        id=rec_id,
        user_id=user.id,
        title=body.title,
        passage=body.passage,
        my_summary=body.my_summary,
        scores_json=json.dumps(body.scores.model_dump(), ensure_ascii=False),
        pack_summary=body.pack_summary or "",
        key_points_json=json.dumps(body.key_points or [], ensure_ascii=False),
        evaluated_feedback=body.evaluated_feedback or "",
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    return SaveResponse(ok=True, id=rec_id)


@router.get("/list", response_model=List[SavedSummary])
def list_my_summaries(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    내 요약 결과 목록(최신순)
    """
    q = (db.query(Summary)
           .filter(Summary.user_id == user.id)
           .order_by(Summary.created_at.desc())
           .offset(offset).limit(limit))
    rows = q.all()
    out: List[SavedSummary] = []
    for r in rows:
        scores = json.loads(r.scores_json or "{}")
        kps = json.loads(r.key_points_json or "[]")
        out.append(SavedSummary(
            id=r.id,
            title=r.title,
            passage=r.passage,
            my_summary=r.my_summary,
            scores=ScorePayload(**scores) if isinstance(scores, dict) else ScorePayload(),
            pack_summary=r.pack_summary or "",
            key_points=list(kps) if isinstance(kps, list) else [],
            evaluated_feedback=r.evaluated_feedback or "",
            created_at=(r.created_at or datetime.utcnow()).isoformat(),
        ))
    return out


@router.get("/{summary_id}", response_model=SavedSummary)
def get_my_summary(
    summary_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    내 요약 결과 1건 상세
    """
    r = (db.query(Summary)
           .filter(Summary.id == summary_id, Summary.user_id == user.id)
           .first())
    if not r:
        raise HTTPException(status_code=404, detail="summary not found")

    scores = json.loads(r.scores_json or "{}")
    kps = json.loads(r.key_points_json or "[]")
    return SavedSummary(
        id=r.id,
        title=r.title,
        passage=r.passage,
        my_summary=r.my_summary,
        scores=ScorePayload(**scores) if isinstance(scores, dict) else ScorePayload(),
        pack_summary=r.pack_summary or "",
        key_points=list(kps) if isinstance(kps, list) else [],
        evaluated_feedback=r.evaluated_feedback or "",
        created_at=(r.created_at or datetime.utcnow()).isoformat(),
    )


@router.post("/chat", response_model=ChatResponse)
def chat_with_tutor(body: ChatRequest):
    """
    지문 + 내 요약을 맥락으로 대화형 튜터 답변 생성.
    프런트는 누적 messages를 계속 보내면 대화가 이어집니다.
    """
    reply = _call_llm_chat(body.passage, body.summary, body.messages)
    return ChatResponse(reply=reply)
