# app/repo.py
import json, random
from typing import Optional

NF = "data/out/nonfiction.jsonl"

def sample_nonfiction(grade_level: Optional[str] = None, topic: Optional[str] = None):
    """
    grade_level: "고1" | "고2" | "고3" (없으면 전체)
    topic: "과학기술" | "인문" | "사회" | "예술/문학" | "시사" (없으면 전체)
    """
    with open(NF, encoding="utf-8") as f:
        rows = [json.loads(x) for x in f]

    def ok(rec):
        if grade_level and str(rec.get("grade_level")) != grade_level:
            return False
        if topic and str(rec.get("topic")) != topic:
            return False
        return True

    pool = [r for r in rows if ok(r)]
    if not pool:
        # 필터 결과 없으면 전체에서라도 하나
        pool = rows
    return random.choice(pool) if pool else None
