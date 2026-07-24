"""Claude (Anthropic) provider — the high-quality default when free mode is off.

Follows the current Anthropic SDK shape (messages.create; adaptive thinking and
prompt caching get layered in at the call sites that need them, P5+). Default
model here is Sonnet for general text; role-specific models are chosen by the
services that call this (opus for reasoning, haiku for classification).
"""
from __future__ import annotations

from typing import Any

import anthropic

from .base import LLMError
from .util import parse_json_lenient

DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider:
    name = "claude"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = anthropic.Anthropic(api_key=api_key, max_retries=0, timeout=30.0)
        self._model = model
        self.last_usage: dict | None = None

    @staticmethod
    def _system_param(system: str) -> list[dict]:
        """System prompt as a cacheable prefix.

        The caller passes the project's stable global memory here, so the same
        prefix is re-sent every episode and served from cache. Volatile
        per-episode text must go in the user message, never in here.
        """
        return [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            }
        ]

    def _record_usage(self, msg: object) -> None:
        u = getattr(msg, "usage", None)
        self.last_usage = {
            "input": getattr(u, "input_tokens", 0) or 0,
            "output": getattr(u, "output_tokens", 0) or 0,
            "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
            "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0,
        }

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
            kwargs["system"] = self._system_param(system)
        try:
            msg = self._client.messages.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            raise LLMError("Claude 호출 실패") from e
        self._record_usage(msg)
        return "".join(b.text for b in msg.content if b.type == "text")

    def generate_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        schema: dict | None = None,
        max_tokens: int = 4096,
    ) -> Any:
        kwargs: dict = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = self._system_param(system)
        if schema is not None:
            kwargs["output_config"] = {"format": {"type": "json_schema", "schema": schema}}
        try:
            msg = self._client.messages.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            raise LLMError("Claude 호출 실패") from e
        self._record_usage(msg)
        text = "".join(b.text for b in msg.content if b.type == "text")
        try:
            return parse_json_lenient(text)
        except Exception as e:  # noqa: BLE001
            raise LLMError("Claude가 올바른 JSON을 반환하지 않았습니다") from e
