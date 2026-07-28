"""Gemini image generation (Nano Banana). Higher quality + reference-image
consistency, but the free tier is effectively blocked (429, needs billing) — so
this is the paid option users switch to after enabling Google Cloud billing.
Reuses the same Gemini key as the LLM.
"""
from __future__ import annotations

import google.genai as genai
from google.genai import types

from .base import ImageError

DEFAULT_MODEL = "gemini-2.5-flash-image"


def _friendly(e: Exception) -> str:
    msg = str(e).lower()
    if "429" in msg or "resource_exhausted" in msg or "quota" in msg or "billing" in msg:
        return "Gemini 이미지 무료 한도 초과/미지원입니다. Google Cloud 결제 등록이 필요합니다."
    if "api key" in msg or "401" in msg or "permission" in msg:
        return "Gemini 인증 실패: 키를 확인하세요."
    if "not found" in msg or "404" in msg:
        return "Gemini 이미지 모델을 찾을 수 없습니다."
    return "Gemini 이미지 생성 실패."


class GeminiImageGenerator:
    name = "gemini"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(
        self, prompt: str, *, width: int = 1024, height: int = 1024, seed: int | None = None
    ) -> bytes:
        # Gemini image gen doesn't take width/height/seed params — those are
        # accepted for interface parity and ignored.
        try:
            resp = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
            )
        except Exception as e:  # noqa: BLE001
            raise ImageError(_friendly(e)) from e
        try:
            parts = resp.candidates[0].content.parts
        except Exception as e:  # noqa: BLE001
            raise ImageError("Gemini 이미지 응답이 비어 있습니다") from e
        for part in parts:
            inline = getattr(part, "inline_data", None)
            if inline is not None and inline.data:
                return inline.data
        raise ImageError("Gemini가 이미지를 반환하지 않았습니다")
