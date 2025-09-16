# app/routers/generate.py
from fastapi import APIRouter
from typing import Dict, Any, List, Tuple
from ..schemas import GenerateReq
from ..repo import sample_nonfiction
from ..openai_client import (
    llm_generate_passage, llm_generate_choices, llm_quality,
    call_json, embed_texts
)
from ..mapping_verify import verify_with_evidence
import re, hashlib, unicodedata, math, time, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..mapping_verify import verify_choices_batch

DIFF_TO_GRADE = {"기초": "고1", "보통": "고2", "어려움": "고3"}
MAX_REPAIR_ROUNDS = 2
MAX_REGENERATE   = 0   # ← 세트 전체 재생성은 기본 0으로 (부분 재생성 권장)
USE_EMBED_RERANK = True
SIM_THRESHOLD    = 0.22

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

def _now() -> float: return time.perf_counter()
def _elapsed(since: float) -> float: return round((_now() - since) * 1000.0, 1)  # ms
def _log_timing(tag: str, ms: float, extra: Dict[str, Any] | None = None):
    payload = {"tag": tag, "ms": ms}; 
    if extra: payload.update(extra)
    logger.info("[TIMING] %s", payload)

def make_db_key(title: str, passage_text: str) -> str:
    if not title: title = (passage_text[:20] or "untitled").strip()
    t = unicodedata.normalize("NFKC", title)
    t = re.sub(r"\s+", "-", t)
    t = re.sub(r"[^가-힣A-Za-z0-9\-]", "", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    t = t.lower()
    h = hashlib.sha1((passage_text or "").encode("utf-8")).hexdigest()[:8]
    return f"{t}-{h}" if t else f"untitled-{h}"

# ------------------------------
# 임베딩/유사도 유틸 (캐시 기반)
# ------------------------------
def _cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)) or 1e-9
    nb = math.sqrt(sum(y*y for y in b)) or 1e-9
    return dot / (na * nb)

def _batch_embed(texts: List[str]) -> Tuple[List[List[float]], float]:
    t0 = _now()
    embs = embed_texts(texts) or []
    return embs, _elapsed(t0)

def _ensure_choice_embeddings(choice_texts: Dict[int, str],
                              choice_embeds: Dict[int, List[float]],
                              timing: Dict[str, Any]) -> None:
    """choice_embeds에 없는 인덱스만 한 번에 배치 임베딩"""
    missing = [(i, txt) for i, txt in choice_texts.items() if i not in choice_embeds]
    if not missing: return
    texts = [txt for _, txt in missing]
    embs, ms = _batch_embed(texts)
    if embs and len(embs) == len(texts):
        for (i, _), v in zip(missing, embs):
            choice_embeds[i] = v
    timing["embed_ms_total"] += ms

def _embed_sentences_once(sentences: List[Dict[str, Any]], timing: Dict[str, Any]) -> Dict[int, List[float]]:
    id2text = {int(s["id"]): s["text"] for s in sentences}
    ids_sorted = sorted(id2text.keys())
    texts = [id2text[i] for i in ids_sorted]
    embs, ms = _batch_embed(texts)
    timing["embed_ms_total"] += ms
    if not embs or len(embs) != len(texts): return {}
    return {i: v for i, v in zip(ids_sorted, embs)}

def _rerank_evidence_by_similarity_cached(
    choice_vec: List[float],
    sent_vecs: Dict[int, List[float]],
    ev_ids: List[int],
    max_keep: int = 2,
    min_sim: float = SIM_THRESHOLD
):
    sims = {}
    for sid in ev_ids:
        v = sent_vecs.get(int(sid))
        if v: sims[int(sid)] = _cosine(choice_vec, v)
    ranked = [sid for sid, s in sorted(sims.items(), key=lambda x: x[1], reverse=True) if s >= min_sim]
    if not ranked and sims:
        ranked = [max(sims.items(), key=lambda x: x[1])[0]]
    return ranked[:max_keep], {str(k): round(v, 4) for k, v in sims.items()}

