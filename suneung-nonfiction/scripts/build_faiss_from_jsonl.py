#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
nonfiction.jsonl -> (OpenAI Embeddings) -> FAISS index + aligned metadata.jsonl

- 입력: nonfiction.jsonl (각 줄은 JSON 오브젝트)
  필수키: group_id, passage
  선택키: title, choices, source, span 등 자유
- 출력:
  1) data/metadata.jsonl  : 인덱스 row와 순서 1:1 대응되는 메타 (원본 + 내부 필드 추가)
  2) data/faiss.index     : cosine 유사도 검색용 FAISS IndexFlatIP

환경변수:
- OPENAI_API_KEY            : 필수
- OPENAI_EMBED_MODEL        : 기본 "text-embedding-3-small"
- RAG_FAISS_INDEX_PATH      : 기본 "data/faiss.index"
- RAG_METADATA_JSON_PATH    : 기본 "data/metadata.jsonl"

사용 예:
    python scripts/build_faiss_from_jsonl.py \
        --input /mnt/data/nonfiction.jsonl \
        --out-dir data \
        --batch-size 128

간단 검증:
    python scripts/build_faiss_from_jsonl.py --verify "논리 전개가 선명한 과학 비문학"
"""
from __future__ import annotations
import os, json, argparse, sys, time, math
from typing import List, Dict, Any, Iterable, Tuple

import numpy as np
import faiss
from dotenv import load_dotenv
load_dotenv()

# OpenAI SDK (>=1.0.0)
from openai import OpenAI
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

DEFAULT_INDEX_PATH = os.getenv("RAG_FAISS_INDEX_PATH", "data/faiss.index")
DEFAULT_META_PATH  = os.getenv("RAG_METADATA_JSON_PATH", "data/metadata.jsonl")


def read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for ln, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception as e:
                raise ValueError(f"JSONL parse error at line {ln}: {e}") from e


def normalize(vecs: np.ndarray) -> np.ndarray:
    """L2 normalize for cosine similarity with IndexFlatIP."""
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
    return vecs / norms


def batched(seq: List[str], n: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


def embed_texts(client: OpenAI, texts: List[str], batch_size: int = 128) -> np.ndarray:
    all_vecs: List[np.ndarray] = []
    for batch in batched(texts, batch_size):
        # 지연 & 재시도 (간단 백오프)
        for attempt in range(6):
            try:
                resp = client.embeddings.create(model=OPENAI_EMBED_MODEL, input=batch)
                vecs = [np.array(d.embedding, dtype=np.float32) for d in resp.data]
                all_vecs.extend(vecs)
                break
            except Exception as e:
                wait = 1.5 ** attempt
                print(f"[embed] error: {e} -> retry in {wait:.1f}s", file=sys.stderr)
                time.sleep(wait)
        else:
            raise RuntimeError("Embedding failed after retries.")
    return np.vstack(all_vecs)


def ensure_outdir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def build_index(
    in_jsonl: str,
    out_meta: str,
    out_index: str,
    batch_size: int = 128,
    filter_empty: bool = True,
) -> Tuple[int, int, int]:
    """
    returns: (num_loaded, num_embedded, dim)
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    rows = list(read_jsonl(in_jsonl))
    print(f"[load] {in_jsonl}: {len(rows)} rows")

    # 필수 필드 검사 & passage 수집
    texts: List[str] = []
    out_rows: List[Dict[str, Any]] = []
    dropped = 0
    for i, r in enumerate(rows):
        passage = (r.get("passage") or "").strip()
        gid = r.get("group_id")
        if filter_empty and (not passage or not gid):
            dropped += 1
            continue
        # passage만 임베딩 (원하면 title까지 합쳐도 됨)
        texts.append(passage)
        # 메타: 인덱스 정렬과 정확히 1:1 대응되도록 원본 + 내부 필드 추가
        out_rows.append({
            **r,
            "_row_index": i,          # 원본 파일 내 라인 인덱스(정보용)
            "_embed_text": "passage", # 어떤 필드를 임베딩했는지 기록
        })
    print(f"[prep] usable: {len(texts)}, dropped: {dropped}")

    if not texts:
        raise RuntimeError("No valid passages to embed.")

    # 임베딩
    vecs = embed_texts(client, texts, batch_size=batch_size)
    dim = vecs.shape[1]
    print(f"[embed] vectors: {vecs.shape}")

    # cosine 유사도용 IndexFlatIP + L2 normalize
    vecs = normalize(vecs)
    index = faiss.IndexFlatIP(dim)
    index.add(vecs)
    print(f"[faiss] index.ntotal={index.ntotal}, dim={dim}")

    # 저장
    ensure_outdir(out_index)
    ensure_outdir(out_meta)
    faiss.write_index(index, out_index)
    with open(out_meta, "w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[save] meta -> {out_meta}")
    print(f"[save] index -> {out_index}")
    return (len(rows), len(out_rows), dim)


def quick_verify(query: str, meta_path: str = DEFAULT_META_PATH, index_path: str = DEFAULT_INDEX_PATH, k: int = 5):
    """간단 검색 검증: 쿼리 임베딩 -> 상위 k개 메타 출력"""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    print(f"[verify] query: {query}")

    # 로드
    metas = list(read_jsonl(meta_path))
    index = faiss.read_index(index_path)

    # 쿼리 임베딩 + normalize
    qv = embed_texts(client, [query], batch_size=1)
    qv = normalize(qv)

    # 검색
    D, I = index.search(qv, k)
    print("\n[top-k]")
    for rank, (idx, score) in enumerate(zip(I[0], D[0]), start=1):
        if idx == -1:
            continue
        m = metas[idx]
        gid = m.get("group_id")
        title = m.get("title", "")
        psg = (m.get("passage") or "")[:140].replace("\n", " ")
        print(f"{rank:>2}. score={score:.3f} gid={gid} title={title} | {psg}...")


def main():
    ap = argparse.ArgumentParser(description="Build FAISS index from nonfiction.jsonl")
    ap.add_argument("--input", "-i", default="nonfiction.jsonl", help="path to nonfiction.jsonl")
    ap.add_argument("--out-dir", "-o", default="data", help="output directory (for index & metadata)")
    ap.add_argument("--batch-size", type=int, default=128, help="embedding batch size")
    ap.add_argument("--verify", help="optional: run top-k search after build with this query")
    args = ap.parse_args()

    meta_out = os.path.join(args.out_dir, os.path.basename(DEFAULT_META_PATH))
    index_out = os.path.join(args.out_dir, os.path.basename(DEFAULT_INDEX_PATH))

    # 환경변수의 경로 규칙과도 맞추고 싶다면, 고정 경로로 저장:
    # meta_out  = DEFAULT_META_PATH
    # index_out = DEFAULT_INDEX_PATH

    total, used, dim = build_index(
        in_jsonl=args.input,
        out_meta=meta_out,
        out_index=index_out,
        batch_size=args.batch_size,
    )
    print(f"[done] loaded={total}, embedded={used}, dim={dim}")

    if args.verify:
        quick_verify(args.verify, meta_path=meta_out, index_path=index_out, k=5)


if __name__ == "__main__":
    main()
