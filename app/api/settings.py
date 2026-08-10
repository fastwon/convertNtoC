"""Settings / API-key endpoints.

POST validates before storing. GET reports presence + a masked hint, never the
raw key. Also exposes the free_mode toggle (Gemini free vs Claude).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.validation import (
    mask_secret,
    validate_anthropic_key,
    validate_gemini_key,
)
from ..storage import config, keys

router = APIRouter(prefix="/api/settings", tags=["settings"])


class KeyBody(BaseModel):
    key: str


class FreeModeBody(BaseModel):
    enabled: bool


class ImageProviderBody(BaseModel):
    provider: str


def _slot(name: str) -> dict:
    val = keys.get_key(name)
    return {"present": bool(val), "masked": mask_secret(val)}


@router.get("/status")
def status() -> dict:
    anthropic_slot = _slot(keys.ANTHROPIC)
    gemini_slot = _slot(keys.GEMINI)
    free_mode = config.is_free_mode()
    # ready = the key required by the active mode is present
    ready = gemini_slot["present"] if free_mode else anthropic_slot["present"]
    image_provider = config.get_image_provider()
    return {
        "free_mode": free_mode,
        "active_provider": "gemini" if free_mode else "claude",
        "anthropic": anthropic_slot,
        "gemini": gemini_slot,
        "image_provider": image_provider,
        "ready": ready,
    }


@router.post("/free-mode")
def set_free_mode(body: FreeModeBody) -> dict:
    config.set_free_mode(body.enabled)
    return {"free_mode": body.enabled}


@router.post("/image-provider")
def set_image_provider(body: ImageProviderBody) -> dict:
    try:
        config.set_image_provider(body.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"image_provider": body.provider}


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


@router.delete("/anthropic")
def delete_anthropic() -> dict:
    keys.delete_key(keys.ANTHROPIC)
    return {"ok": True}


@router.delete("/gemini")
def delete_gemini() -> dict:
    keys.delete_key(keys.GEMINI)
    return {"ok": True}
