# app/mapping_verify.py
from typing import List, Dict
from .openai_client import call_json

def verify_with_evidence(sentences: List[Dict], choice_text: str, evidence_ids: List[int], must: str):
    """
    지정된 evidence 문장만 보고 선지와의 관계를 판정(지원/모순/약함/무증거).
    must: "support"|"contradict" (목표 판정; 여기서는 참고만 하고, 실제 label은 모델이 판단)
    """
    sent_map = {int(s["id"]): s["text"] for s in sentences}
    evidence = {sid: sent_map.get(sid, "") for sid in evidence_ids or []}

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

JSON:
{{"label":"support|contradict|weak|no_evidence","notes":"간결 사유"}}
"""
    out = call_json(prompt) or {}
    label = out.get("label") or "no_evidence"
    notes = out.get("notes") or ""
    return {"label": label, "notes": notes}
