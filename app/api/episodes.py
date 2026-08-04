"""Episode endpoints. An episode is one uploaded chapter of the novel; its text
is the input to character extraction / storyboard generation in later P4 steps.
"""
from __future__ import annotations

from dataclasses import asdict
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from ..services.export import ExportError, export_episode
from ..storage import repository as repo

router = APIRouter(tags=["episodes"])


class EpisodeCreate(BaseModel):
    number: int | None = None  # auto = max(existing)+1
    raw_text: str = ""


class EpisodeText(BaseModel):
    raw_text: str


@router.get("/api/projects/{project_id}/episodes")
def list_episodes(project_id: str) -> list[dict]:
    if repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return [asdict(e) for e in repo.list_episodes(project_id)]


@router.post("/api/projects/{project_id}/episodes")
def create_episode(project_id: str, body: EpisodeCreate) -> dict:
    if repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    existing = repo.list_episodes(project_id)
    number = body.number if body.number is not None else (max((e.number for e in existing), default=0) + 1)
    if number <= 0:
        raise HTTPException(status_code=400, detail="회차 번호는 1 이상이어야 합니다")
    if any(e.number == number for e in existing):
        raise HTTPException(status_code=409, detail=f"{number}화가 이미 존재합니다")
    e = repo.create_episode(project_id, number, body.raw_text)
    return asdict(e)


@router.get("/api/episodes/{episode_id}")
def get_episode(episode_id: str) -> dict:
    e = repo.get_episode(episode_id)
    if e is None:
        raise HTTPException(status_code=404, detail="회차를 찾을 수 없습니다")
    return asdict(e)


@router.put("/api/episodes/{episode_id}/text")
def update_text(episode_id: str, body: EpisodeText) -> dict:
    e = repo.get_episode(episode_id)
    if e is None:
        raise HTTPException(status_code=404, detail="회차를 찾을 수 없습니다")
    repo.update_episode_text(episode_id, body.raw_text)
    return asdict(repo.get_episode(episode_id))


@router.delete("/api/episodes/{episode_id}")
def delete_episode(episode_id: str) -> dict:
    e = repo.get_episode(episode_id)
    if e is None:
        raise HTTPException(status_code=404, detail="회차를 찾을 수 없습니다")
    repo.delete_episode(episode_id)
    return {"ok": True}


@router.get("/api/episodes/{episode_id}/export")
def export(episode_id: str, format: str = "png") -> Response:
    """Download the episode's finished cuts as png (webtoon strip) / pdf / zip."""
    e = repo.get_episode(episode_id)
    if e is None:
        raise HTTPException(status_code=404, detail="회차를 찾을 수 없습니다")
    try:
        data, media_type, ext = export_episode(episode_id, format)
    except ExportError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    # ASCII fallback + RFC 5987 UTF-8 name so Korean filenames survive
    name = f"{e.number}화"
    disposition = (
        f"attachment; filename=\"episode-{e.number}.{ext}\"; "
        f"filename*=UTF-8''{quote(name)}.{ext}"
    )
    return Response(content=data, media_type=media_type,
                    headers={"Content-Disposition": disposition})
