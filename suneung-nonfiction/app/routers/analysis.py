from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any, Optional
import os, json
from openai import OpenAI

# ★ items 섹션으로 가도록 태그 지정
router = APIRouter(prefix="/api/v1", tags=["items"])

# ---------- 데이터 모델 ----------
class Choice(BaseModel):
    index: int
    text: str

class AnalyzeRequest(BaseModel):
    item_id: str                     # 문자열 슬러그/ID 허용
    question: str
    passage: str
    choices: List[Choice]
    correct_index: int
    user_selected_index: int
    evidence_map: Dict[int, str] = Field(default_factory=dict)
    meta: Optional[Dict[str, Any]] = None

class PerChoiceFeedback(BaseModel):
    index: int
    verdict: str                     # "support" | "contradict" | "irrelevant"
    score: int                       # 0~100
    user_evidence: str = ""
    evidence_feedback: str
    model_rationale: str

class AnalyzeResponse(BaseModel):
    is_user_correct: bool
    correct_index: int
    per_choice: List[PerChoiceFeedback]
    overall_feedback: str
    scores: Dict[str, int]           # {"correctness","evidence_quality","reasoning","overall"}

# ---------- LLM 프롬프트 ----------
def build_prompt(p: AnalyzeRequest) -> str:
    return f"""
[ROLE]
너는 한국어 독해·논리 평가자다. 출력은 반드시 지정된 JSON 스키마만 사용한다.

[TASK TYPE]
문항 유형은 '옳은 것을 고르시오'이다. 즉, choices 중 맞는 진술(True)은 보통 1개, 나머지는 False다.
'correct_index'는 정답(True)인 선지의 index다.

[WHAT TO DO]
각 선지 i에 대해 다음을 수행하라.
1) 먼저 '지문 ↔ 선지'의 관계를 판정하라:
   - 지문이 선지를 지지하면 verdict="support"
   - 지문이 선지를 반박(내용상 부정·모순)하면 verdict="contradict"
   - 지문에서 판단 불가/무관이면 verdict="irrelevant"

2) 사용자의 근거(user_evidence = evidence_map[i])가
   '선택/배제' 판단에 얼마나 적절한지 점수화하라(0~100):
   - 평가 기준은 "정답 판별 관점"이다.
     * 만약 해당 선지가 True(= i == correct_index)라면,
       근거가 지문으로 그 선지를 '지지'할수록 점수가 높다.
     * 만약 해당 선지가 False(= i != correct_index)라면,
       근거가 지문으로 그 선지를 '반박(배제)'할수록 점수가 높다.
   - 구체적 루브릭:
     * 90~100: 지문 핵심 문장/의미를 정확히 인용·요약하여
               (True: 지지 / False: 반박) 판단을 명확히 뒷받침.
     * 60~80 : 일부 맞지만 핵심이 빠짐/표현이 모호/간접적 근거.
     * 20~50 : 일반론적·재진술 위주로 설득력이 약함.
     * 0~10  : 무관/오해/반대 방향 근거/공란/불확실(“모르겠다” 등).
   - 아래와 같은 한국어 표현이 포함되면 기본 10점 이하로 간주:
     ["모르겠다","잘 모르","기억 안","애매","확신","모름","??"]

3) evidence_feedback(문장)에는
   - 왜 높은/낮은 점수를 줬는지,
   - (True/False에 따라) '선택/배제' 판단에 어떻게 기여했는지를 간결하게 설명하라.
4) model_rationale(문장)에는 지문에서의 핵심 근거 논지를 1~2문장으로 요약하되,
   25단어 이내 짧은 인용/요약만 사용하라(과도한 장문 인용 금지).

[INPUT]
Question: {p.question}

Passage:
{p.passage}

Choices (index는 0부터 시작):
{json.dumps([c.dict() for c in p.choices], ensure_ascii=False, indent=2)}

Correct Index: {p.correct_index}
User Selected Index: {p.user_selected_index}

User Evidence Map:
{json.dumps(p.evidence_map, ensure_ascii=False, indent=2)}

[OUTPUT FORMAT RULE]
- 오직 JSON만 반환한다.
- per_choice[i]는 모든 index를 포함해야 하며,
  verdict ∈ {"support","contradict","irrelevant"}, score ∈ [0,100] 정수.
"""

