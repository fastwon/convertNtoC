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

    def generate(
        self, prompt: str, *, width: int = 1024, height: int = 1024, seed: int | None = None
    ) -> bytes:
        url = BASE + urllib.parse.quote(prompt)
        params: dict = {
            "width": width,
            "height": height,
            "nologo": "true",
            "model": self._model,
        }
        if seed is not None:
            params["seed"] = seed
        try:
            r = httpx.get(url, params=params, timeout=180, follow_redirects=True)
            r.raise_for_status()
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise ImageError("인터넷 연결에 실패했습니다. 온라인 상태를 확인하세요.") from e
        except httpx.TimeoutException as e:
            raise ImageError("이미지 서버 응답이 지연됩니다. 잠시 후 다시 시도하세요.") from e
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            if code == 429:
                raise ImageError("이미지 서버가 혼잡합니다(429). 잠시 후 다시 시도하세요.") from e
            raise ImageError(f"이미지 생성 실패 (HTTP {code}).") from e
        except Exception as e:  # noqa: BLE001
            raise ImageError("이미지 생성 요청 실패 (네트워크를 확인하세요).") from e
        if not r.headers.get("content-type", "").startswith("image"):
            raise ImageError("이미지가 반환되지 않았습니다")
        return r.content
