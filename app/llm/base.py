"""LLM provider abstraction. Callers (services) depend only on this interface;
Claude vs Gemini differences (SDK, prompt caching, structured output) live
inside each implementation, never leaked to callers.

P4b defines low-level text generation + key validation. Structured extraction
(generate_json) is added in P4c on top of this same interface.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


class LLMError(Exception):
    """Provider unavailable / call failed. Never carries the raw API key."""


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def validate(self) -> tuple[bool, str]:
        """One cheap real call to check the key. (ok, human-readable message)."""
        ...

    def generate_text(self, prompt: str, *, system: str | None = None, max_tokens: int = 2048) -> str:
        ...
