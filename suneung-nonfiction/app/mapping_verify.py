# app/mapping_verify.py
from typing import List, Dict, Any
from .openai_client import call_json

def verify_with_evidence(sentences: List[Dict], choice_text: str, evidence_ids: List[int], must: str):
    sent_map = {int(s["id"]): s["text"] for s in sentences}
    evidence = {int(sid): sent_map.get(int(sid), "") for sid in evidence_ids or []}
    prompt = f"""
역할: 국어 비문학 선지 검증자. JSON만 출력.
지정된 근거 문장들(evidence)만 보고, 선지의 주장과의 관계를 엄격히 판정하라.
암시/추론 금지. 근거에 포함되지 않은 문장, 외부 지식 사용 금지.

[선지]: {choice_text}
[근거 문장]: {evidence}

라벨:
- "support": 근거 문장이 선지 주장을 직접 뒷받침
- "contradict": 근거 문장이 선지 주장과 직접 모순
- "weak": 부분 일치/확장/추정
- "no_evidence": 근거로 연결 불가

JSON: {{"label":"support|contradict|weak|no_evidence","notes":"간결 사유"}}
"""
    out = call_json(prompt) or {}
    label = out.get("label") or "no_evidence"
    notes = out.get("notes") or ""
    return {"label": label, "notes": notes}

def verify_choices_batch(sentences: List[Dict], items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    items: [{"idx":0,"text":"...","evidence_ids":[2,3],"must":"support"}, ...]
    반환: [{"idx":0,"label":"support","notes":"..."}, ...] (idx 기준 매칭)
    """
    sent_map = {int(s["id"]): s["text"] for s in sentences}
    pack = []
    for it in items:
        ev = {int(sid): sent_map.get(int(sid), "") for sid in (it.get("evidence_ids") or [])}
        pack.append({
            "idx": it.get("idx"),
            "must": it.get("must"),
            "choice": it.get("text",""),
            "evidence": ev
        })

    prompt = f"""
역할: 한국어 수능 비문학 선지 검증자. JSON 배열만 출력.
아래 각 항목에 대해 evidence만 근거로, 선지 텍스트와의 관계를 판정한다.
암시/추론/외부지식 사용 금지.

라벨:
- "support": evidence가 선지 주장 직접 뒷받침
- "contradict": evidence가 선지 주장과 직접 모순
- "weak": 부분 일치/확장/추정
- "no_evidence": 연결 불가

입력 배열:
{pack}

출력(JSON 배열):
[{{"idx":0,"label":"support|contradict|weak|no_evidence","notes":"간결 사유"}}, ...]
"""
    out = call_json(prompt) or {}
    # 모델이 dict로 감싸는 경우 대비
    arr = out if isinstance(out, list) else out.get("items") or out.get("results") or []
    norm = []
    for r in arr:
        norm.append({
            "idx": r.get("idx"),
            "label": r.get("label") or "no_evidence",
            "notes": r.get("notes") or ""
        })
    return norm
