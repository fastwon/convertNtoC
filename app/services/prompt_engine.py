"""Deterministic image-prompt assembly.

The LLM produced the panel breakdown (scene + which characters/looks). The final
image prompt — [style] + [character looks] + [scene] — is assembled by plain code
here, not by a model, so it's reproducible and cache-friendly (DESIGN §6.5).
"""
from __future__ import annotations

from ..storage import repository as repo
from ..storage.models import Panel, Project


def _appearance_desc(project_id: str, name: str, label: str) -> str | None:
    """Outfit (외형) for a character's specific look, falling back to the persona
    (인물 설명) when no outfit has been set yet."""
    for c in repo.list_characters(project_id):
        if c.name != name:
            continue
        looks = repo.list_appearances(c.id)
        chosen = next((a for a in looks if a.label == label), None)
        if chosen is None:
            chosen = next((a for a in looks if a.is_default), looks[0] if looks else None)
        outfit = chosen.description.strip() if chosen else ""
        if outfit:
            return outfit
        persona = c.traits.get("description", "") if isinstance(c.traits, dict) else ""
        return str(persona).strip() or None
    return None


def build_panel_prompt(project: Project, panel: Panel) -> str:
    # Lead with the scene so THIS cut's content dominates; style/character text
    # (shared across cuts) comes after as conditioning, not the headline.
    parts: list[str] = []

    if panel.scene.strip():
        parts.append(f"장면: {panel.scene.strip()}")

    for pc in panel.characters or []:
        name = pc.get("name", "")
        label = pc.get("appearance_label", "기본")
        desc = _appearance_desc(project.id, name, label)
        if desc:
            tag = f"{name}" if label in ("", "기본") else f"{name}({label})"
            parts.append(f"{tag}: {desc}")

    style = project.style_prompt.strip()
    if style:
        parts.append(f"화풍: {style}")

    # dialogue/speech goes on later (P7 speech bubbles) — keep text out of the art
    parts.append("만화 컷 일러스트, 글자·말풍선 없이 그림만")
    return ", ".join(parts)
