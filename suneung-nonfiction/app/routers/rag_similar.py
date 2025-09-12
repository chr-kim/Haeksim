# app/routers/rag_similar.py
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
import os, json, re, hashlib, unicodedata
import faiss
import numpy as np
from dotenv import load_dotenv
load_dotenv()

# ==== OpenAI (python v1 SDK) ====
from openai import OpenAI
OPENAI_MODEL_REWRITER = os.getenv("OPENAI_MODEL_REWRITER", "gpt-4o-mini")
OPENAI_MODEL_GENERATOR = os.getenv("OPENAI_MODEL_GENERATOR", "gpt-4o")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# A타입 품질 지표(기존 generate()와 동일 유틸 재사용)
from app.openai_client import llm_quality  # noqa

router = APIRouter(prefix="/rag", tags=["rag"])

# ====== 데이터/인덱스 경로 ======
INDEX_PATH = os.getenv("RAG_FAISS_INDEX_PATH", "data/faiss.index")
META_PATH  = os.getenv("RAG_METADATA_JSON_PATH", "data/metadata.jsonl")
EMB_DIM    = int(os.getenv("RAG_EMBED_DIM", "1536"))  # e.g., text-embedding-3-small

# ====== 상수 (AdvancedRAG 요지: 평가→리파인→멀티쿼리) ======
QUERY_PASS_THRESHOLD = 0.75   # 평가 overall 컷 (미달 시 개선안 사용)
MAX_REFINE_ROUNDS    = 1      # 리파인 라운드 (필요시 ↑)
MULTI_QUERY_N        = 3      # 총 쿼리 개수(개선안 + variants)
ENABLE_HYDE          = True   # HyDE(가설 지문) 쿼리 추가 여부

# ====== 임베딩 ======
def embed_texts(texts: List[str]) -> np.ndarray:
    resp = client.embeddings.create(model=OPENAI_EMBED_MODEL, input=texts)
    vecs = [np.array(d.embedding, dtype=np.float32) for d in resp.data]
    return np.vstack(vecs)

# ====== 메타 로딩 ======
def load_metadata(meta_path: str) -> List[Dict[str, Any]]:
    metas = []
    with open(meta_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                metas.append(json.loads(line))
    return metas

# ====== Lazy 리소스 ======
_faiss_index = None
_metadata = None
def get_index_and_meta() -> Tuple[faiss.Index, List[Dict[str, Any]]]:
    global _faiss_index, _metadata
    if _faiss_index is None:
        if not os.path.exists(INDEX_PATH):
            raise RuntimeError(f"FAISS index not found: {INDEX_PATH}")
        _faiss_index = faiss.read_index(INDEX_PATH)
        if _faiss_index.d != EMB_DIM:
            raise RuntimeError(f"Index dim { _faiss_index.d } != EMB_DIM { EMB_DIM }")
    if _metadata is None:
        if not os.path.exists(META_PATH):
            raise RuntimeError(f"Metadata not found: {META_PATH}")
        _metadata = load_metadata(META_PATH)
    return _faiss_index, _metadata

# ====== 스키마 (필수 필드만 유지) ======
class GenerateSimilarRequest(BaseModel):
    current_passage: str = Field(..., description="사용자가 방금 읽은 지문(원문)")
    difficulty_reason: str = Field(..., description="사용자가 느낀 어려움의 이유(예: 용어 난이도/논리 전개/예시 전환 속도)")
    exclude_group_ids: List[str] = Field(default_factory=list, description="다시 쓰지 말아야 할 group_id 목록(원 지문 포함)")
    top_k: int = Field(default=8, ge=1, le=50, description="검색 후보 수(필터 전)")
    context_top_k: int = Field(default=5, ge=1, le=50, description="LLM 컨텍스트로 넣을 문서 수")
    min_score: Optional[float] = Field(default=0.22, description="코사인 유사도 하한(0~1)")
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)

