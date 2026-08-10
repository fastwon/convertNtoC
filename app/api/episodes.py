"""Episode endpoints. An episode is one uploaded chapter of the novel; its text
is the input to character extraction / storyboard generation in later P4 steps.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..paths import exports_dir
from ..services.export import ExportError, save_export
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


@router.post("/api/episodes/{episode_id}/export")
def export(episode_id: str, format: str = "png") -> dict:
    """Save the episode's finished cuts to the user's exports folder.

    Writes server-side (reliable inside the PyWebView shell, where browser blob
    downloads are dropped) and returns the saved path + folder.
    """
    e = repo.get_episode(episode_id)
    if e is None:
        raise HTTPException(status_code=404, detail="회차를 찾을 수 없습니다")
    try:
        path = save_export(episode_id, format, e.number)
    except ExportError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    return {"path": str(path), "folder": str(path.parent), "filename": path.name}


@router.post("/api/exports/open")
def open_exports_folder() -> dict:
    """Open the exports folder in the OS file manager (Windows Explorer)."""
    folder = exports_dir()
    try:
        os.startfile(folder)  # type: ignore[attr-defined]  # Windows-only
    except OSError as err:
        raise HTTPException(status_code=500, detail=f"폴더를 열 수 없습니다: {err}") from err
    return {"folder": str(folder)}