# ---------- JSON 스키마 (가능하면 강제) ----------
JSON_SCHEMA = {
    "name": "AnalyzeResponse",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["is_user_correct", "correct_index", "per_choice", "overall_feedback", "scores"],
        "properties": {
            "is_user_correct": {"type": "boolean"},
            "correct_index": {"type": "integer"},
            "overall_feedback": {"type": "string"},
            "scores": {
                "type": "object",
                "required": ["correctness", "evidence_quality", "reasoning", "overall"],
                "properties": {
                    "correctness": {"type": "integer"},
                    "evidence_quality": {"type": "integer"},
                    "reasoning": {"type": "integer"},
                    "overall": {"type": "integer"},
                },
                "additionalProperties": False
            },
            "per_choice": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["index","verdict","score","user_evidence","evidence_feedback","model_rationale"],
                    "properties": {
                        "index": {"type": "integer"},
                        "verdict": {"type": "string", "enum":["support","contradict","irrelevant"]},
                        "score": {"type": "integer"},
                        "user_evidence": {"type": "string"},
                        "evidence_feedback": {"type": "string"},
                        "model_rationale": {"type": "string"}
                    },
                    "additionalProperties": False
                }
            }
        }
    }
}

# ---------- LLM JSON 보정 레이어 ----------
def coerce_response(data: Dict[str, Any], req: AnalyzeRequest) -> AnalyzeResponse:
    # 기본값
    out: Dict[str, Any] = {}
    out["correct_index"] = int(data.get("correct_index", req.correct_index))
    out["is_user_correct"] = bool(
        data.get("is_user_correct",
                 req.user_selected_index == out["correct_index"])
    )
    # per_choice 정렬/보정
    raw = data.get("per_choice") or []
    fixed_list = []
    by_index = {}
    for d in raw:
        if isinstance(d, dict) and "index" in d:
            by_index[d["index"]] = d

    for c in req.choices:
        src = by_index.get(c.index, {})
        fixed_list.append({
            "index": c.index,
            "verdict": src.get("verdict", "irrelevant"),
            "score": int(src.get("score", 0)),
            "user_evidence": req.evidence_map.get(c.index, ""),
            "evidence_feedback": src.get("evidence_feedback", ""),
            "model_rationale": src.get("model_rationale", ""),
        })
    out["per_choice"] = fixed_list

    # overall_feedback
    out["overall_feedback"] = data.get("overall_feedback", "")

    # scores
    s = data.get("scores") or {}
    if not isinstance(s, dict): s = {}
    correctness = 100 if out["is_user_correct"] else 0
    evq = int(sum(pc["score"] for pc in fixed_list) / max(1, len(fixed_list)))
    reasoning = int(s.get("reasoning", 70))
    overall = int(s.get("overall", (correctness + evq + reasoning)//3))
    out["scores"] = {
        "correctness": int(s.get("correctness", correctness)),
        "evidence_quality": int(s.get("evidence_quality", evq)),
        "reasoning": reasoning,
        "overall": overall,
    }

    # 최종 검증
    return AnalyzeResponse(**out)

# ---------- 엔드포인트 ----------
@router.post("/items/{item_id}/analysis", response_model=AnalyzeResponse)
def analyze_item(item_id: str, body: AnalyzeRequest):
    if item_id != body.item_id:
        raise HTTPException(status_code=400,
                            detail=f"item_id mismatch: path={item_id}, body={body.item_id}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    system = ("You are a meticulous Korean-language reading comprehension evaluator. "
              "Always reply with valid JSON only. No prose, no markdown.")
    user = build_prompt(body)

    # 1) JSON 스키마 강제 시도
    use_schema = True
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system},
                      {"role":"user","content":user}],
            temperature=0.2,
            response_format={"type":"json_schema", "json_schema": JSON_SCHEMA},
        )
    except Exception:
        # 일부 환경에서 json_schema 미지원이면 json_object로 폴백
        use_schema = False
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system},
                      {"role":"user","content":user}],
            temperature=0.2,
            response_format={"type":"json_object"},
        )

    content = resp.choices[0].message.content
    try:
        data = json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM non-JSON: {e}")

    # 2) 엄격 검증 → 실패 시 보정(coerce) 후 재검증
    try:
        return AnalyzeResponse(**data)
    except ValidationError:
        try:
            return coerce_response(data, body)
        except ValidationError as e:
            # 최종 실패
            raise HTTPException(status_code=500, detail=f"Bad JSON from LLM (after coerce): {e}")
