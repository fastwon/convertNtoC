"""Gemini (Google) provider — the free-tier default.

Uses the google-genai SDK. Model IDs and config field names come from the
installed SDK, not memory. Errors never include the API key.
"""
from __future__ import annotations

import google.genai as genai
from google.genai import types

from .base import LLMError

# Free-tier flash model; good enough for extraction/summarization.
DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def validate(self) -> tuple[bool, str]:
        try:
            # Listing models is a cheap authenticated call.
            next(iter(self._client.models.list()), None)
            return True, "유효한 Gemini 키입니다"
        except Exception as e:  # noqa: BLE001 - map any SDK error to a safe message
            msg = str(e).lower()
            if "api key" in msg or "permission" in msg or "unauthenticated" in msg or "401" in msg:
                return False, "인증 실패: Gemini 키가 올바르지 않습니다"
            if "quota" in msg or "429" in msg:
                return False, "요청 한도 초과: 잠시 후 다시 시도하세요"
            return False, "Gemini 키 검증에 실패했습니다 (네트워크/키 확인)"

    def generate_text(self, prompt: str, *, system: str | None = None, max_tokens: int = 2048) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        )
        try:
            resp = self._client.models.generate_content(
                model=self._model, contents=prompt, config=config
            )
        except Exception as e:  # noqa: BLE001
            raise LLMError("Gemini 호출 실패") from e
        return resp.text or ""
