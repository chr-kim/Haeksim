from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
import os, json, re
from openai import OpenAI

router = APIRouter(prefix="/api/v1", tags=["chat"])

# -------- 공용 스키마 --------
class Choice(BaseModel):
    index: int
    text: str

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    item_id: str
    question: str
    passage: str
    choices: List[Choice]
    correct_index: int
    user_selected_index: int
    evidence_map: Dict[int, str] = Field(default_factory=dict)
    history: List[ChatTurn] = Field(default_factory=list)
    message: str

class ChatResponse(BaseModel):
    reply: str

SYSTEM_PROMPT = (
    "당신은 한국어 독해 학습코치입니다. 항상 지문 근거를 바탕으로, 간결하고 단계적으로 설명하세요. "
    "지문과 무관한 추측은 피하고, 인용은 짧게 하세요."
)

def _choices_table(choices: List[Choice]) -> str:
    """표기 번호(no: 1~N)와 index(0~N-1)를 함께 보여주는 표 형식 문자열."""
    rows = []
    for c in choices:
        rows.append(f"- no: {c.index + 1} (index: {c.index}) | text: {c.text}")
    return "\n".join(rows)

def _extract_no_list(message: str, max_no: int) -> List[int]:
    """
    '1번', ' 2 번 ' 등 패턴에서 표기 번호(no)만 추출.
    숫자만 대상으로 하며 1..max_no 범위만 유효.
    """
    nos = []
    for m in re.finditer(r"(?<!\d)(\d+)\s*번", message):
        try:
            n = int(m.group(1))
            if 1 <= n <= max_no:
                nos.append(n)
        except Exception:
            pass
    # 중복 제거, 입력 순서 유지
    seen = set()
    dedup = []
    for n in nos:
        if n not in seen:
            seen.add(n)
            dedup.append(n)
    return dedup

def build_context(req: ChatRequest) -> str:
    return f"""
[문항 컨텍스트]
- 문항ID: {req.item_id}
- 문제 질문: {req.question}

[지문]
{req.passage}

[선지 목록]
(아래는 화면 표기 번호(no)와 내부 index의 매핑표입니다. no는 1부터, index는 0부터 시작합니다.)
{_choices_table(req.choices)}

[정답/선택]
- 실제 정답 index: {req.correct_index}
- 나의 선택 index: {req.user_selected_index}

[내가 적은 선지별 근거]
{json.dumps(req.evidence_map, ensure_ascii=False, indent=2)}

[번호 해석 규칙]
- 사용자가 "n번"이라고 말하면, 이는 표기 번호(no)이며 choices 배열의 index는 (n-1)입니다.
- 예: "1번" → index 0, "2번" → index 1, ...
""".strip()

# -------- 엔드포인트 --------
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)

    # 1) 시스템 + 컨텍스트
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": build_context(req)})

    # 2) 직전 히스토리(최대 12턴) 재구성
    for turn in req.history[-12:]:
        messages.append({"role": turn.role, "content": turn.content})

    # 3) 사용자가 이번 질문에서 언급한 "n번" → index 매핑 힌트를 자동 삽입
    no_list = _extract_no_list(req.message, max_no=len(req.choices))
    if no_list:
        idx_list = [n - 1 for n in no_list]
        hint = (
            "[번호 참조 해석]\n"
            f"- 이번 질문 원문: {req.message}\n"
            f"- 감지된 표기 번호(no): {no_list}\n"
            f"- index로 환산: {idx_list}\n"
            "- 위 환산을 기준으로 해당 선택지를 참조해서 답하세요."
        )
        messages.append({"role": "system", "content": hint})

    # 4) 실제 사용자 메시지
    messages.append({"role": "user", "content": req.message})

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=messages,
        )
        reply = resp.choices[0].message.content
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail={f"LLM chat failed: {e}"})