# ------------------------------
router = APIRouter(tags=["items"])

@router.post("/items/generate")
def generate(req: GenerateReq):
    _t0_total = _now()
    timing = {
        "sampling_ms": 0.0,
        "gen_passage_ms": 0.0,
        "gen_choices_ms": 0.0,
        "quality_ms": 0.0,
        "verify_ms_total": 0.0,
        "verify_ms_each": [],
        "embed_ms_total": 0.0,
        "rewrite_ms_total": 0.0,
        "regen_ms_total": 0.0,
        "repair_rounds": 0,
        "regen_count": 0,
        "api_calls": {
            "generate_passage": 0,
            "generate_choices": 0,
            "quality": 0,
            "verify": 0,
            "rewrite": 0,
            "embed": 0  # (배치 1~2회로 압축됨)
        }
    }

    # 0) 베이스 샘플
    t = _now()
    base = sample_nonfiction(
        grade_level=DIFF_TO_GRADE.get(req.difficulty),
        topic=req.topic
    )
    timing["sampling_ms"] = _elapsed(t)
    key_points = "; ".join([s["text"] for s in base["sentences"][:4]]) if base else ""
    base_context = {
        "group_id": base.get("group_id") if base else None,
        "sentences": base.get("sentences") if base else []
    }

    # 1) 지문 생성
    t = _now()
    gen_passage = llm_generate_passage(
        topic=req.topic, difficulty=req.difficulty,
        target_chars=req.target_chars, base_context=base_context
    )
    timing["gen_passage_ms"] = _elapsed(t)
    timing["api_calls"]["generate_passage"] += 1

    passage_sentences = gen_passage.get("passage_sentences", []) or []
    for i, s in enumerate(passage_sentences):
        s["id"] = int(s.get("id") or (i+1))
        s["text"] = str(s.get("text","")).strip()
    passage_text = " ".join(s["text"] for s in passage_sentences if s["text"])
    title = (gen_passage.get("title") or "").strip()
    question = (gen_passage.get("question") or "위 글의 내용으로 적절한 것을 고르시오.").strip()
    db_key = make_db_key(title, passage_text)

    # 2) (병렬) 선지 생성 & 품질 평가
    choices = []
    quality = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = []
        if req.mode.upper() == "B":
            def _gen_choices():
                tt = _now()
                out = llm_generate_choices(passage_sentences=passage_sentences)
                ms = _elapsed(tt)
                timing["gen_choices_ms"] = ms
                timing["api_calls"]["generate_choices"] += 1
                return out
            futures.append(("choices", ex.submit(_gen_choices)))

        def _run_quality():
            tt = _now()
            out = llm_quality(passage_text, req.topic, key_points)
            ms = _elapsed(tt)
            timing["quality_ms"] = ms
            timing["api_calls"]["quality"] += 1
            return out
        futures.append(("quality", ex.submit(_run_quality)))

        for name, fut in futures:
            out = fut.result()
            if name == "choices":
                choices = (out.get("choices") or [])
            else:
                quality = out

    result = {
        "title": title,
        "question": question,
        "db_key": db_key,
        "generated_passage": passage_text,
        "sentences": passage_sentences,
        "quality": quality,
        "repairs": [],
        "regen_count": 0,
        "difficulty": req.difficulty,
        "topic": req.topic,
        "target_chars": req.target_chars,
        "base_group_id": base.get("group_id") if base else None,
        "used_base_group_id": gen_passage.get("used_base_group_id"),
    }

    if req.mode.upper() != "B":
        timing["total_ms"] = _elapsed(_t0_total)
        result["timing"] = timing
        return result

    # 3) 임베딩 캐시 준비 (지문 전체 1회 / 선지 텍스트 배치)
    sentence_vecs = _embed_sentences_once(passage_sentences, timing)
    # 선택지 텍스트 사전화
    choice_texts = {i: (c.get("text") or "") for i, c in enumerate(choices)}
    choice_vecs: Dict[int, List[float]] = {}
    _ensure_choice_embeddings(choice_texts, choice_vecs, timing)  # 배치 1회

    sent_id_set = {int(s["id"]) for s in passage_sentences}

    def _accept_all(_choices: List[Dict[str, Any]]):
        verified_map = {}
        rag_scores = []
        prec_cnt_total = rec_cnt_total = faith_err_cnt = 0
        prec_den_total = rec_den_total = 0

        # (A) evidence 리랭크 (임베딩 캐시 활용) - 기존과 동일
        prepared_batch = []  # 배치 검증 입력을 모음
        for idx, c in enumerate(_choices):
            original_ev = list(c.get("evidence_sent_ids") or [])
            ev = [int(x) for x in original_ev if int(x) in sent_id_set]

            if USE_EMBED_RERANK:
                _ensure_choice_embeddings({idx: c.get("text","")}, choice_vecs, timing)
                ch_vec = choice_vecs.get(idx)
                if ch_vec and ev:
                    ranked, sims = _rerank_evidence_by_similarity_cached(ch_vec, sentence_vecs, ev, max_keep=2, min_sim=SIM_THRESHOLD)
                else:
                    ranked, sims = (ev[:1] if ev else []), {}
            else:
                ranked, sims = (ev[:2], {})

            if not ranked:
                return False, idx, "empty evidence", verified_map

            c["evidence_sent_ids"] = ranked
            c["evidence_diag"] = {"method":"embed_cached" if USE_EMBED_RERANK else "overlap", "picked": ranked, "sims": sims}

            must = "support" if c.get("is_correct") else "contradict"
            prepared_batch.append({"idx": idx, "text": c.get("text",""), "evidence_ids": ranked, "must": must})

        # (B) 배치 1회 검증
        t_verify = _now()
        batch_res = verify_choices_batch(passage_sentences, prepared_batch)
        timing["verify_ms_each"] = []  # 개별이 아닌 배치로 집계
        timing["verify_ms_total"] += _elapsed(t_verify)
        timing["api_calls"]["verify"] += 1

        # (C) 결과 반영 + 지표 집계
        idx2res = {r["idx"]: r for r in batch_res if r.get("idx") is not None}
        for idx, c in enumerate(_choices):
            r = idx2res.get(idx) or {"label":"no_evidence","notes":""}
            label = r["label"]; notes = r["notes"]
            ev_ids = c["evidence_diag"]["picked"]; sims = c["evidence_diag"]["sims"]
            must = "support" if c.get("is_correct") else "contradict"

            # 지표
            good_ev = [i for i in ev_ids if isinstance(sims.get(str(i)), (int,float)) and sims[str(i)] >= SIM_THRESHOLD]
            prec_cnt_total += len(good_ev); prec_den_total += max(1, len(ev_ids))
            inter = set(ev_ids).intersection(set(ev_ids))  # 원본=최종(여기서는 동일)
            rec_cnt_total += len(inter); rec_den_total += max(1, len(ev_ids))
            if label != must or label in ("weak","no_evidence"):
                faith_err_cnt += 1

            sim_vals = [sims.get(str(i)) for i in ev_ids if isinstance(sims.get(str(i)), (int,float))]
            evidence_strength = round(sum(sim_vals)/len(sim_vals),4) if sim_vals else 0.0
            evidence_min = round(min(sim_vals),4) if sim_vals else 0.0

            verified_map[idx] = {
                "final_sent_ids": ev_ids,
                "label": label,
                "notes": notes,
                "evidence_strength": evidence_strength,
                "evidence_min": evidence_min,
                "diag": {"method":"embed_cached" if USE_EMBED_RERANK else "overlap", "picked": ev_ids, "sims": sims},
                "context_precision_local": round(len(good_ev) / max(1, len(ev_ids)), 3),
                "context_recall_local": round(len(inter) / max(1, len(ev_ids)), 3),
            }
            rag_scores.append({
                "idx": idx, "must": must, "label_ok": (label == must),
                "evidence_strength": evidence_strength, "evidence_min": evidence_min
            })

        acc = sum(1 for r in rag_scores if r["label_ok"]) / max(1, len(rag_scores))
        avg_strength = sum(r["evidence_strength"] for r in rag_scores)/max(1,len(rag_scores))
        result_summary = {
            "label_accuracy": round(acc,3),
            "avg_evidence_strength": round(avg_strength,4),
            "context_precision": round(prec_cnt_total / max(1, prec_den_total), 3),
            "context_recall": round(rec_cnt_total  / max(1, rec_den_total),  3),
            "faithfulness_error_rate": round(faith_err_cnt / max(1, len(_choices)), 3)
        }
        return True, None, result_summary, verified_map

    # 첫 검증
    ok, bad_idx, reason_or_summary, verified_map = _accept_all(choices)
    repair_round = 0

    # 필요 시: 실패 선지만 교정 → 해당 선지 임베딩만 갱신 → 다시 전체 검증(병렬)
    while not ok and repair_round < MAX_REPAIR_ROUNDS:
        must = "support" if choices[bad_idx].get("is_correct") else "contradict"
        before = choices[bad_idx].get("text","")

        tloc = _now()
        # 선지 교정
        sents = {s["id"]: s["text"] for s in passage_sentences}
        evidence = {int(sid): sents.get(int(sid), "") for sid in (choices[bad_idx].get("evidence_sent_ids") or [])}
        prompt = f"""
역할: 국어 비문학 선지 교정기. JSON만.
요구: 아래 [근거 문장]에 직접 연결되도록 선지 텍스트를 최소 수정하라.
- 목표 판정: {must}
- 새로운 사실/용어 추가 금지, 근거 문장의 내용/관계를 명확히 반영
출력: {{"text":"..."}}

[근거 문장]: {evidence}
[원 선지]: {before}
"""
        out = call_json(prompt) or {}
        after_text = (out.get("text") or before).strip()
        choices[bad_idx]["text"] = after_text
        timing["rewrite_ms_total"] += _elapsed(tloc)
        timing["api_calls"]["rewrite"] += 1

        # 교정된 선지 임베딩만 갱신
        embs, ms = _batch_embed([after_text])
        timing["embed_ms_total"] += ms
        if embs: choice_vecs[bad_idx] = embs[0]

        result["repairs"].append({
            "index": bad_idx, "must": must,
            "before": before, "after": choices[bad_idx]["text"],
            "reason": reason_or_summary
        })
        repair_round += 1

        ok, bad_idx, reason_or_summary, verified_map = _accept_all(choices)

    result["choices"] = choices
    result["verified_mapping"] = verified_map
    timing["repair_rounds"] = repair_round
    timing["verify_ms_total"] = round(sum(timing["verify_ms_each"]), 1)

    # RAG-like 요약
    if isinstance(reason_or_summary, dict):
        result["rag_eval"] = {
            "label_accuracy": reason_or_summary.get("label_accuracy"),
            "avg_evidence_strength": reason_or_summary.get("avg_evidence_strength"),
            "context_precision": reason_or_summary.get("context_precision"),
            "context_recall": reason_or_summary.get("context_recall"),
            "faithfulness_error_rate": reason_or_summary.get("faithfulness_error_rate"),
            "sim_threshold": SIM_THRESHOLD,
            "method": "embed_cached" if USE_EMBED_RERANK else "overlap"
        }
    else:
        result["rag_eval"] = {"method": "embed_cached" if USE_EMBED_RERANK else "overlap"}

    timing["total_ms"] = _elapsed(_t0_total)
    result["timing"] = timing
    return result
