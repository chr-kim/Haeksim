from fastapi import APIRouter
from typing import Dict, Any
from ..schemas import GenerateReq
# 아래 유틸/서비스는 현 main.py와 동일 import 경로 유지
from ..repo import sample_nonfiction
from ..openai_client import llm_generate_with_evidence, llm_quality, call_json, embed_texts
from ..mapping_verify import verify_with_evidence
import re
import hashlib
import unicodedata
# 👉 기존 app/main.py에 있던 상수/유틸 일부를 이 파일로 복사
# (DIFF_TO_GRADE, SIM_THRESHOLD, trim_evidence_by_similarity 등)

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import math
from app.routers import rag_similar

DIFF_TO_GRADE = {"기초": "고1", "보통": "고2", "어려움": "고3"}

MAX_REPAIR_ROUNDS = 2
MAX_REGENERATE   = 1

USE_EMBED_RERANK = True
SIM_THRESHOLD    = 0.22

def rewrite_choice_with_evidence(passage_sentences: List[Dict[str,str]], choice: Dict[str,Any], must: str) -> str:
    sents = {s["id"]: s["text"] for s in passage_sentences}
    evidence = {sid: sents.get(sid,"") for sid in choice.get("evidence_sent_ids", [])}
    prompt = f"""
역할: 국어 비문학 선지 교정기. JSON만.
요구: 아래 [근거 문장]에 직접 연결되도록 선지 텍스트를 최소 수정하라.
- 목표 판정: {must}
- 새로운 사실/용어 추가 금지, 근거 문장의 내용/관계를 명확히 반영
출력: {{"text":"..."}}

[근거 문장]: {evidence}
[원 선지]: {choice.get("text","")}
"""
    out = call_json(prompt) or {}
    new_text = out.get("text") or choice.get("text","")
    return new_text.strip()

def make_db_key(title: str, passage_text: str) -> str:
    """
    - 한글/영문/숫자/하이픈만 허용, 공백은 하이픈으로
    - 소문자화(영문만), 양끝 하이픈 정리
    - 본문 sha1 앞 8글자를 suffix로 붙여 충돌 최소화
    """
    if not title:
        title = (passage_text[:20] or "untitled").strip()

    t = unicodedata.normalize("NFKC", title)
    t = re.sub(r"\s+", "-", t)                 # 공백 -> -
    t = re.sub(r"[^가-힣A-Za-z0-9\-]", "", t)  # 허용 외 제거
    t = re.sub(r"-{2,}", "-", t).strip("-")    # 중복/양끝 -
    t = t.lower()

    h = hashlib.sha1((passage_text or "").encode("utf-8")).hexdigest()[:8]
    return f"{t}-{h}" if t else f"untitled-{h}"

def trim_evidence_by_overlap(choice_text: str, sentences: List[Dict[str, str]], ev_ids: List[int], max_keep: int = 2) -> List[int]:
    valid_ids = {int(s["id"]) for s in sentences}
    ev_ids = [int(i) for i in ev_ids if int(i) in valid_ids]
    if not ev_ids: return []
    toks = set(re.findall(r"[가-힣A-Za-z0-9]+", choice_text or ""))
    by_id = {int(s["id"]): s["text"] for s in sentences}
    scored = []
    for sid in ev_ids:
        st = by_id.get(sid, "")
        score = sum(1 for t in toks if t and t in st)
        scored.append((score, sid))
    picked = [sid for score, sid in sorted(scored, key=lambda x: x[0], reverse=True) if score > 0]
    if not picked: return ev_ids[:1]
    return picked[:max_keep]

# [EMBED] 코사인
def _cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)) or 1e-9
    nb = math.sqrt(sum(y*y for y in b)) or 1e-9
    return dot / (na * nb)

def trim_evidence_by_similarity(choice_text: str, sentences: List[Dict[str, str]], ev_ids: List[int], max_keep: int = 2, min_sim: float = SIM_THRESHOLD):
    """
    1) choice_text + 후보 evidence 문장들 임베딩
    2) 코사인 유사도 내림차순 상위 max_keep 선택
    3) min_sim 미만은 탈락(전부 미달이면 최고 1개 폴백)
    반환: (선택 evidence id 리스트, 진단 dict)
    """
    id2sent = {int(s["id"]): s["text"] for s in sentences}
    ev_ids = [int(i) for i in ev_ids if int(i) in id2sent]
    if not ev_ids:
        return [], {"method":"embed", "picked":[], "sims":{}}

    texts = [choice_text] + [id2sent[i] for i in ev_ids]
    embs = embed_texts(texts)

    if not embs or len(embs) != len(texts):  # 임베딩 실패 → overlap 폴백
        picked = trim_evidence_by_overlap(choice_text, sentences, ev_ids, max_keep=max_keep)
        return picked, {"method":"overlap_fallback", "picked":picked, "sims":{}}

    q = embs[0]
    sims = {}
    for idx, sid in enumerate(ev_ids, start=1):
        sims[sid] = _cosine(q, embs[idx])

    ranked = [sid for sid, s in sorted(sims.items(), key=lambda x: x[1], reverse=True) if s >= min_sim]
    if not ranked:
        ranked = [max(sims.items(), key=lambda x: x[1])[0]]  # 전부 미달 시 최고 1개

    picked = ranked[:max_keep]
    return picked, {"method":"embed", "picked":picked, "sims":{str(k): round(v,4) for k,v in sims.items()}}


