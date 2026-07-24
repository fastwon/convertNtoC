"""Global memory endpoints: world bible, memory preview, episode summarization."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..llm.base import LLMError
from ..services import memory as svc
from ..storage import repository as repo

router = APIRouter(tags=["memory"])


class WorldBibleBody(BaseModel):
    world_bible: str


@router.get("/api/projects/{project_id}/world-bible")
def get_world_bible(project_id: str) -> dict:
    if repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    gm = repo.get_global_memory(project_id)
    return {"world_bible": gm.world_bible if gm else "", "updated_at": gm.updated_at if gm else None}


@router.put("/api/projects/{project_id}/world-bible")
def set_world_bible(project_id: str, body: WorldBibleBody) -> dict:
    if repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    gm = repo.set_global_memory(project_id, body.world_bible)
    return {"world_bible": gm.world_bible if gm else "", "updated_at": gm.updated_at if gm else None}


@router.get("/api/projects/{project_id}/memory")
def preview_memory(project_id: str, before: int | None = None) -> dict:
    """Exactly what gets injected as the cached system prefix."""
    try:
        text = svc.build_global_memory(project_id, before_episode_number=before)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"memory": text, "chars": len(text)}


@router.post("/api/episodes/{episode_id}/summarize")
def summarize(episode_id: str) -> dict:
    try:
        return svc.summarize_episode(episode_id)
    except LLMError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
