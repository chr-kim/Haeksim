import os, json
from typing import Any, Dict, List
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"  # ← 임베딩 모델

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

# openai_client.py (추가)
def llm_generate_passage(
    *,
    topic: str,
    difficulty: str,
    target_chars: int,
    base_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    sent_min, sent_max, diff_rule = _difficulty_spec(difficulty)
    KOREAN_CHAR_BIAS = 1.30
    min_chars = max(300, int(target_chars * 0.9 * KOREAN_CHAR_BIAS))
    max_chars = int(target_chars * 1.1 * KOREAN_CHAR_BIAS)
    length_rule = f"{min_chars}~{max_chars}자(±10%, 한국어 '문자 수' 기준)"

    BASE = {
        "group_id": (base_context or {}).get("group_id"),
        "sentences": (base_context or {}).get("sentences") or []
    }

    sys = "너는 한국어 수능 국어 비문학 지문 제작 전문가다. 항상 JSON만 출력한다."
    user = f"""
[생성 조건]
- 주제 범주: {topic}
- 난이도: {difficulty} ({diff_rule})
- 지문 길이: {length_rule}
- 문장 수: {sent_min}~{sent_max}문장, 각 문장은 마침표로 끝낼 것
- 사실 발명 금지, BASE의 논지/사실관계 유지(직접복사 금지, 의미 재구성)

[참고 자료(BASE)]
BASE = {json.dumps(BASE, ensure_ascii=False)}

[출력 JSON]
{{
  "title": "8~20자 핵심 명사구(특수문자/괄호/따옴표/콜론 금지)",
  "question": "위 글의 내용으로 적절한 것을 고르시오.",
  "passage_sentences": [{{"id":1,"text":"..."}}],   # 1부터 순번, 마침표로 끝남
  "used_base_group_id": {json.dumps(BASE.get("group_id"))}
}}
"""
    return _chat_json([{"role":"system","content":sys},{"role":"user","content":user}])


def llm_generate_choices(
    *,
    passage_sentences: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    입력: 방금 생성된 지문 문장 리스트
    출력: {"choices":[{text,is_correct,relation,evidence_sent_ids}, ...]} (정확히 5개)
    """
    sys = "너는 한국어 수능 국어 비문학 선택지 제작 전문가다. 항상 JSON만 출력한다."
    user = f"""
[지문 문장들]
{json.dumps(passage_sentences, ensure_ascii=False)}

[선지 규칙]
- "choices"는 정확히 5개
- 정답 1개(is_correct=true, relation="support"), 오답 4개(is_correct=false, relation="contradict")
- 각 선지는 지문 문장 1~2개와 '직접' 근거/모순되도록 "evidence_sent_ids":[...]
- 절대표현(항상/전부/유일 등) 남용 금지, 지문이 보편을 보장하지 않으면 쓰지 말 것
- 정답 위치는 1~5번 중 무작위
- 지문 내용 외부 확장/추정 금지

[출력 JSON]
{{
  "choices": [
    {{"text":"...", "is_correct":true,  "relation":"support",    "evidence_sent_ids":[2]}},
    {{"text":"...", "is_correct":false, "relation":"contradict", "evidence_sent_ids":[3]}}
  ]
}}
"""
    return _chat_json([{"role":"system","content":sys},{"role":"user","content":user}])


def llm_generate_with_evidence(
    mode: str, *,
    topic: str,
    difficulty: str,
    target_chars: int,
    base_context: Dict[str, Any] | None = None  # ← 베이스 컨텍스트 주입
) -> Dict[str, Any]:
    """
    topic: 과학기술/인문/사회/예술/문학/시사 (프롬프트 힌트)
    difficulty: 기초/보통/어려움
    target_chars: 권장 800~1200자
    """
    sent_min, sent_max, diff_rule = _difficulty_spec(difficulty)
    KOREAN_CHAR_BIAS = 1.30  # 한글의 '토큰→문자수' 보정 (필요시 1.25~1.35 사이로 조정)
    min_chars = max(300, int(target_chars * 0.9 * KOREAN_CHAR_BIAS))
    max_chars = int(target_chars * 1.1 * KOREAN_CHAR_BIAS)
    length_rule = f"{min_chars}~{max_chars}자(±10%, 한국어 '문자 수(공백 포함)' 기준)"

    # 프롬프트에 사용할 BASE 정보 정규화
    BASE = {
        "group_id": (base_context or {}).get("group_id"),
        "sentences": (base_context or {}).get("sentences") or []
    }

    sys = "너는 한국어 수능 국어 비문학 문제 제작 전문가다. 항상 JSON만 출력한다."
    user = f"""
[생성 조건]
- 주제 범주: {topic}
- 난이도: {difficulty} ({diff_rule})
- 지문 길이: {length_rule}
- 문장 수: {sent_min}~{sent_max}문장, 각 문장은 마침표로 끝낼 것
- 사실 발명 금지

[참고 자료]
- 아래 베이스 문장들을 핵심 근거로 사용하되 “직접 복사”는 금지한다.
- 의미/논지/사실관계를 유지하며 재구성(paraphrase)할 것.
- 베이스 group_id는 "used_base_group_id"에 명시한다.
BASE = {json.dumps(BASE, ensure_ascii=False)}

[제목 규칙]
- "title": 8~20자 내 핵심 명사구(한국어), 특수문자/따옴표/괄호/콜론 금지, 공백 2연속 금지

[문두(질문) 규칙]
- "question": 수능형 선택지 문제 질문 한 문장.
- 기본형으로 고정: "위 글의 내용으로 적절한 것을 고르시오."
- 오답 유도형(적절하지 않은 것) 금지. 정답은 정확히 1개만 is_correct=true.

[선지 규칙(mode=="B"일 때)]
- "choices"는 5개. 정확히 1개 is_correct=true(정답), 나머지 false(오답)
- 정답 relation="support", 오답 relation="contradict"
- 각 선지는 지문 문장 1~2개에 "직접" 근거/모순되도록 "evidence_sent_ids":[...]
- 절대표현(항상/오직/전부 등) 남용 금지, 지문이 보편을 보장하지 않으면 쓰지 않기

[정답 위치 규칙]
- 정답(is_correct=true)은 1~5번 중 무작위로 배치할 것.

[주제 다양성 규칙]
- {topic} 범주 안에서 세부 소주제·사례·시대·관점을 바꿔 반복성을 피할 것.
- 직전 베이스와 동일/유사 어휘를 불필요하게 반복하지 말 것(동의어/상위어 사용).

[최종 JSON 스키마]
{{
  "title": "..." ,
  "question": "위 글의 내용으로 적절한 것을 고르시오.",
  "passage_sentences": [{{"id":1,"text":"..."}}, ...],
  "choices": [  // mode B일 때만
    {{"text":"...", "is_correct":true,  "relation":"support",    "evidence_sent_ids":[2]}},
    {{"text":"...", "is_correct":false, "relation":"contradict", "evidence_sent_ids":[3]}}
  ],
  "used_base_group_id": {json.dumps(BASE.get("group_id"))}  // 사용한 베이스 그룹 id (없으면 null)
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