router = APIRouter(tags=["items"])

# ===== 여기에 app/main.py의 generate() 본문을 그대로 옮겨 붙이세요 =====
# 엔드포인트 경로만 바꿉니다: /api/v1/items/generate
@router.post("/items/generate")
def generate(req: GenerateReq):
    # 0) 난이도→학년/주제 필터로 베이스 지문 샘플
    base = sample_nonfiction(
        grade_level=DIFF_TO_GRADE.get(req.difficulty),
        topic=req.topic
    )
    key_points = "; ".join([s["text"] for s in base["sentences"][:4]]) if base else ""

    # 1) 생성(근거 내장)
    gen = llm_generate_with_evidence(
        req.mode, topic=req.topic, difficulty=req.difficulty, target_chars=req.target_chars
    )
    passage_sentences = gen.get("passage_sentences", [])
    # 방어: id 보정
    for i, s in enumerate(passage_sentences):
        s["id"] = int(s.get("id") or (i+1))
        s["text"] = str(s.get("text","")).strip()
    passage_text = " ".join(s["text"] for s in passage_sentences if s["text"])

    # ★ 제목 및 DB Key
    title = (gen.get("title") or "").strip()
    db_key = make_db_key(title, passage_text)
    question = (gen.get("question") or "위 글의 내용으로 적절한 것을 고르시오.").strip()

    result = {
        "title": title,
        "question": question,   
        "db_key": db_key,
        "generated_passage": passage_text,
        "sentences": passage_sentences,
        "quality": llm_quality(passage_text, req.topic, key_points),
        "repairs": [],
        "regen_count": 0,
        "difficulty": req.difficulty,
        "topic": req.topic,
        "target_chars": req.target_chars,
        # ★ 여기 추가
        "base_group_id": base.get("group_id") if base else None
    }
    if req.mode.upper() != "B":
        return result

    choices = gen.get("choices", []) or []

    def accept_all(_choices):
        verified_map = {}
        sent_id_set = {int(s["id"]) for s in passage_sentences}

        # [RAGAS-like] 누적용
        rag_scores = []
        prec_cnt_total, prec_den_total = 0, 0
        rec_cnt_total,  rec_den_total  = 0, 0
        faith_err_cnt = 0

        for idx, c in enumerate(_choices):
            original_ev = list(c.get("evidence_sent_ids") or [])  # 원래 LLM가 지정한 근거 세트
            ev = [int(x) for x in original_ev if int(x) in sent_id_set]

            # 근거 정제(임베딩 리랭크 or overlap)
            if USE_EMBED_RERANK:
                ev, diag = trim_evidence_by_similarity(c.get("text",""), passage_sentences, ev, max_keep=2, min_sim=SIM_THRESHOLD)
            else:
                ev = trim_evidence_by_overlap(c.get("text",""), passage_sentences, ev, max_keep=2)
                diag = {"method":"overlap", "picked":ev, "sims":{}}

            if not ev:
                return False, idx, "empty evidence", verified_map

            c["evidence_sent_ids"] = ev
            c["evidence_diag"] = diag

            # 근거 강도(평균/최솟값)
            sim_vals = [diag.get("sims",{}).get(str(i)) for i in ev]
            sim_vals = [v for v in sim_vals if isinstance(v, (int,float))]
            evidence_strength = round(sum(sim_vals)/len(sim_vals),4) if sim_vals else 0.0
            evidence_min = round(min(sim_vals),4) if sim_vals else 0.0

            # 검증
            must = "support" if c.get("is_correct") else "contradict"
            v = verify_with_evidence(passage_sentences, c.get("text",""), ev, must)
            c["verify"] = v
            label = v.get("label")

            # [RAGAS-like] context_precision / recall / faithfulness_error
            # - precision: 최종 선택 ev 중 유사도 임계 이상 비율
            good_ev = [i for i in ev if isinstance(diag.get("sims",{}).get(str(i)), (int,float)) and diag["sims"][str(i)] >= SIM_THRESHOLD]
            prec_cnt_total += len(good_ev)
            prec_den_total += max(1, len(ev))  # 0분모 방지

            # - recall: 원래 evidence_sent_ids 중 최종 남은 비율
            orig_ev_clean = [int(x) for x in original_ev if int(x) in sent_id_set]
            inter = set(orig_ev_clean).intersection(set(ev))
            rec_cnt_total += len(inter)
            rec_den_total += max(1, len(orig_ev_clean))

            # - faithfulness error: 목표 라벨 불일치 또는 weak/no_evidence
            if label != must or label in ("weak", "no_evidence"):
                faith_err_cnt += 1

            verified_map[idx] = {
                "final_sent_ids": ev,
                "label": label,
                "notes": v.get("notes",""),
                "evidence_strength": evidence_strength,
                "evidence_min": evidence_min,
                "diag": diag,
                # 지문/선지 단위의 소지표(참고용)
                "context_precision_local": round(len(good_ev) / max(1, len(ev)), 3),
                "context_recall_local": round(len(inter) / max(1, len(orig_ev_clean)), 3),
            }

            rag_scores.append({
                "idx": idx,
                "must": must,
                "label_ok": (label == must),
                "evidence_strength": evidence_strength,
                "evidence_min": evidence_min
            })

            if label != must:
                return False, idx, f"need {must}, got {label}", verified_map

        # 세트 요약 지표
        acc = sum(1 for r in rag_scores if r["label_ok"]) / max(1,len(rag_scores))
        avg_strength = sum(r["evidence_strength"] for r in rag_scores)/max(1,len(rag_scores))

        context_precision = round(prec_cnt_total / max(1, prec_den_total), 3)
        context_recall    = round(rec_cnt_total  / max(1, rec_den_total),  3)
        faithfulness_error_rate = round(faith_err_cnt / max(1, len(_choices)), 3)

        result_summary = {
            "label_accuracy": round(acc,3),
            "avg_evidence_strength": round(avg_strength,4),
            "context_precision": context_precision,
            "context_recall": context_recall,
            "faithfulness_error_rate": faithfulness_error_rate
        }
        return True, None, result_summary, verified_map

    ok, bad_idx, reason_or_summary, verified_map = accept_all(choices)
    repair_round, regen = 0, 0

    while not ok and repair_round < MAX_REPAIR_ROUNDS:
        must = "support" if choices[bad_idx].get("is_correct") else "contradict"
        before = choices[bad_idx].get("text","")
        choices[bad_idx]["text"] = rewrite_choice_with_evidence(passage_sentences, choices[bad_idx], must)
        result["repairs"].append({
            "index": bad_idx, "must": must,
            "before": before, "after": choices[bad_idx]["text"],
            "reason": reason_or_summary
        })

        ok, bad_idx, reason_or_summary, verified_map = accept_all(choices)
        repair_round += 1

        if not ok and repair_round >= MAX_REPAIR_ROUNDS and regen < MAX_REGENERATE:
            # 세트 재생성
            regen += 1
            result["regen_count"] = regen
            gen = llm_generate_with_evidence(req.mode, topic=req.topic, difficulty=req.difficulty, target_chars=req.target_chars)
            passage_sentences = gen.get("passage_sentences", [])
            for i, s in enumerate(passage_sentences):
                s["id"] = int(s.get("id") or (i+1))
                s["text"] = str(s.get("text","")).strip()
            passage_text = " ".join(s["text"] for s in passage_sentences if s["text"])
            result["generated_passage"] = passage_text
            result["sentences"] = passage_sentences
            choices = gen.get("choices", []) or []
            repair_round = 0
            ok, bad_idx, reason_or_summary, verified_map = accept_all(choices)

    result["choices"] = choices
    result["verified_mapping"] = verified_map
    # [RAGAS-like] 세트 요약 지표 반영
    if isinstance(reason_or_summary, dict):
        result["rag_eval"] = {
            "label_accuracy": reason_or_summary.get("label_accuracy"),
            "avg_evidence_strength": reason_or_summary.get("avg_evidence_strength"),
            "context_precision": reason_or_summary.get("context_precision"),
            "context_recall": reason_or_summary.get("context_recall"),
            "faithfulness_error_rate": reason_or_summary.get("faithfulness_error_rate"),
            "sim_threshold": SIM_THRESHOLD,
            "method": "embed_rerank" if USE_EMBED_RERANK else "overlap"
        }
    else:
        result["rag_eval"] = {"method": "embed_rerank" if USE_EMBED_RERANK else "overlap"}

    return result