# ====== A타입 화면과 동일한 응답 구조 ======
class ATypeLikeResponse(BaseModel):
    title: str
    db_key: str
    generated_passage: str
    sentences: List[Dict[str, Any]]
    quality: Dict[str, Any]
    repairs: List[Any]
    regen_count: int
    topic: Optional[str] = None

    # (프런트 exclude용 보조 정보)
    used_context_ids: List[str] = Field(default_factory=list)
    used_context: List[Dict[str, Any]] = Field(default_factory=list)

    # (선택) 학습 보조
    summary: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)
    outline: List[Dict[str, Any]] = Field(default_factory=list)
    glossary: List[Dict[str, str]] = Field(default_factory=list)
    study_questions: List[str] = Field(default_factory=list)
    difficulty_note: Optional[str] = None

    # 리라이트/평가 노출
    rewritten_query: Optional[str] = None
    rewritten: Optional[Dict[str, Any]] = None
    query_eval: Optional[Dict[str, Any]] = None
    queries_used: Optional[List[str]] = None

        # ★ 추가
    final_query: Optional[str] = None                   # 실제 검색에 사용된 메인 쿼리
    query_eval_before: Optional[Dict[str, Any]] = None  # 개선 전 점수
    query_eval_after: Optional[Dict[str, Any]] = None   # 개선 후 점수(= query_eval과 동일)

def _l2_normalize(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-12)

