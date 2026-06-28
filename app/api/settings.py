"""Settings / API-key endpoints.

POST validates (Anthropic via a real call, image via format check) and only
stores on success. GET reports presence + a masked hint, never the raw key.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.validation import mask_secret, validate_anthropic_key, validate_image_key
from ..storage import keys

router = APIRouter(prefix="/api/settings", tags=["settings"])


class KeyBody(BaseModel):
    key: str


def _slot(name: str) -> dict:
    val = keys.get_key(name)
    return {"present": bool(val), "masked": mask_secret(val)}


@router.get("/status")
def status() -> dict:
    anthropic_slot = _slot(keys.ANTHROPIC)
    image_slot = _slot(keys.IMAGE)
    return {
        "anthropic": anthropic_slot,
        "image": image_slot,
        "ready": anthropic_slot["present"],  # minimum to operate: Anthropic key
    }


@router.post("/anthropic")
def set_anthropic(body: KeyBody) -> dict:
    ok, message = validate_anthropic_key(body.key)
    if ok:
        keys.set_key(keys.ANTHROPIC, body.key.strip())
    return {"ok": ok, "message": message, "masked": mask_secret(body.key.strip()) if ok else None}


@router.post("/image")
def set_image(body: KeyBody) -> dict:
    ok, message = validate_image_key(body.key)
    if ok:
        keys.set_key(keys.IMAGE, body.key.strip())
    return {"ok": ok, "message": message, "masked": mask_secret(body.key.strip()) if ok else None}


@router.delete("/anthropic")
def delete_anthropic() -> dict:
    keys.delete_key(keys.ANTHROPIC)
    return {"ok": True}


@router.delete("/image")
def delete_image() -> dict:
    keys.delete_key(keys.IMAGE)
    return {"ok": True}
