import uuid
from typing import Dict, Any, List

_ITEMS: Dict[str, Dict[str, Any]] = {}
_CHOICES: Dict[str, List[Dict[str, Any]]] = {}

def new_id() -> str:
    return str(uuid.uuid4())

def save_item_internal(item: Dict[str, Any], choices: List[Dict[str, Any]]) -> str:
    item_id = item.get("id") or new_id()
    item["id"] = item_id
    _ITEMS[item_id] = item
    cleaned = []
    for idx, c in enumerate(choices):
        c2 = dict(c); c2["index"] = idx
        cleaned.append(c2)
    _CHOICES[item_id] = cleaned
    return item_id

def get_item_internal(item_id: str) -> Dict[str, Any]:
    return _ITEMS.get(item_id)

def get_choices_internal(item_id: str) -> List[Dict[str, Any]]:
    return _CHOICES.get(item_id, [])

def list_items_public(limit=20, offset=0) -> List[Dict[str, Any]]:
    items = list(_ITEMS.values())[offset:offset+limit]
    res = []
    for it in items:
        item_id = it["id"]
        res.append({
            "id": it["id"],
            "title": it["title"],
            "question": it["question"],
            "generated_passage": it["generated_passage"],
            "sentences": it["sentences"],
            "quality": it.get("quality", {}),
            "rag_eval": it.get("rag_eval", {}),
            "topic": it["topic"],
            "difficulty": it["difficulty"],
            "choices": [{"index": c["index"], "text": c["text"]} for c in _CHOICES.get(item_id, [])],
        })
    return res
