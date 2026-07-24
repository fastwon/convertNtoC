"""Data access layer. Every query is scoped by project_id where applicable so
cross-project data never leaks (the core consistency promise).

Deleting a project/character also clears its vectors and image files, since the
vec0 table and the filesystem are outside SQLite's FK cascade.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from . import db, files, vectors
from .models import Appearance, Character, Episode, GlobalMemory, Panel, Project


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


def _dumps(value: Any | None) -> str | None:
    return None if value is None else json.dumps(value, ensure_ascii=False)


def _loads(text: str | None) -> Any | None:
    return None if text is None else json.loads(text)


# --- row -> dataclass -------------------------------------------------------

def _project(r: Any) -> Project:
    return Project(
        id=r["id"], name=r["name"], style_prompt=r["style_prompt"],
        image_model_ref=r["image_model_ref"], font_settings=_loads(r["font_settings"]),
        created_at=r["created_at"],
    )


def _character(r: Any) -> Character:
    return Character(
        id=r["id"], project_id=r["project_id"], name=r["name"],
        traits=_loads(r["traits"]), ref_image_path=r["ref_image_path"],
        created_at=r["created_at"],
    )


def _appearance(r: Any) -> Appearance:
    return Appearance(
        id=r["id"], character_id=r["character_id"], label=r["label"],
        description=r["description"], ref_image_path=r["ref_image_path"],
        source_episode_number=r["source_episode_number"],
        is_default=bool(r["is_default"]), created_at=r["created_at"],
    )


def _episode(r: Any) -> Episode:
    return Episode(
        id=r["id"], project_id=r["project_id"], number=r["number"],
        raw_text=r["raw_text"], summary=r["summary"], status=r["status"],
        created_at=r["created_at"],
    )


def _panel(r: Any) -> Panel:
    return Panel(
        id=r["id"], episode_id=r["episode_id"], order=r["ord"], prompt=r["prompt"],
        image_path=r["image_path"], dialogue=_loads(r["dialogue"]), created_at=r["created_at"],
    )


# --- Project ----------------------------------------------------------------

def create_project(
    name: str,
    style_prompt: str = "",
    image_model_ref: str | None = None,
    font_settings: dict[str, Any] | None = None,
) -> Project:
    pid, now = _new_id(), _now()
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO project(id, name, style_prompt, image_model_ref, font_settings, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (pid, name, style_prompt, image_model_ref, _dumps(font_settings), now),
        )
        conn.execute(
            "INSERT INTO global_memory(project_id, world_bible, updated_at) VALUES (?, '', ?)",
            (pid, now),
        )
    return get_project(pid)  # type: ignore[return-value]


def get_project(project_id: str) -> Project | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM project WHERE id = ?", (project_id,)).fetchone()
    return _project(row) if row else None


def list_projects() -> list[Project]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM project ORDER BY created_at DESC").fetchall()
    return [_project(r) for r in rows]


def update_project(project_id: str, **fields: Any) -> Project | None:
    allowed = {"name", "style_prompt", "image_model_ref", "font_settings"}
    sets, vals = [], []
    for key, val in fields.items():
        if key not in allowed:
            raise ValueError(f"수정 불가 필드: {key}")
        sets.append(f"{key} = ?")
        vals.append(_dumps(val) if key == "font_settings" else val)
    if sets:
        vals.append(project_id)
        with db.connect() as conn:
            conn.execute(f"UPDATE project SET {', '.join(sets)} WHERE id = ?", vals)
    return get_project(project_id)


def delete_project(project_id: str) -> None:
    with db.connect() as conn:
        char_ids = [
            r["id"] for r in conn.execute(
                "SELECT id FROM character WHERE project_id = ?", (project_id,)
            ).fetchall()
        ]
        conn.execute("DELETE FROM project WHERE id = ?", (project_id,))  # cascades rows
    for cid in char_ids:
        vectors.delete(cid)
    files.delete_project_files(project_id)


# --- Character --------------------------------------------------------------

def create_character(
    project_id: str,
    name: str,
    traits: dict[str, Any] | None = None,
    ref_image_path: str | None = None,
) -> Character:
    """Create a character plus its '기본' appearance (every character has ≥1 look)."""
    cid, now = _new_id(), _now()
    description = ""
    if isinstance(traits, dict):
        description = str(traits.get("description", "")).strip()
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO character(id, project_id, name, traits, ref_image_path, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (cid, project_id, name, _dumps(traits), ref_image_path, now),
        )
        conn.execute(
            "INSERT INTO character_appearance"
            "(id, character_id, label, description, ref_image_path,"
            " source_episode_number, is_default, created_at)"
            " VALUES (?, ?, '기본', ?, ?, NULL, 1, ?)",
            (_new_id(), cid, description, ref_image_path, now),
        )
    return get_character(cid)  # type: ignore[return-value]


# --- Appearances (per-character looks over time) ----------------------------

def list_appearances(character_id: str) -> list[Appearance]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM character_appearance WHERE character_id = ?"
            " ORDER BY is_default DESC, created_at",
            (character_id,),
        ).fetchall()
    return [_appearance(r) for r in rows]


def get_appearance(appearance_id: str) -> Appearance | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM character_appearance WHERE id = ?", (appearance_id,)
        ).fetchone()
    return _appearance(row) if row else None


def create_appearance(
    character_id: str,
    label: str,
    description: str = "",
    source_episode_number: int | None = None,
) -> Appearance:
    aid, now = _new_id(), _now()
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO character_appearance"
            "(id, character_id, label, description, ref_image_path,"
            " source_episode_number, is_default, created_at)"
            " VALUES (?, ?, ?, ?, NULL, ?, 0, ?)",
            (aid, character_id, label, description, source_episode_number, now),
        )
    return get_appearance(aid)  # type: ignore[return-value]


def update_appearance(appearance_id: str, **fields: Any) -> Appearance | None:
    allowed = {"label", "description", "ref_image_path", "source_episode_number"}
    sets, vals = [], []
    for key, val in fields.items():
        if key not in allowed:
            raise ValueError(f"수정 불가 필드: {key}")
        sets.append(f"{key} = ?")
        vals.append(val)
    if sets:
        vals.append(appearance_id)
        with db.connect() as conn:
            conn.execute(
                f"UPDATE character_appearance SET {', '.join(sets)} WHERE id = ?", vals
            )
    return get_appearance(appearance_id)


def set_default_appearance(character_id: str, appearance_id: str) -> None:
    with db.connect() as conn:
        conn.execute(
            "UPDATE character_appearance SET is_default = 0 WHERE character_id = ?",
            (character_id,),
        )
        conn.execute(
            "UPDATE character_appearance SET is_default = 1 WHERE id = ? AND character_id = ?",
            (appearance_id, character_id),
        )


def delete_appearance(appearance_id: str) -> None:
    ap = get_appearance(appearance_id)
    if ap is None:
        return
    with db.connect() as conn:
        conn.execute("DELETE FROM character_appearance WHERE id = ?", (appearance_id,))
        # never leave a character without a default look
        if ap.is_default:
            row = conn.execute(
                "SELECT id FROM character_appearance WHERE character_id = ?"
                " ORDER BY created_at LIMIT 1",
                (ap.character_id,),
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE character_appearance SET is_default = 1 WHERE id = ?", (row["id"],)
                )
    if ap.ref_image_path:
        path = files.resolve(ap.ref_image_path)
        if path.exists():
            path.unlink()


def get_character(character_id: str) -> Character | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM character WHERE id = ?", (character_id,)).fetchone()
    return _character(row) if row else None


def list_characters(project_id: str) -> list[Character]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM character WHERE project_id = ? ORDER BY created_at", (project_id,)
        ).fetchall()
    return [_character(r) for r in rows]


def update_character(character_id: str, **fields: Any) -> Character | None:
    allowed = {"name", "traits", "ref_image_path"}
    sets, vals = [], []
    for key, val in fields.items():
        if key not in allowed:
            raise ValueError(f"수정 불가 필드: {key}")
        sets.append(f"{key} = ?")
        vals.append(_dumps(val) if key == "traits" else val)
    if sets:
        vals.append(character_id)
        with db.connect() as conn:
            conn.execute(f"UPDATE character SET {', '.join(sets)} WHERE id = ?", vals)
    return get_character(character_id)


def delete_character(character_id: str) -> None:
    char = get_character(character_id)
    appearances = list_appearances(character_id)
    with db.connect() as conn:
        conn.execute("DELETE FROM character WHERE id = ?", (character_id,))  # cascades appearances
    vectors.delete(character_id)
    # remove image files for every look (FK cascade drops rows, not files)
    paths = [a.ref_image_path for a in appearances]
    if char:
        paths.append(char.ref_image_path)
    for rel in paths:
        if not rel:
            continue
        p = files.resolve(rel)
        if p.exists():
            p.unlink()


# --- Episode ----------------------------------------------------------------

def create_episode(project_id: str, number: int, raw_text: str = "") -> Episode:
    eid, now = _new_id(), _now()
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO episode(id, project_id, number, raw_text, status, created_at)"
            " VALUES (?, ?, ?, ?, 'draft', ?)",
            (eid, project_id, number, raw_text, now),
        )
    return get_episode(eid)  # type: ignore[return-value]


def get_episode(episode_id: str) -> Episode | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM episode WHERE id = ?", (episode_id,)).fetchone()
    return _episode(row) if row else None


def list_episodes(project_id: str) -> list[Episode]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM episode WHERE project_id = ? ORDER BY number", (project_id,)
        ).fetchall()
    return [_episode(r) for r in rows]


def update_episode_text(episode_id: str, raw_text: str) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE episode SET raw_text = ? WHERE id = ?", (raw_text, episode_id))


def delete_episode(episode_id: str) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM episode WHERE id = ?", (episode_id,))  # cascades panels


def set_episode_summary(episode_id: str, summary: str) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE episode SET summary = ? WHERE id = ?", (summary, episode_id))


def set_episode_status(episode_id: str, status: str) -> None:
    with db.connect() as conn:
        conn.execute("UPDATE episode SET status = ? WHERE id = ?", (status, episode_id))


# --- Panel ------------------------------------------------------------------

def create_panel(
    episode_id: str,
    order: int,
    prompt: str = "",
    image_path: str | None = None,
    dialogue: Any | None = None,
) -> Panel:
    pid, now = _new_id(), _now()
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO panel(id, episode_id, ord, prompt, image_path, dialogue, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pid, episode_id, order, prompt, image_path, _dumps(dialogue), now),
        )
        row = conn.execute("SELECT * FROM panel WHERE id = ?", (pid,)).fetchone()
    return _panel(row)


def list_panels(episode_id: str) -> list[Panel]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM panel WHERE episode_id = ? ORDER BY ord", (episode_id,)
        ).fetchall()
    return [_panel(r) for r in rows]


# --- Global memory ----------------------------------------------------------

def get_global_memory(project_id: str) -> GlobalMemory | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM global_memory WHERE project_id = ?", (project_id,)
        ).fetchone()
    return GlobalMemory(row["project_id"], row["world_bible"], row["updated_at"]) if row else None


def set_global_memory(project_id: str, world_bible: str) -> GlobalMemory | None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO global_memory(project_id, world_bible, updated_at) VALUES (?, ?, ?)"
            " ON CONFLICT(project_id) DO UPDATE SET world_bible = excluded.world_bible,"
            " updated_at = excluded.updated_at",
            (project_id, world_bible, _now()),
        )
    return get_global_memory(project_id)