# ====== 공통 유틸 ======
def make_db_key(title: str, passage_text: str) -> str:
    t = title or (passage_text[:20] or "untitled")
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"\s+", "-", t)
    t = re.sub(r"[^가-힣A-Za-z0-9\-]", "", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    t = t.lower()
    h = hashlib.sha1((passage_text or "").encode("utf-8")).hexdigest()[:8]
    return f"{t}-{h}" if t else f"untitled-{h}"

_SENT_SPLIT = re.compile(r'(?<=[\.!?])\s+')
def to_sentences(text: str) -> List[Dict[str, Any]]:
    parts = [p.strip() for p in _SENT_SPLIT.split(text.strip()) if p.strip()]
    return [{"id": i+1, "text": s} for i, s in enumerate(parts)]

# ====== 1) 쿼리 리라이트 (학습 지향) ======
REASON_SYSTEM_PROMPT = """역할: 국어 비문학 학습 코치이자 검색 전문가.
입력: '현재 지문'과 '어려웠던 이유'.
목표: 학습(이해) 중심 RAG가 잘 되도록, '학습 목표'와 '핵심 개념'을 반영한 검색 쿼리를 작성.
주의: 원문 문장을 베끼지 말고, 개념/주제/문체를 일반화.

반환 JSON:
{
  "query": "검색에 쓸 압축 쿼리",
  "must_have": ["핵심개념1","핵심개념2"],
  "reading_goals": ["무엇을 이해해야 하는가 (예: 개념 정의, 관계 파악, 인과 구조)"],
  "simplify_strategy": "난해 요소를 완화하는 전략(예: 용어 평이화, 예시 추가, 문장 길이 단축)",
  "should_avoid": ["피해야 할 요소(예: 과도한 수식어, 통계 수치 복사)"]
}
"""

def rewrite_query(current_passage: str, difficulty_reason: str) -> Dict[str, Any]:
    user_content = f"""[현재 지문]
{current_passage}

[어려웠던 이유]
{difficulty_reason}
"""
    resp = client.chat.completions.create(
        model=OPENAI_MODEL_REWRITER,
        temperature=0.1,
        messages=[
            {"role":"system", "content": REASON_SYSTEM_PROMPT},
            {"role":"user", "content": user_content}
        ]
    )
    text = resp.choices[0].message.content.strip()
    try:
        m = re.search(r"\{.*\}", text, flags=re.S)
        data = json.loads(m.group(0)) if m else json.loads(text)
        if "query" not in data:
            raise ValueError("missing 'query'")
        data.setdefault("must_have", [])
        data.setdefault("reading_goals", [])
        data.setdefault("simplify_strategy", "")
        data.setdefault("should_avoid", [])
        return data
    except Exception:
        fallback = difficulty_reason.strip().split("\n")[0][:200]
        return {
            "query": fallback,
            "must_have": [],
            "reading_goals": [],
            "simplify_strategy": "",
            "should_avoid": []
        }

# ====== 2) 쿼리 평가/리파인 (AdvancedRAG 요지) ======
QUERY_EVAL_SYSTEM = """역할: RAG 검색 쿼리 평가자/코치. 반드시 JSON만 출력.
평가기준(0~1): coverage(핵심개념 포함도), clarity(명료성), specificity(구체성),
goal_alignment(학습목표 부합도), noise(불필요어/모순/금지요소; 낮을수록 좋음).
overall은 (coverage, clarity, specificity, goal_alignment)의 가중 평균(0.3/0.25/0.25/0.2)에서
noise를 벌점(최대 -0.15)으로 반영하여 0~1로 정규화.
"""

QUERY_EVAL_USER_TMPL = (
    "[입력 지문 요약 후보] (직접 사용 금지, 맥락 참고)\n"
    "{passage_hint}\n\n"
    "[어려웠던 이유]\n"
    "{diff_reason}\n\n"
    "[리라이트 된 쿼리 블록]\n"
    "{rewritten_json}\n\n"
    "요구:\n"
    "1) 위 쿼리를 평가하고(score), 부족하면 더 나은 쿼리(improved.query)와 사유 제시.\n"
    "2) variants: 검색 다양성을 위한 1~2개의 대체 쿼리(동의어/상위·하위개념/구문 변형).\n"
    "3) hyde: 쿼리를 2~3문장 가설 지문으로 확장(검색 임베딩 용도). 원문 베끼지 말 것.\n\n"
    "JSON:\n"
    "{{\n"
    '  "score": {{"coverage":0,"clarity":0,"specificity":0,"goal_alignment":0,"noise":0,"overall":0}},\n'
    '  "improved": {{"query":"...","must_have":[],"reading_goals":[],"should_avoid":[],"simplify_strategy":"..."}},\n'
    '  "variants": [{{"query":"..."}}, {{"query":"..."}}],\n'
    '  "hyde": "..."\n'
    "}}\n"
)

def _json_extract(text:str)->Dict[str,Any]:
    m = re.search(r"\{.*\}", text, flags=re.S)
    return json.loads(m.group(0)) if m else json.loads(text)

def ensure_terms(q: str, terms: List[str]) -> str:
    q_low = q.lower()
    for t in terms or []:
        if t and t.lower() not in q_low:
            q += f" {t}"
    return q.strip()

def eval_and_refine_query(
    rewritten: Dict[str,Any],
    current_passage: str,
    difficulty_reason: str,
    n_variants: int = MULTI_QUERY_N,
    enable_hyde: bool = ENABLE_HYDE,
) -> Dict[str,Any]:
    passage_hint = current_passage[:600]
    user = QUERY_EVAL_USER_TMPL.format(
        passage_hint=passage_hint,
        diff_reason=difficulty_reason,
        rewritten_json=json.dumps(rewritten, ensure_ascii=False)
    )
    resp = client.chat.completions.create(
        model=OPENAI_MODEL_REWRITER, temperature=0.1,
        messages=[{"role":"system","content":QUERY_EVAL_SYSTEM},
                  {"role":"user","content":user}]
    )
    try:
        data = _json_extract(resp.choices[0].message.content.strip())
    except Exception:
        data = {
            "score":{"coverage":0.6,"clarity":0.6,"specificity":0.6,"goal_alignment":0.6,"noise":0.2,"overall":0.6},
            "improved": rewritten,
            "variants": [],
            "hyde": ""
        }
    # variants 제한
    vs = list(data.get("variants") or [])
    data["variants"] = vs[:max(0, n_variants-1)]
    if not enable_hyde:
        data["hyde"] = ""
    # must_have는 항상 포함 보정
    base_q = (data.get("improved",{}) or {}).get("query") or rewritten.get("query","")
    mh = (data.get("improved",{}) or {}).get("must_have") or rewritten.get("must_have") or []
    (data["improved"] or {}).update({"query": ensure_terms(base_q, mh)})
    return data

# ====== 3) 멀티쿼리 검색 (group_id 단위로 최고점 집계) ======
def retrieve_similar(queries: List[str], top_k: int, exclude_group_ids: List[str], min_score: Optional[float]) -> List[Dict[str, Any]]:
    index, metas = get_index_and_meta()
    seen_gids = set(exclude_group_ids or [])
    agg: Dict[str, Dict[str, Any]] = {}  # gid -> {meta + _score + _q}
    for q in queries:
        q = (q or "").strip()
        if not q:
            continue
        qv = embed_texts([q])
        qv = _l2_normalize(qv.astype(np.float32))
        D, I = index.search(qv, top_k*3)
        for idx, score in zip(I[0], D[0]):
            if idx == -1:
                continue
            meta = metas[idx]
            gid = str(meta.get("group_id") or meta.get("base_group_id") or meta.get("id") or "")
            if (not gid) or (gid in seen_gids):
                continue
            if (min_score is not None) and (float(score) < float(min_score)):
                continue
            keep = agg.get(gid)
            if (keep is None) or (float(score) > keep.get("_score", -1e9)):
                agg[gid] = {**meta, "_score": float(score), "_q": q}
    results = sorted(agg.values(), key=lambda x: x["_score"], reverse=True)[:top_k]
    return results

# ====== 4) 컨텍스트 블록 (점수/매칭쿼리 표시) ======
def build_context_block(items: List[Dict[str, Any]]) -> str:
    lines = []
    for it in items:
        gid = it.get("group_id") or it.get("id") or "unknown"
        title = it.get("title") or ""
        q_used = it.get("_q", "")
        score = it.get("_score", None)
        passage = it.get("passage") or it.get("content") or ""
        snippet = passage if len(passage) <= 800 else passage[:800] + "..."
        sc = f"{score:.3f}" if isinstance(score, (int,float)) else "-"
        qshort = (q_used or "")[:60]
        lines.append(f"[ID:{gid}] {title} (score={sc}; by='{qshort}')\n{snippet}\n")
    return "\n---\n".join(lines)

# ====== 5) 요약 중심 생성 ======
GENERATOR_SYSTEM = """역할: 한국어 비문학 학습 코치. 절대 원문을 베끼지 말 것.
입력 '참고 자료'는 아이디어/주제/구조만 참고. 문장/수치/고유표현 직접 복사 금지.

출력(JSON만):
{
  "summary": "200~300자 요약",
  "key_points": ["핵심 논지/관계/근거 등 3~6개"],
  "outline": [{"section":"구조요약 소제목","note":"한 줄 설명"}],
  "glossary": [{"term":"핵심 용어","definition":"쉬운 정의"}],
  "simplified_passage": "400~600자 평이한 재서술(예시 1개 포함 가능, 표절 금지)",
  "study_questions": ["개방형 확인 질문 3~5개(객관식/정답라벨 금지)"],
  "difficulty_note": "사용자가 어려워한 지점을 어떻게 완화했는지"
}
"""

def generate_study(difficulty_reason: str, rewritten: Dict[str, Any], contexts: List[Dict[str, Any]], temperature: float) -> Dict[str, Any]:
    ctx = build_context_block(contexts)
    user_prompt = f"""[학습 목표]
{json.dumps(rewritten.get("reading_goals", []), ensure_ascii=False)}

[핵심 개념 힌트]
{json.dumps(rewritten.get("must_have", []), ensure_ascii=False)}

[완화 전략]
{rewritten.get("simplify_strategy","")}

[피해야 할 요소]
{json.dumps(rewritten.get("should_avoid", []), ensure_ascii=False)}

[어려웠던 이유]
{difficulty_reason}

[참고 자료(아이디어/주제/구조만 참고; 표절 금지)]
{ctx}
"""
    resp = client.chat.completions.create(
        model=OPENAI_MODEL_GENERATOR,
        temperature=temperature,
        messages=[
            {"role":"system", "content": GENERATOR_SYSTEM},
            {"role":"user", "content": user_prompt}
        ]
    )
    text = resp.choices[0].message.content.strip()
    try:
        m = re.search(r"\{.*\}", text, flags=re.S)
        data = json.loads(m.group(0)) if m else json.loads(text)
        for k in ["summary","key_points","outline","glossary","simplified_passage","study_questions"]:
            if k not in data:
                raise ValueError("missing fields")
        return data
    except Exception:
        return {
            "summary": "생성에 실패했습니다. 쿼리/하한을 조정해 다시 시도해 주세요.",
            "key_points": [],
            "outline": [],
            "glossary": [],
            "simplified_passage": "",
            "study_questions": ["지문을 다시 읽고 핵심 개념을 3가지로 정리해 보세요."],
            "difficulty_note": "—"
        }

# ====== 6) 엔드포인트 (A타입 구조 반환) ======
@router.post("/generate_similar", response_model=ATypeLikeResponse)
def generate_similar_problem(req: GenerateSimilarRequest) -> ATypeLikeResponse:
    if not req.current_passage.strip():
        raise HTTPException(400, "current_passage is empty")
    if not req.difficulty_reason.strip():
        raise HTTPException(400, "difficulty_reason is empty")

    # 1) 학습 지향 1차 리라이트
    rewritten = rewrite_query(req.current_passage, req.difficulty_reason)

    # 2) 1차 평가/리파인
    refine = eval_and_refine_query(rewritten, req.current_passage, req.difficulty_reason)
    query_eval_before = refine.get("score", {}) or {}
    overall_before = float(query_eval_before.get("overall", 0.0))

    # 원본/개선안 텍스트
    orig_q = (rewritten.get("query") or "").strip()
    impr_q = ((refine.get("improved") or {}).get("query") or orig_q).strip()

    # ★ 동일 조건으로 개선안 재평가(힌트 포함)
    improved_json = {
        "query": impr_q,
        "must_have": (refine.get("improved") or {}).get("must_have") or rewritten.get("must_have") or [],
        "reading_goals": (refine.get("improved") or {}).get("reading_goals") or rewritten.get("reading_goals") or [],
        "should_avoid": (refine.get("improved") or {}).get("should_avoid") or rewritten.get("should_avoid") or [],
        "simplify_strategy": (refine.get("improved") or {}).get("simplify_strategy") or rewritten.get("simplify_strategy") or "",
    }
    eval_after = eval_and_refine_query(improved_json, req.current_passage, req.difficulty_reason,
                                       n_variants=1, enable_hyde=False)
    query_eval_after = eval_after.get("score", {}) or {}
    overall_after = float(query_eval_after.get("overall", 0.0))

    # 2.5) 최종 쿼리 선택 규칙
    # - 임계값 미달이면 개선안 우선, 단 현저히 악화되면(>0.05) 원본 유지
    # - 임계값 이상이면 개선안이 소폭 이상 개선(>=0.02)일 때만 교체
    DEGRADED_MARGIN = 0.05
    IMPROVE_DELTA = 0.02
    if overall_before < QUERY_PASS_THRESHOLD:
        if overall_after + DEGRADED_MARGIN < overall_before:
            main_q = orig_q
            final_eval = query_eval_before
        else:
            main_q = impr_q
            final_eval = query_eval_after
    else:
        if overall_after > overall_before + IMPROVE_DELTA:
            main_q = impr_q
            final_eval = query_eval_after
        else:
            main_q = orig_q
            final_eval = query_eval_before

    # 멀티쿼리 구성(variants + hyde)
    queries = [main_q]
    for v in (refine.get("variants") or []):
        qv = (v.get("query") or "").strip()
        if qv and qv.lower() not in {q.lower() for q in queries}:
            queries.append(qv)
    hyde_text = (refine.get("hyde") or "").strip()
    if ENABLE_HYDE and hyde_text and hyde_text.lower() not in {q.lower() for q in queries}:
        queries.append(hyde_text)

    # 3) 멀티쿼리 검색(원본 제외 + 하한)
    cand = retrieve_similar(
        queries=queries,
        top_k=req.top_k,
        exclude_group_ids=req.exclude_group_ids,
        min_score=req.min_score
    )
    if not cand:
        raise HTTPException(404, "유사한 지문을 찾지 못했습니다. 쿼리/하한(min_score)을 조정해 보세요.")

    cand = sorted(cand, key=lambda x: x.get("_score", 0.0), reverse=True)[:req.context_top_k]

    # 4) 요약팩 생성 → A타입 구조로 변환
    gen = generate_study(req.difficulty_reason, rewritten, cand, req.temperature)

    generated_passage = (gen.get("simplified_passage") or "").strip()
    if not generated_passage:
        generated_passage = (gen.get("summary") or "").strip()
    sentences = to_sentences(generated_passage)

    top_ctx = cand[0] if cand else {}
    title = (top_ctx.get("title") or "학습 요약 지문").strip()
    topic = top_ctx.get("topic") or "학습"

    db_key = make_db_key(title, generated_passage)

    key_points_hint = "; ".join(gen.get("key_points", []))
    quality = llm_quality(generated_passage, topic, key_points_hint)

    used_context, used_ids = [], []
    for it in cand:
        gid = str(it.get("group_id") or it.get("id") or "")
        if gid:
            used_ids.append(gid)
            used_context.append({
                "group_id": gid,
                "title": it.get("title") or "",
                "score": round(float(it.get("_score", 0.0)), 4),
                "matched_query": it.get("_q", "")
            })

    fmt = lambda d: {k: round(float(v), 3) for k, v in (d or {}).items()}

    return ATypeLikeResponse(
        title=title,
        db_key=db_key,
        generated_passage=generated_passage,
        sentences=sentences,
        quality=quality,
        repairs=[],
        regen_count=0,
        topic=topic,
        used_context_ids=used_ids,
        used_context=used_context,
        summary=gen.get("summary"),
        key_points=list(gen.get("key_points", [])),
        outline=[o for o in gen.get("outline", []) if isinstance(o, dict)],
        glossary=[g for g in gen.get("glossary", []) if isinstance(g, dict)],
        study_questions=list(gen.get("study_questions", [])),
        difficulty_note=gen.get("difficulty_note"),

        # 리라이트/평가 관련
        rewritten_query=rewritten.get("query"),
        rewritten=rewritten,
        final_query=main_q,
        query_eval=fmt(final_eval),               # 최종 선택의 점수
        query_eval_before=fmt(query_eval_before), # 개선 전
        query_eval_after=fmt(query_eval_after),   # 개선 후
        queries_used=queries
    )


