"""Provider selection based on the free_mode toggle + stored keys.

free_mode on  -> Gemini (needs the Gemini key)
free_mode off -> Claude  (needs the Anthropic key)
"""
from __future__ import annotations

from ..storage import config, keys
from .base import LLMError, LLMProvider


def active_provider_name() -> str:
    return "gemini" if config.is_free_mode() else "claude"


def get_provider() -> LLMProvider:
    if config.is_free_mode():
        key = keys.get_key(keys.GEMINI)
        if not key:
            raise LLMError("무료 모드가 켜져 있지만 Gemini 키가 없습니다. 설정에서 키를 입력하세요.")
        from .gemini import GeminiProvider

        return GeminiProvider(key)

    key = keys.get_key(keys.ANTHROPIC)
    if not key:
        raise LLMError("Claude 모드지만 Anthropic 키가 없습니다. 설정에서 키를 입력하거나 무료 모드를 켜세요.")
    from .anthropic_provider import AnthropicProvider

    return AnthropicProvider(key)
