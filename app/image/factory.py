"""Image generator selection based on the image_provider setting.

pollinations — free, keyless (default)
gemini       — paid (needs Google Cloud billing), reuses the Gemini key
"""
from __future__ import annotations

from ..storage import config, keys
from .base import ImageError, ImageGenerator
from .pollinations import PollinationsGenerator


def active_generator_name() -> str:
    return config.get_image_provider()


def get_generator() -> ImageGenerator:
    provider = config.get_image_provider()
    if provider == "gemini":
        key = keys.get_key(keys.GEMINI)
        if not key:
            raise ImageError("Gemini 이미지: Gemini 키가 필요합니다. 설정에서 입력하세요.")
        from .gemini_image import GeminiImageGenerator

        return GeminiImageGenerator(key)
    return PollinationsGenerator()
