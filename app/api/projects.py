"""Project CRUD endpoints. The project's style (style_prompt + image_model_ref)
is the locked default reused by every episode generation in later phases.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..storage import repository as repo

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    style_prompt: str = ""
    image_model_ref: str | None = None
    font_settings: dict[str, Any] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    style_prompt: str | None = None
    image_model_ref: str | None = None
    font_settings: dict[str, Any] | None = None


@router.get("")
def list_projects() -> list[dict]:
    return [asdict(p) for p in repo.list_projects()]


@router.post("")
def create_project(body: ProjectCreate) -> dict:
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="프로젝트 이름을 입력하세요")
    p = repo.create_project(
        body.name.strip(), body.style_prompt, body.image_model_ref, body.font_settings
    )
    return asdict(p)


@router.get("/{project_id}")
def get_project(project_id: str) -> dict:
    p = repo.get_project(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return asdict(p)


@router.patch("/{project_id}")
def update_project(project_id: str, body: ProjectUpdate) -> dict:
    if repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    fields = body.model_dump(exclude_unset=True)
    if "name" in fields and (fields["name"] is None or not str(fields["name"]).strip()):
        raise HTTPException(status_code=400, detail="프로젝트 이름은 비울 수 없습니다")
    p = repo.update_project(project_id, **fields)
    return asdict(p)


@router.delete("/{project_id}")
def delete_project(project_id: str) -> dict:
    if repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    repo.delete_project(project_id)
    return {"ok": True}
