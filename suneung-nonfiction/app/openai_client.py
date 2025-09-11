import os, json
from typing import Any, Dict, List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"  # ← 임베딩 모델 추가

def _chat_json(messages: List[Dict[str, Any]], max_tokens: int = 3200) -> Dict[str, Any]:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=max_tokens,
    )
    text = resp.choices[0].message.content
    try:
        return json.loads(text)
    except Exception:
        return {"error": "invalid_json", "raw": text}

def call_json(prompt: str) -> Dict[str, Any]:
    return _chat_json([
        {"role":"system","content":"너는 한국어 국어 비문학 문제 생성/검증 전용 모델이다. 반드시 JSON만 출력한다."},
        {"role":"user","content": prompt}
    ])

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    OpenAI 임베딩 유틸. 입력 텍스트 리스트와 같은 순서의 벡터 리스트를 반환.
    실패 시 빈 리스트를 반환(상위에서 overlap 폴백 사용).
    """
    try:
        resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
        return [d.embedding for d in resp.data]
    except Exception:
        return []

def _difficulty_spec(difficulty: str):
    # 문장 수/추론 난이도 가이드
    if difficulty == "기초":
        return (6, 10, "어휘와 문장구조는 단순하게, 사실 서술 중심. 추론은 1단계 이내.")
    if difficulty == "보통":
        return (8, 12, "어휘/구문은 보통, 개념 연결과 1~2단계 추론 포함.")
    # 어려움(기본)
    return (10, 14, "전문어 최소 사용 가능, 명제 간 관계와 2단계 이상의 추론 포함.")

def llm_generate_with_evidence(mode: str, *, topic: str, difficulty: str, target_chars: int) -> Dict[str, Any]:
    """
    topic: 과학기술/인문/사회/예술/문학/시사 (프롬프트 힌트)
    difficulty: 기초/보통/어려움
    target_chars: 800~1200자
    """
    sent_min, sent_max, diff_rule = _difficulty_spec(difficulty)
    length_rule = f"{max(300, int(target_chars*0.9))}~{int(target_chars*1.1)}자(±10%)"

    sys = "너는 한국어 수능 국어 비문학 문제 제작 전문가다. 항상 JSON만 출력한다."
    user = f"""
[생성 조건]
- 주제 범주: {topic}
- 난이도: {difficulty} ({diff_rule})
- 지문 길이: {length_rule}
- 문장 수: {sent_min}~{sent_max}문장, 각 문장은 마침표로 끝낼 것
- 사실 발명 금지

[제목 생성 규칙]
- "title": 8~20자 내 핵심 명사구(한국어), 특수문자/따옴표/괄호/콜론 금지, 공백 2연속 금지
- 예시: "의료 AI의 윤리 과제", "디지털 플랫폼과 자기표현"

[출력 요구]
1) "title": "..."   // ← 지문 제목(필수)
2) "passage_sentences": [{{"id":1,"text":"..."}} ...]  // {sent_min}~{sent_max}개
3) mode=="A"면 선지 생략. mode=="B"면 "choices" 5개:
   - 정확히 1개 is_correct=true(정답), 나머지 false(오답)
   - 정답 relation="support", 오답 relation="contradict"
   - 각 선지는 지문 문장 1~2개에 직접 근거/모순되도록 "evidence_sent_ids":[...]
   - 절대표현(항상/오직/전부 등)은 지문이 보편을 보장하지 않으면 쓰지 말 것

[최종 JSON 스키마]
{{
  "title": "..." ,
  "passage_sentences": [{{"id":1,"text":"..."}} , ...],
  "choices": [  // mode B일 때만
    {{"text":"...", "is_correct":true,  "relation":"support",    "evidence_sent_ids":[2]}}...
  ]
}}

mode="{mode}"
"""
    return _chat_json([{"role":"system","content":sys},{"role":"user","content":user}])

def llm_quality(passage: str, topic_hint: str, key_points: str) -> Dict[str, Any]:
    sys = "너는 한국어 비문학 생성물 품질을 채점하는 검증자다. JSON만 출력."
    user = f"""
[지문]: {passage}
[주제 힌트]: {topic_hint}
[베이스 핵심 포인트]: {key_points}

기준(각 0~2): topic_alignment, logic, factuality, groundedness, clarity
pass_fail: pass|revise
JSON:
{{
 "topic_alignment":0, "logic":0, "factuality":0, "groundedness":0, "clarity":0,
 "pass_fail":"pass", "notes":"간결 코멘트"
}}
"""
    return _chat_json([{"role":"system","content": sys},{"role":"user","content": user}])
