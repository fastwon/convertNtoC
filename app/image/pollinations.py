"""Pollinations — a free, keyless image endpoint. Good for seeing cuts render
immediately; character consistency is weak (no reference-image conditioning).
That's a deliberate tradeoff — see docs/DESIGN.md §7.
"""
from __future__ import annotations

import urllib.parse

import httpx

from .base import ImageError

BASE = "https://image.pollinations.ai/prompt/"


class PollinationsGenerator:
    name = "pollinations"

    def __init__(self, model: str = "flux") -> None:
        self._model = model

    def generate(self, prompt: str, *, width: int = 1024, height: int = 1024) -> bytes:
        url = BASE + urllib.parse.quote(prompt)
        params = {
            "width": width,
            "height": height,
            "nologo": "true",
            "model": self._model,
        }
        try:
            r = httpx.get(url, params=params, timeout=180, follow_redirects=True)
            r.raise_for_status()
        except Exception as e:  # noqa: BLE001
            raise ImageError("이미지 생성 요청 실패 (네트워크 확인)") from e
        if not r.headers.get("content-type", "").startswith("image"):
            raise ImageError("이미지가 반환되지 않았습니다")
        return r.content
