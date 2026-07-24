"""LLM provider abstraction. Callers (services) depend only on this interface;
Claude vs Gemini differences (SDK, prompt caching, structured output) live
inside each implementation, never leaked to callers.

P4b defines low-level text generation + key validation. Structured extraction
(generate_json) is added in P4c on top of this same interface.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class LLMError(Exception):
    """Provider unavailable / call failed. Never carries the raw API key."""


@runtime_checkable
class LLMProvider(Protocol):
    name: str
    # Token usage from the most recent call, normalized across providers:
    # {"input", "output", "cache_read", "cache_write"}. None before any call.
    last_usage: dict | None

    def validate(self) -> tuple[bool, str]:
        """One cheap real call to check the key. (ok, human-readable message)."""
        ...

    def generate_text(self, prompt: str, *, system: str | None = None, max_tokens: int = 2048) -> str:
        ...

    def generate_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        schema: dict | None = None,
        max_tokens: int = 4096,
    ) -> Any:
        """Return parsed JSON. `schema` (JSON Schema) is enforced where the
        provider supports it; otherwise the prompt must describe the shape."""
        ...
