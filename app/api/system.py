"""System / storage info. Exposes where local data lives (no secrets)."""
from __future__ import annotations

from fastapi import APIRouter

from ..paths import app_data_dir
from ..storage import db, repository

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/info")
def info() -> dict:
    dbf = db.db_path()
    return {
        "data_dir": str(app_data_dir()),
        "db_path": str(dbf),
        "db_exists": dbf.exists(),
        "project_count": len(repository.list_projects()),
    }
