"""Storyboard (콘티) endpoints: generate cuts, list/edit/delete panels."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..llm.base import LLMError
from ..services import storyboard as svc
from ..storage import repository as repo

router = APIRouter(tags=["storyboard"])


@router.post("/api/episodes/{episode_id}/storyboard")
def generate(episode_id: str) -> dict:
    try:
        return svc.generate_storyboard(episode_id)
    except LLMError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/api/episodes/{episode_id}/panels")
def list_panels(episode_id: str) -> list[dict]:
    if repo.get_episode(episode_id) is None:
        raise HTTPException(status_code=404, detail="회차를 찾을 수 없습니다")
    return [asdict(p) for p in repo.list_panels(episode_id)]


class PanelPatch(BaseModel):
    scene: str | None = None
    characters: list[dict[str, Any]] | None = None
    dialogue: list[dict[str, Any]] | None = None


@router.patch("/api/panels/{panel_id}")
def update_panel(panel_id: str, body: PanelPatch) -> dict:
    if repo.get_panel(panel_id) is None:
        raise HTTPException(status_code=404, detail="컷을 찾을 수 없습니다")
    fields = body.model_dump(exclude_unset=True)
    return asdict(repo.update_panel(panel_id, **fields))


@router.delete("/api/panels/{panel_id}")
def delete_panel(panel_id: str) -> dict:
    if repo.get_panel(panel_id) is None:
        raise HTTPException(status_code=404, detail="컷을 찾을 수 없습니다")
    repo.delete_panel(panel_id)
    return {"ok": True}
