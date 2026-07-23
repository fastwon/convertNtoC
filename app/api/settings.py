"""Settings / API-key endpoints.

POST validates before storing. GET reports presence + a masked hint, never the
raw key. Also exposes the free_mode toggle (Gemini free vs Claude).
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.validation import (
    mask_secret,
    validate_anthropic_key,
    validate_gemini_key,
    validate_image_key,
)
from ..storage import config, keys

router = APIRouter(prefix="/api/settings", tags=["settings"])


class KeyBody(BaseModel):
    key: str


class FreeModeBody(BaseModel):
    enabled: bool


def _slot(name: str) -> dict:
    val = keys.get_key(name)
    return {"present": bool(val), "masked": mask_secret(val)}


@router.get("/status")
def status() -> dict:
    anthropic_slot = _slot(keys.ANTHROPIC)
    gemini_slot = _slot(keys.GEMINI)
    image_slot = _slot(keys.IMAGE)
    free_mode = config.is_free_mode()
    # ready = the key required by the active mode is present
    ready = gemini_slot["present"] if free_mode else anthropic_slot["present"]
    return {
        "free_mode": free_mode,
        "active_provider": "gemini" if free_mode else "claude",
        "anthropic": anthropic_slot,
        "gemini": gemini_slot,
        "image": image_slot,
        "ready": ready,
    }


@router.post("/free-mode")
def set_free_mode(body: FreeModeBody) -> dict:
    config.set_free_mode(body.enabled)
    return {"free_mode": body.enabled}


def _save(name: str, key: str, validator) -> dict:
    ok, message = validator(key)
    if ok:
        keys.set_key(name, key.strip())
    return {"ok": ok, "message": message, "masked": mask_secret(key.strip()) if ok else None}


@router.post("/anthropic")
def set_anthropic(body: KeyBody) -> dict:
    return _save(keys.ANTHROPIC, body.key, validate_anthropic_key)


@router.post("/gemini")
def set_gemini(body: KeyBody) -> dict:
    return _save(keys.GEMINI, body.key, validate_gemini_key)


@router.post("/image")
def set_image(body: KeyBody) -> dict:
    return _save(keys.IMAGE, body.key, validate_image_key)


@router.delete("/anthropic")
def delete_anthropic() -> dict:
    keys.delete_key(keys.ANTHROPIC)
    return {"ok": True}


@router.delete("/gemini")
def delete_gemini() -> dict:
    keys.delete_key(keys.GEMINI)
    return {"ok": True}


@router.delete("/image")
def delete_image() -> dict:
    keys.delete_key(keys.IMAGE)
    return {"ok": True}
