"""Image generator selection. Currently the free Pollinations endpoint; a Gemini
(paid) and external-API generator slot in behind the same interface later (P6d).
"""
from __future__ import annotations

from .base import ImageGenerator
from .pollinations import PollinationsGenerator


def active_generator_name() -> str:
    return "pollinations"


def get_generator() -> ImageGenerator:
    return PollinationsGenerator()
