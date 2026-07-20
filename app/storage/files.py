"""Local image file storage under app_data_dir/projects/<project_id>/.

Paths stored in the DB are RELATIVE to app_data_dir (portable if the data dir
moves). Use resolve() to get an absolute path for reading.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from ..paths import app_data_dir


def _projects_root() -> Path:
    root = app_data_dir() / "projects"
    root.mkdir(parents=True, exist_ok=True)
    return root


def project_dir(project_id: str) -> Path:
    d = _projects_root() / project_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_bytes(project_id: str, subdir: str, filename: str, data: bytes) -> str:
    """Write bytes under projects/<project_id>/<subdir>/<filename>; return the
    app-data-relative path (POSIX separators) to store in the DB."""
    d = project_dir(project_id) / subdir
    d.mkdir(parents=True, exist_ok=True)
    path = d / filename
    path.write_bytes(data)
    return path.relative_to(app_data_dir()).as_posix()


def resolve(rel_path: str) -> Path:
    return app_data_dir() / rel_path


def delete_project_files(project_id: str) -> None:
    d = _projects_root() / project_id
    if d.exists():
        shutil.rmtree(d)
