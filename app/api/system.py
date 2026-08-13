"""System / storage info + maintenance. Exposes where local data lives (no
secrets), how much space it uses, and lets the user open the folder or reclaim
space from re-upload backups (panels/old)."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..paths import app_data_dir
from ..storage import db

router = APIRouter(prefix="/api/system", tags=["system"])


def _dir_size(p: Path) -> int:
    if not p.exists():
        return 0
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def _old_backup_dirs() -> list[Path]:
    """Every panels/old backup folder across all projects (re-upload leftovers)."""
    projects = app_data_dir() / "projects"
    if not projects.exists():
        return []
    return [d for d in projects.glob("*/panels/old") if d.is_dir()]


def _counts() -> dict:
    with db.connect() as conn:
        def n(sql: str) -> int:
            return int(conn.execute(sql).fetchone()[0])
        return {
            "projects": n("SELECT COUNT(*) FROM project"),
            "episodes": n("SELECT COUNT(*) FROM episode"),
            "characters": n("SELECT COUNT(*) FROM character"),
            "panels": n("SELECT COUNT(*) FROM panel"),
        }


@router.get("/info")
def info() -> dict:
    data_dir = app_data_dir()
    dbf = db.db_path()
    projects_dir = data_dir / "projects"
    backup_size = sum(_dir_size(d) for d in _old_backup_dirs())
    db_size = dbf.stat().st_size if dbf.exists() else 0
    images_size = _dir_size(projects_dir)
    return {
        "data_dir": str(data_dir),
        "db_path": str(dbf),
        "db_exists": dbf.exists(),
        "db_size": db_size,
        "images_size": images_size,
        "backup_size": backup_size,
        "total_size": db_size + images_size,
        "counts": _counts(),
    }


@router.post("/open-data-folder")
def open_data_folder() -> dict:
    folder = app_data_dir()
    try:
        os.startfile(folder)  # type: ignore[attr-defined]  # Windows-only
    except OSError as err:
        raise HTTPException(status_code=500, detail=f"폴더를 열 수 없습니다: {err}") from err
    return {"folder": str(folder)}


@router.post("/purge-backups")
def purge_backups() -> dict:
    """Delete every panels/old backup folder to reclaim space. Current images
    are untouched — only the pre-re-upload copies are removed."""
    freed = 0
    for d in _old_backup_dirs():
        freed += _dir_size(d)
        shutil.rmtree(d, ignore_errors=True)
    return {"freed": freed}
