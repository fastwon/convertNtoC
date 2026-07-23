"""Claude (Anthropic) provider — the high-quality default when free mode is off.

Follows the current Anthropic SDK shape (messages.create; adaptive thinking and
prompt caching get layered in at the call sites that need them, P5+). Default
model here is Sonnet for general text; role-specific models are chosen by the
services that call this (opus for reasoning, haiku for classification).
"""
from __future__ import annotations

import anthropic

from .base import LLMError

DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider:
    name = "claude"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = anthropic.Anthropic(api_key=api_key, max_retries=0, timeout=30.0)
        self._model = model

    def validate(self) -> tuple[bool, str]:
        try:
            self._client.models.list()
            return True, "유효한 Anthropic 키입니다"
        except anthropic.AuthenticationError:
            return False, "인증 실패: 키가 올바르지 않습니다"
        except anthropic.APIConnectionError:
            return False, "네트워크 오류: 인터넷 연결을 확인하세요"
        except Exception:  # noqa: BLE001
            return False, "Anthropic 키 검증에 실패했습니다"

    def generate_text(self, prompt: str, *, system: str | None = None, max_tokens: int = 2048) -> str:
        kwargs: dict = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        try:
            msg = self._client.messages.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            raise LLMError("Claude 호출 실패") from e
        return "".join(b.text for b in msg.content if b.type == "text")
