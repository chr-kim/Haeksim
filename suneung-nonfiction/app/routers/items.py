from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import json
from uuid import uuid4            
from ..db_sql import get_db
from ..models import Item, Choice, Submission, User
from ..schemas import SaveItemReq, SubmitReq, SubmitRes, ItemPublic
from .auth import get_current_user  # 인증 재사용

router = APIRouter(tags=["items"])

def _upsert_item(db: Session, payload: Dict[str, Any]) -> Item:
    item_id = payload.get("id") or payload.get("db_key") or f"item-{uuid4().hex}"
    it = db.get(Item, item_id)
    if not it:
        it = Item(id=item_id)
        db.add(it)
    it.db_key = payload.get("db_key")
    it.title = payload.get("title")
    it.question = payload.get("question","")
    it.generated_passage = payload.get("generated_passage","")
    it.sentences_json = json.dumps(payload.get("sentences", []), ensure_ascii=False)
    it.quality_json = json.dumps(payload.get("quality", {}), ensure_ascii=False)
    it.rag_eval_json = json.dumps(payload.get("rag_eval", {}), ensure_ascii=False)
    it.topic = payload.get("topic","")
    it.difficulty = payload.get("difficulty","")
    return it

@router.post("/items", response_model=Dict[str, str])
def save_item(req: SaveItemReq, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = req.payload
    it = _upsert_item(db, p)

    # 보기 재생성
    db.query(Choice).filter(Choice.item_id == it.id).delete()
    for idx, c in enumerate(p.get("choices", [])):
        db.add(Choice(
            item_id=it.id, index=idx, text=c.get("text", ""),
            evidence_sent_ids_json=json.dumps(c.get("evidence_sent_ids", []), ensure_ascii=False),
            evidence_diag_json=json.dumps(c.get("evidence_diag", {}), ensure_ascii=False),
            verify_label=(c.get("verify", {}) or {}).get("label"),
            verify_notes=(c.get("verify", {}) or {}).get("notes", ""),
            is_correct=bool(c.get("is_correct", False)),
        ))
    db.commit()
    return {"item_id": it.id}

@router.get("/items", response_model=List[ItemPublic])
def list_items(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    rows = (db.query(Item).order_by(Item.title.asc()).offset(offset).limit(limit).all())
    res: List[ItemPublic] = []
    for it in rows:
        chs = (db.query(Choice).filter(Choice.item_id == it.id)
               .order_by(Choice.index.asc()).all())
        res.append(ItemPublic(
            id=it.id, title=it.title, question=it.question,
            generated_passage=it.generated_passage,
            sentences=json.loads(it.sentences_json or "[]"),
            quality=json.loads(it.quality_json or "{}"),
            rag_eval=json.loads(it.rag_eval_json or "{}"),
            topic=it.topic, difficulty=it.difficulty,
            choices=[{"index": c.index, "text": c.text} for c in chs],
        ))
    return res

@router.post("/items/{item_id}/submit", response_model=SubmitRes)
def submit_item(item_id: str, req: SubmitReq,
                db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    it = db.get(Item, item_id)
    if not it:
        raise HTTPException(404, "item not found")
    chs = db.query(Choice).filter(Choice.item_id == item_id).all()
    correct_choice = next((c for c in chs if c.is_correct), None)
    correct_idx = correct_choice.index if correct_choice else None
    correct = (req.choice_index == correct_idx)
    explain = "선택 근거와 해설은 서버 생성 결과를 요약해 제공합니다."
    evidence_ids = []
    if correct_choice:
        evidence_ids = json.loads(correct_choice.evidence_sent_ids_json or "[]")
    db.add(Submission(
        user_id=user.id, item_id=item_id, choice_index=req.choice_index, correct=correct,
        explain=explain, evidence_sent_ids_json=json.dumps(evidence_ids, ensure_ascii=False)
    ))
    db.commit()
    return SubmitRes(correct=correct, explain=explain, evidence_sent_ids=evidence_ids)
