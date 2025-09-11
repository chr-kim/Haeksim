# ingest/03_merge_labels_and_answers.py
import json, csv, os
from utils_text import split_passage_questions, ko_sentence_split

IN_BLOCKS = "data/out/parsed_blocks.jsonl"
IN_LABELS = "data/out/items_for_label.csv"
IN_ANS    = "data/answer_keys.csv"
OUT_NF    = "data/out/nonfiction.jsonl"

def _normalize(name: str) -> str:
    # 헤더 키 정규화 (BOM 제거, 공백 제거, 소문자화)
    return (name or "").replace("\ufeff", "").strip().lower()

def _find_key(field_map, candidates):
    for k in candidates:
        found = field_map.get(k)
        if found:
            return found
    return None

def load_labels():
    d = {}
    # BOM 안전
    with open(IN_LABELS, encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        raw_fields = rdr.fieldnames or []
        # 원본 헤더 → 정규화 키 매핑
        field_map = { _normalize(n): n for n in raw_fields }

        gid_key   = _find_key(field_map, ("group_id","groupid","gruop_id","grp_id","grpid"))
        nf_key    = _find_key(field_map, ("is_nonfiction","isnonfiction","is_nf","nonfiction"))
        grade_key = _find_key(field_map, ("grade_level","grade","gradelevel"))
        topic_key = _find_key(field_map, ("topic","category"))

        if not gid_key:
            raise KeyError(f"'group_id' column not found. Found columns: {raw_fields}")

        def to_bool(x):
            s = str(x).strip().lower()
            return s in ("true","1","y","yes","t")

        for row in rdr:
            gid = (row.get(gid_key) or "").strip()
            if not gid:
                continue
            d[gid] = {
                "is_nonfiction": to_bool(row.get(nf_key, "")) if nf_key else False,
                "grade_level": (row.get(grade_key) or "").strip() or None if grade_key else None,
                "topic": (row.get(topic_key) or "").strip() or None if topic_key else None,
            }
    return d

def load_answers():
    d = {}
    if not os.path.exists(IN_ANS):
        return d
    # BOM 안전
    with open(IN_ANS, encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        raw_fields = rdr.fieldnames or []
        field_map = { _normalize(n): n for n in raw_fields }

        gid_key = _find_key(field_map, ("group_id","groupid","gruop_id","grp_id","grpid"))
        num_key = _find_key(field_map, ("number","qnum","q_no"))
        ans_key = _find_key(field_map, ("answer_index","answer","ans","idx"))

        if not gid_key or not num_key or not ans_key:
            raise KeyError(f"answer_keys.csv header missing. Found: {raw_fields}")

        for row in rdr:
            gid = (row.get(gid_key) or "").strip()
            if not gid:
                continue
            # number 파싱
            try:
                num = int(str(row.get(num_key, "")).strip())
            except Exception:
                continue
            # answer_index 파싱 (비어있으면 None)
            val = str(row.get(ans_key, "")).strip()
            d[(gid, num)] = int(val) if val.isdigit() else None
    return d

def main():
    labels  = load_labels()
    answers = load_answers()

    os.makedirs(os.path.dirname(OUT_NF), exist_ok=True)
    with open(IN_BLOCKS, encoding="utf-8") as fin, open(OUT_NF, "w", encoding="utf-8") as fout:
        for line in fin:
            o = json.loads(line)
            gid = o["group_id"]

            lab = labels.get(gid, {"is_nonfiction": False})
            # 비문학만 진행
            if not lab["is_nonfiction"]:
                continue

            pq = split_passage_questions(o["raw_block"])
            passage   = pq["passage"]
            questions = pq["questions"]
            sentences = ko_sentence_split(passage)

            # 정답 매핑 (없으면 None 유지)
            for q in questions:
                key = (gid, q["number"])
                q["answer_index"] = answers.get(key, None)

            rec = {
                "source_id": gid.split("_grp_")[0],
                "group_id": gid,
                "passage": passage,
                "sentences": sentences,
                "questions": questions,
                # 추가된 라벨
                "grade_level": lab.get("grade_level"),
                "topic": lab.get("topic"),
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"비문학 jsonl -> {OUT_NF}")

if __name__ == "__main__":
    main()
