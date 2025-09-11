import re
from kss import split_sentences

RE_GROUP = re.compile(
    r'^[\[\(]\s*\d+\s*[~∼～-]\s*\d+\s*[\]\)]\s*.*다음\s*글', re.M
)
RE_QNUM   = re.compile(r'^\d+\.\s', re.M)
RE_CHOICE = re.compile(r'^[①②③④⑤]', re.M)
RE_SUB    = re.compile(r'^\([가-힣]\)', re.M)

def ko_sentence_split(text:str):
    sents = split_sentences(text)
    return [{"id": i+1, "text": s.strip()} for i,s in enumerate(sents) if s.strip()]

def split_passage_questions(block:str):
    q_positions = [m.start() for m in RE_QNUM.finditer(block)]
    if not q_positions:
        return {"passage": block.strip(), "questions":[]}
    passage_text = block[:q_positions[0]].strip()
    q_chunks = [block[q_positions[i]: q_positions[i+1] if i+1<len(q_positions) else len(block)] for i in range(len(q_positions))]
    questions = []
    for qc in q_chunks:
        lines = [ln.strip() for ln in qc.splitlines() if ln.strip()]
        m = re.match(r'^(\d+)\.\s?', lines[0])
        number = int(m.group(1)) if m else None
        body, choices = [], []
        for ln in lines[1:]:
            if RE_CHOICE.match(ln):
                choices.append(ln)
            else:
                body.append(ln)
        questions.append({
            "number": number,
            "stem": " ".join(body).strip(),
            "choices": [{"index":i, "text":c} for i,c in enumerate(choices)]
        })
    return {"passage": passage_text, "questions": questions}
