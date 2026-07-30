"""Storyboard (콘티) generation: break an episode into comic cuts.

The LLM splits the episode text into ordered panels — each with a visual scene
description, which characters appear (and which of their looks), and dialogue.
The project's global memory (style + character bank + world + prior summaries)
is sent as the cached system prefix so cuts stay consistent across episodes.

This produces the *panel breakdown*. The final image prompt string is assembled
by plain code in P6b, not by the model.
"""
from __future__ import annotations

from typing import Any

from ..llm import factory
from ..llm.base import LLMError
from ..storage import repository as repo
from .memory import build_global_memory

MAX_TEXT_CHARS = 20000

STORYBOARD_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "panels": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene": {"type": "string"},
                    "characters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "appearance_label": {"type": "string"},
                            },
                            "required": ["name", "appearance_label"],
                            "additionalProperties": False,
                        },
                    },
                    "dialogue": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["speech", "thought", "narration"]},
                                "speaker": {"type": "string"},
                                "text": {"type": "string"},
                            },
                            "required": ["type", "speaker", "text"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["scene", "characters", "dialogue"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["panels"],
    "additionalProperties": False,
}

SYSTEM_SUFFIX = (
    "\n\n너는 위 설정을 따르는 웹툰 콘티 작가다. 회차 본문을 만화 컷(패널)으로 나눈다. "
    "설명 없이 지정된 JSON만 출력한다."
)

INSTRUCTION = """위 본문을 만화 컷으로 나눠라.

규칙:
- 본문에 실제로 있는 장면만 컷으로 만든다. 없는 사건을 지어내지 마라.
- 각 컷(panel)마다:
  - scene: 그 컷의 시각적 묘사(인물의 위치·표정·행동·배경·구도). 그림을 위한 묘사.
  - characters: 그 컷에 등장하는 인물. 각 인물의 name과, 위 캐릭터 뱅크의 어느 모습인지 appearance_label(예: "기본", "10년 전"). 회상 장면이면 과거 모습 라벨을 쓴다. 등장 인물이 없으면 빈 배열.
  - dialogue: 그 컷의 텍스트. 각 항목은 type, speaker, text.
    - type: "speech"(직접 소리 내어 하는 말) / "thought"(속으로 하는 생각) / "narration"(지문·상황 설명, 인물의 말이 아님)
    - speaker: 말하거나 생각하는 인물 이름. narration은 빈 문자열.
    - text: 내용.
    텍스트가 없으면 빈 배열.
- 컷 순서는 본문 진행 순서를 따른다.
- 분량에 맞게 적당한 수의 컷으로 나눈다(너무 잘게 쪼개지 말 것)."""


def _validate(data: Any, valid_names: set[str], label_by_name: dict[str, set[str]]) -> list[dict]:
    # accept {"panels": [...]} or a bare [...] (Gemini often drops the wrapper)
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict) and isinstance(data.get("panels"), list):
        raw = data["panels"]
    else:
        raise LLMError("콘티 결과 형식이 올바르지 않습니다")
    panels: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        scene = str(item.get("scene", "")).strip()
        if not scene:
            continue
        chars = []
        for ch in item.get("characters", []) or []:
            if not isinstance(ch, dict) or not ch.get("name"):
                continue
            name = str(ch["name"]).strip()
            label = str(ch.get("appearance_label", "")).strip() or "기본"
            # keep only bank characters; snap unknown labels to an existing look
            if name in valid_names:
                if label not in label_by_name.get(name, set()):
                    label = next(iter(label_by_name.get(name, {"기본"})), "기본")
                chars.append({"name": name, "appearance_label": label})
        dlg = []
        for d in item.get("dialogue", []) or []:
            if isinstance(d, dict) and d.get("text"):
                dtype = str(d.get("type", "speech")).strip().lower()
                if dtype not in ("speech", "thought", "narration"):
                    dtype = "speech"
                dlg.append(
                    {
                        "type": dtype,
                        "speaker": str(d.get("speaker", "")).strip(),
                        "text": str(d["text"]).strip(),
                    }
                )
        panels.append({"scene": scene, "characters": chars, "dialogue": dlg})
    return panels


def generate_storyboard(episode_id: str) -> dict:
    episode = repo.get_episode(episode_id)
    if episode is None:
        raise LLMError("회차를 찾을 수 없습니다")
    if not episode.raw_text.strip():
        raise LLMError("회차 본문이 비어 있습니다")

    bank = repo.list_characters(episode.project_id)
    valid_names = {c.name for c in bank}
    label_by_name = {c.name: {a.label for a in repo.list_appearances(c.id)} for c in bank}

    system = build_global_memory(episode.project_id, before_episode_number=episode.number)
    system += SYSTEM_SUFFIX
    prompt = f"[{episode.number}화 본문]\n{episode.raw_text[:MAX_TEXT_CHARS]}\n\n{INSTRUCTION}"

    provider = factory.get_provider()
    data = provider.generate_json(prompt, system=system, schema=STORYBOARD_SCHEMA, max_tokens=8192)
    panels = _validate(data, valid_names, label_by_name)
    if not panels:
        raise LLMError("생성된 컷이 없습니다")

    saved = repo.replace_episode_panels(episode_id, panels)
    repo.set_episode_status(episode_id, "storyboarded")
    return {
        "provider": provider.name,
        "panels": [
            {"id": p.id, "order": p.order, "scene": p.scene,
             "characters": p.characters, "dialogue": p.dialogue}
            for p in saved
        ],
        "usage": getattr(provider, "last_usage", None),
    }
