# ingest/04_build_index.py
import os, json, math
import numpy as np
import faiss
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

IN = "data/out/nonfiction.jsonl"
IDX_DIR = "data/out/index"
EMB_MODEL = "text-embedding-3-small"  # 1536차원, 빠르고 저렴
BATCH = 64

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def embed_batch(texts: List[str]) -> np.ndarray:
    """
    OpenAI 임베딩 API로 일괄 임베딩.
    반환: (N, D) float32
    """
    resp = client.embeddings.create(model=EMB_MODEL, input=texts)
    vecs = [d.embedding for d in resp.data]
    arr = np.array(vecs, dtype="float32")
    return arr

def main():
    os.makedirs(IDX_DIR, exist_ok=True)

    # 데이터 읽기
    passages, keys = [], []
    with open(IN, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            # 긴 지문은 잘려 나가지 않도록 필요 시 앞/뒤를 요약해도 됨 (지금은 전체 사용)
            passages.append(o["passage"])
            keys.append(o["group_id"])

    if not passages:
        print("no passages to index"); return

    # 배치 임베딩
    all_vecs = []
    for i in range(0, len(passages), BATCH):
        chunk = passages[i:i+BATCH]
        vecs = embed_batch(chunk)
        all_vecs.append(vecs)
        print(f"embedded {i+len(chunk)}/{len(passages)}")

    mat = np.vstack(all_vecs).astype("float32")
    # 내적 검색 성능을 위해 L2 정규화
    faiss.normalize_L2(mat)

    d = mat.shape[1]  # 차원(1536)
    index = faiss.IndexFlatIP(d)
    index.add(mat)
    faiss.write_index(index, os.path.join(IDX_DIR, "passages.faiss"))
    np.save(os.path.join(IDX_DIR, "keys.npy"), np.array(keys, dtype=object))
    meta = {"emb_model": EMB_MODEL, "dim": int(d), "count": len(keys)}
    with open(os.path.join(IDX_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"faiss index built: {len(keys)} items, dim={d}, model={EMB_MODEL}")

if __name__ == "__main__":
    main()
