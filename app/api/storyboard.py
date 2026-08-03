"""Storyboard (콘티) endpoints: generate cuts, list/edit/delete panels."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

import os

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..image.base import ImageError
from ..llm.base import LLMError
from ..services import images as image_svc
from ..services import storyboard as svc
from ..services.lettering import LetteringError, letter_panel
from ..services.prompt_engine import build_panel_prompt
from ..storage import files
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


@router.post("/api/panels/{panel_id}/image")
def generate_image(panel_id: str) -> dict:
    try:
        return image_svc.generate_panel_image(panel_id)
    except ImageError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


@router.post("/api/panels/{panel_id}/upload-image")
async def upload_image(panel_id: str, file: UploadFile = File(...)) -> dict:
    """Directly attach an image to a cut (e.g. one made in the Gemini web app).
    Coexists with auto-generation — this just sets the cut's image."""
    panel = repo.get_panel(panel_id)
    if panel is None:
        raise HTTPException(status_code=404, detail="컷을 찾을 수 없습니다")
    ep = repo.get_episode(panel.episode_id)
    if ep is None:
        raise HTTPException(status_code=404, detail="회차를 찾을 수 없습니다")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="이미지 파일(png/jpg/webp/gif)만 가능합니다")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="빈 파일입니다")
    # keep the previous cut image + lettered version by moving them to panels/old/
    # (don't delete — the user may want the earlier take back)
    if panel.image_path:
        files.archive_file(panel.image_path)
    if panel.lettered_path:
        files.archive_file(panel.lettered_path)
    rel = files.save_bytes(ep.project_id, "panels", f"{panel_id}_up{ext}", data)
    repo.update_panel(panel_id, image_path=rel, lettered_path=None)  # new base image
    return {"image_path": rel}


@router.get("/api/panels/{panel_id}/prompt")
def get_prompt(panel_id: str) -> dict:
    """The assembled cut prompt (style + character outfit + scene) to paste into
    an external tool like the Gemini web app."""
    panel = repo.get_panel(panel_id)
    if panel is None:
        raise HTTPException(status_code=404, detail="컷을 찾을 수 없습니다")
    ep = repo.get_episode(panel.episode_id)
    project = repo.get_project(ep.project_id) if ep else None
    if project is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return {"prompt": build_panel_prompt(project, panel)}


@router.get("/api/panels/{panel_id}/image")
def get_image(panel_id: str) -> FileResponse:
    panel = repo.get_panel(panel_id)
    if panel is None or not panel.image_path:
        raise HTTPException(status_code=404, detail="컷 이미지가 없습니다")
    path = files.resolve(panel.image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다")
    return FileResponse(path)


@router.post("/api/panels/{panel_id}/letter")
def letter(panel_id: str) -> dict:
    try:
        return letter_panel(panel_id)
    except LetteringError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/api/panels/{panel_id}/lettered-image")
def get_lettered_image(panel_id: str) -> FileResponse:
    panel = repo.get_panel(panel_id)
    if panel is None or not panel.lettered_path:
        raise HTTPException(status_code=404, detail="대사 합성 이미지가 없습니다")
    path = files.resolve(panel.lettered_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다")
    return FileResponse(path)
