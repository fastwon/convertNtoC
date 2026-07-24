"""Character extraction + new-vs-existing cross-check.

Given an episode's text and the project's existing character bank, ask the LLM
to list every named character, flagging whether each is new or matches an
existing bank entry. The result is returned for user confirmation (P4d); nothing
is written to the bank here.
"""
from __future__ import annotations

from typing import Any

from ..llm import factory
from ..llm.base import LLMError
from ..storage import repository as repo

# JSON Schema (used by providers that support structured output, e.g. Claude).
EXTRACTION_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "is_new": {"type": "boolean"},
                    "matched_character_id": {"type": ["string", "null"]},
                    "traits": {"type": "string"},
                },
                "required": ["name", "is_new", "matched_character_id", "traits"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["characters"],
    "additionalProperties": False,
}

SYSTEM = (
    "너는 소설 텍스트에서 등장인물을 정확히 추출하는 분석 도우미다. "
    "설명 없이 지정된 JSON만 출력한다."
)

# Guard against pathological input sizes on the free tier.
MAX_TEXT_CHARS = 20000


def _build_prompt(raw_text: str, existing: list[dict]) -> str:
    if existing:
        bank = "\n".join(f"- id={c['id']}, 이름={c['name']}" for c in existing)
    else:
        bank = "(없음 — 아직 등록된 인물이 없음)"
    text = raw_text[:MAX_TEXT_CHARS]
    return f"""다음은 웹툰화할 소설의 한 회차다. 등장인물을 모두 찾아라.

[이미 등록된 캐릭터 뱅크]
{bank}

[규칙]
- 각 등장인물마다 다음을 판단한다:
  - name: 인물 이름
  - is_new: 위 캐릭터 뱅크에 없는 새 인물이면 true, 이미 있는 인물이면 false
  - matched_character_id: 뱅크의 기존 인물과 동일인이면 그 id, 아니면 null
  - traits: 외모·성격 특징을 한 문장으로 요약
- 뱅크의 인물과 동일인으로 판단되면 반드시 is_new=false 로 하고 matched_character_id 를 채운다.
- 이름이 없는 단역·군중은 제외한다.

[출력 형식] 아래 JSON 형식으로만 출력한다:
{{"characters":[{{"name":"홍길동","is_new":true,"matched_character_id":null,"traits":"20대 남성, 검은 머리, 과묵함"}}]}}

[소설 본문]
{text}
"""


def _validate_result(data: Any, existing_by_id: dict) -> list[dict]:
    if not isinstance(data, dict) or not isinstance(data.get("characters"), list):
        raise LLMError("추출 결과 형식이 올바르지 않습니다")
    out: list[dict] = []
    for item in data["characters"]:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        matched = item.get("matched_character_id")
        # drop hallucinated ids that aren't in this project's bank
        if matched not in existing_by_id:
            matched = None
        # for existing characters, surface the bank's current description so the
        # user can compare before deciding whether to update it
        current = None
        if matched:
            traits = existing_by_id[matched].traits
            current = str(traits.get("description", "")).strip() if isinstance(traits, dict) else ""
        out.append(
            {
                "name": str(item["name"]).strip(),
                "is_new": bool(item.get("is_new", matched is None)),
                "matched_character_id": matched,
                "traits": str(item.get("traits", "")).strip(),
                "current_traits": current,
            }
        )
    return out


def extract_characters(episode_id: str) -> dict:
    episode = repo.get_episode(episode_id)
    if episode is None:
        raise LLMError("회차를 찾을 수 없습니다")
    if not episode.raw_text.strip():
        raise LLMError("회차 본문이 비어 있습니다")

    bank = repo.list_characters(episode.project_id)
    existing = [{"id": c.id, "name": c.name} for c in bank]
    existing_by_id = {c.id: c for c in bank}

    provider = factory.get_provider()  # raises LLMError if the active key is missing
    prompt = _build_prompt(episode.raw_text, existing)
    data = provider.generate_json(prompt, system=SYSTEM, schema=EXTRACTION_SCHEMA)

    characters = _validate_result(data, existing_by_id)
    return {"provider": provider.name, "characters": characters}
