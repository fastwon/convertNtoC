"""Gemini (Google) provider — the free-tier default.

Uses the google-genai SDK. Model IDs and config field names come from the
installed SDK, not memory. Errors never include the API key.
"""
from __future__ import annotations

from typing import Any

import google.genai as genai
from google.genai import types

from .base import LLMError
from .util import parse_json_lenient

# Free-tier flash model; good enough for extraction/summarization.
DEFAULT_MODEL = "gemini-2.0-flash"


def _friendly_error(e: Exception) -> str:
    msg = str(e).lower()
    if "429" in msg or "resource_exhausted" in msg or "quota" in msg or "rate" in msg:
        return "무료 사용량 한도를 초과했습니다. 잠시(1분+) 후 다시 시도하거나, 한도가 회복되면 재시도하세요."
    if "api key" in msg or "401" in msg or "unauthenticated" in msg or "permission" in msg:
        return "Gemini 인증 실패: 설정에서 키를 확인하세요."
    if "not found" in msg or "404" in msg:
        return "Gemini 모델을 찾을 수 없습니다 (모델명 확인 필요)."
    return "Gemini 호출 실패 (네트워크/키를 확인하세요)."


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
            raise LLMError(_friendly_error(e)) from e
        return resp.text or ""

    def generate_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        schema: dict | None = None,  # noqa: ARG002 - Gemini relies on JSON mode + prompt
        max_tokens: int = 4096,
    ) -> Any:
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )
        try:
            resp = self._client.models.generate_content(
                model=self._model, contents=prompt, config=config
            )
        except Exception as e:  # noqa: BLE001
            raise LLMError(_friendly_error(e)) from e
        try:
            return parse_json_lenient(resp.text or "")
        except Exception as e:  # noqa: BLE001
            raise LLMError("Gemini가 올바른 JSON을 반환하지 않았습니다") from e
