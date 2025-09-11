import json, os, fitz
from utils_text import RE_GROUP, split_passage_questions

RAW_DIR = "data/raw"
OUT_JSONL = "data/out/parsed_blocks.jsonl"

def iter_pdfs():
    for fn in os.listdir(RAW_DIR):
        if fn.lower().endswith(".pdf"):
            yield fn, os.path.splitext(fn)[0]  # (파일명, source_id)

def main():
    os.makedirs(os.path.dirname(OUT_JSONL), exist_ok=True)
    with open(OUT_JSONL, "w", encoding="utf-8") as fout:
        for filename, source_id in iter_pdfs():
            doc = fitz.open(os.path.join(RAW_DIR, filename))
            full = "\n\n".join(page.get_text("text") for page in doc)
            heads = [(m.start(), m.group()) for m in RE_GROUP.finditer(full)]
            spans = [(heads[i][0], heads[i+1][0] if i+1<len(heads) else len(full)) for i in range(len(heads))]
            for idx,(s,e) in enumerate(spans, start=1):
                block = full[s:e].strip()
                obj = {
                    "source_id": source_id,                # ★
                    "group_id": f"{source_id}_grp_{idx:03d}",  # ★ 전역 고유
                    "raw_block": block
                }
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print(f"blocks -> {OUT_JSONL}")

if __name__=="__main__":
    main()
