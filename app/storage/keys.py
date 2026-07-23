"""Secret storage via the OS credential store (Windows Credential Manager).

Keys are NEVER written to plaintext files or bundled into the exe. All access
goes through this module so the storage backend stays in one place.
"""
from __future__ import annotations

import keyring
from keyring.errors import PasswordDeleteError

SERVICE = "convertN2C"

ANTHROPIC = "anthropic_api_key"
GEMINI = "gemini_api_key"
IMAGE = "image_api_key"
VALID_NAMES = {ANTHROPIC, GEMINI, IMAGE}


def set_key(name: str, value: str) -> None:
    keyring.set_password(SERVICE, name, value)


def get_key(name: str) -> str | None:
    return keyring.get_password(SERVICE, name)


def delete_key(name: str) -> None:
    try:
        keyring.delete_password(SERVICE, name)
    except PasswordDeleteError:
        pass  # already absent — treat delete as idempotent


def has_key(name: str) -> bool:
    return bool(get_key(name))
