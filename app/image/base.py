"""ImageGenerator abstraction. Callers assemble a prompt string and get PNG/JPEG
bytes back; which backend runs (free endpoint / Gemini / external API / local
SD) is chosen by the factory.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


class ImageError(Exception):
    """Image generation failed. Never carries an API key."""


@runtime_checkable
class ImageGenerator(Protocol):
    name: str

    def generate(self, prompt: str, *, width: int = 1024, height: int = 1024) -> bytes:
        """Return image bytes (PNG or JPEG) for the assembled prompt."""
        ...
