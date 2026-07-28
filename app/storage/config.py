"""Non-secret app settings (SQLite kv). Secrets go in keyring, not here.

free_mode: when on (default), the app uses the free Gemini provider; when off,
it uses Claude.
"""
from __future__ import annotations

from . import db

FREE_MODE = "free_mode"
IMAGE_PROVIDER = "image_provider"


def get_config(key: str, default: str | None = None) -> str | None:
    with db.connect() as conn:
        row = conn.execute("SELECT value FROM app_config WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_config(key: str, value: str) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO app_config(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def is_free_mode() -> bool:
    return get_config(FREE_MODE, "1") == "1"  # default ON (free Gemini)


def set_free_mode(on: bool) -> None:
    set_config(FREE_MODE, "1" if on else "0")


VALID_IMAGE_PROVIDERS = {"pollinations", "gemini"}


def get_image_provider() -> str:
    val = get_config(IMAGE_PROVIDER, "pollinations")
    return val if val in VALID_IMAGE_PROVIDERS else "pollinations"


def set_image_provider(provider: str) -> None:
    if provider not in VALID_IMAGE_PROVIDERS:
        raise ValueError(f"지원하지 않는 이미지 공급자: {provider}")
    set_config(IMAGE_PROVIDER, provider)
