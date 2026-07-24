"""Character extraction + character bank (CRUD, confirm, reference images).

Extraction returns candidates for user confirmation. Confirm persists the
selected new characters into the project's bank. Reference images are stored
as local files; face embeddings are added later (P6, once the image provider
is chosen).
"""
from __future__ import annotations

import os
from dataclasses import asdict

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..llm.base import LLMError
from ..services import characters as svc
from ..storage import files
from ..storage import repository as repo

router = APIRouter(tags=["characters"])

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


# --- extraction -------------------------------------------------------------

@router.post("/api/episodes/{episode_id}/extract-characters")
def extract(episode_id: str) -> dict:
    try:
        return svc.extract_characters(episode_id)
    except LLMError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


class ConfirmItem(BaseModel):
    name: str
    traits: str = ""
    save: bool = True
    matched_character_id: str | None = None  # set -> update that bank entry instead


class ConfirmBody(BaseModel):
    characters: list[ConfirmItem]


@router.post("/api/episodes/{episode_id}/confirm-characters")
def confirm(episode_id: str, body: ConfirmBody) -> dict:
    """Persist confirmed characters.

    New characters are created; existing ones are only updated when the user
    explicitly approved it (save=True with matched_character_id). Defaulting to
    "don't touch" keeps the bank — and therefore visual consistency — stable.
    """
    ep = repo.get_episode(episode_id)
    if ep is None:
        raise HTTPException(status_code=404, detail="회차를 찾을 수 없습니다")
    bank = repo.list_characters(ep.project_id)
    existing_names = {c.name for c in bank}
    existing_ids = {c.id for c in bank}

    saved, updated = [], []
    for item in body.characters:
        if not item.save:
            continue
        name = item.name.strip()
        if not name:
            continue
        if item.matched_character_id and item.matched_character_id in existing_ids:
            # approved update of an existing bank entry (description only;
            # renaming stays a deliberate action in the character bank UI)
            ch = repo.update_character(
                item.matched_character_id, traits={"description": item.traits.strip()}
            )
            if ch:
                updated.append(asdict(ch))
            continue
        if name in existing_names:
            continue  # same name already in the bank -> don't duplicate
        ch = repo.create_character(ep.project_id, name, {"description": item.traits.strip()})
        existing_names.add(name)
        saved.append(asdict(ch))
    return {"saved": saved, "updated": updated}


# --- bank CRUD --------------------------------------------------------------

@router.get("/api/projects/{project_id}/characters")
def list_characters(project_id: str) -> list[dict]:
    if repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return [asdict(c) for c in repo.list_characters(project_id)]


class CharacterPatch(BaseModel):
    name: str | None = None
    traits: str | None = None


@router.patch("/api/characters/{character_id}")
def update_character(character_id: str, body: CharacterPatch) -> dict:
    ch = repo.get_character(character_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")
    fields: dict = {}
    if body.name is not None:
        if not body.name.strip():
            raise HTTPException(status_code=400, detail="이름은 비울 수 없습니다")
        fields["name"] = body.name.strip()
    if body.traits is not None:
        fields["traits"] = {"description": body.traits.strip()}
    updated = repo.update_character(character_id, **fields) if fields else ch
    return asdict(updated)


@router.delete("/api/characters/{character_id}")
def delete_character(character_id: str) -> dict:
    if repo.get_character(character_id) is None:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")
    repo.delete_character(character_id)
    return {"ok": True}


# --- reference image --------------------------------------------------------

@router.post("/api/characters/{character_id}/ref-image")
async def upload_ref_image(character_id: str, file: UploadFile = File(...)) -> dict:
    ch = repo.get_character(character_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="이미지 파일(png/jpg/webp/gif)만 가능합니다")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="빈 파일입니다")
    rel = files.save_bytes(ch.project_id, "characters", f"{character_id}{ext}", data)
    updated = repo.update_character(character_id, ref_image_path=rel)
    return asdict(updated)


@router.get("/api/characters/{character_id}/ref-image")
def get_ref_image(character_id: str) -> FileResponse:
    ch = repo.get_character(character_id)
    if ch is None or not ch.ref_image_path:
        raise HTTPException(status_code=404, detail="참조 이미지가 없습니다")
    path = files.resolve(ch.ref_image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다")
    return FileResponse(path)
