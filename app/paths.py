"""Filesystem path resolution for dev and PyInstaller-frozen runs.

In a PyInstaller one-file build, bundled data is unpacked to ``sys._MEIPASS``;
in dev it lives in the repo tree. All persistent user data goes to the OS
app-data directory (never inside the bundle).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from platformdirs import user_data_dir, user_documents_dir

APP_NAME = "convertN2C"


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _base_dir() -> Path:
    if _is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # repo root (this file is app/paths.py)
    return Path(__file__).resolve().parent.parent


def static_dir() -> Path:
    """Directory holding the built React SPA (index.html + assets)."""
    if _is_frozen():
        return _base_dir() / "frontend_dist"
    return _base_dir() / "frontend" / "dist"


def app_data_dir() -> Path:
    """Per-user writable data root (DB, vector store, images). Created if missing.

    Override with the CONVERTN2C_DATA_DIR env var (portable mode / tests) so the
    real user data is never touched by throwaway runs.
    """
    override = os.environ.get("CONVERTN2C_DATA_DIR")
    d = Path(override) if override else Path(user_data_dir(APP_NAME, appauthor=False))
    d.mkdir(parents=True, exist_ok=True)
    return d


def exports_dir() -> Path:
    """User-facing folder where finished comics are exported. A real folder the
    user can find (Documents\\convertN2C 내보내기), unlike the hidden app-data dir.

    Under CONVERTN2C_DATA_DIR (tests / portable mode) it lives inside that dir so
    throwaway runs never write to the user's Documents.
    """
    override = os.environ.get("CONVERTN2C_DATA_DIR")
    if override:
        d = Path(override) / "exports"
    else:
        d = Path(user_documents_dir()) / f"{APP_NAME} 내보내기"
    d.mkdir(parents=True, exist_ok=True)
    return d
