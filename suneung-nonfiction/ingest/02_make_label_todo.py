# ingest/02_make_label_todo.py
import json, csv, os

IN = "data/out/parsed_blocks.jsonl"
OUT = "data/out/items_for_label.csv"

def main():
    rows = []
    with open(IN, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            rows.append({
                "group_id": o["group_id"],
                # 수기 라벨
                "is_nonfiction": "",          # true/false
                "grade_level": "",            # "고1" | "고2" | "고3"
                "topic": ""                   # "과학기술" | "인문" | "사회" | "예술/문학" | "시사"
            })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["group_id","is_nonfiction","grade_level","topic"])
        w.writeheader(); w.writerows(rows)
    print(f"라벨 CSV -> {OUT} (is_nonfiction/grade_level/topic 수작업 기입)")

if __name__ == "__main__":
    main()
