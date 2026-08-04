"""SQLite connection + schema.

Character consistency is driven by text (LLM name matching + vision-anchored
appearance descriptions), not vector search, so there is no embedding store.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ..paths import app_data_dir

DB_FILENAME = "convertN2C.sqlite3"


def db_path() -> Path:
    return app_data_dir() / DB_FILENAME


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open a connection with FK enforcement.

    Commits on success, rolls back on exception, always closes. One connection
    per operation keeps things thread-safe under uvicorn's sync threadpool.
    """
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS project (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  style_prompt  TEXT NOT NULL DEFAULT '',
  font_settings TEXT,                 -- JSON
  created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS character (
  id             TEXT PRIMARY KEY,
  project_id     TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  traits         TEXT,                  -- JSON
  ref_image_path TEXT,                  -- relative to app_data_dir
  created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_character_project ON character(project_id);

-- A character can look different at different points in the story (present day,
-- a flashback to their school years, after an injury, aged up). Each row is one
-- such look, with its own description and reference image, so panel generation
-- can pick the right one per cut.
CREATE TABLE IF NOT EXISTS character_appearance (
  id                    TEXT PRIMARY KEY,
  character_id          TEXT NOT NULL REFERENCES character(id) ON DELETE CASCADE,
  label                 TEXT NOT NULL,              -- "기본", "10년 전", "부상 후"
  description           TEXT NOT NULL DEFAULT '',
  ref_image_path        TEXT,                       -- relative to app_data_dir
  source_episode_number INTEGER,                    -- where this look shows up
  is_default            INTEGER NOT NULL DEFAULT 0,
  created_at            TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_appearance_character ON character_appearance(character_id);

CREATE TABLE IF NOT EXISTS episode (
  id         TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
  number     INTEGER NOT NULL,
  raw_text   TEXT NOT NULL DEFAULT '',
  summary    TEXT,
  status     TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL,
  UNIQUE(project_id, number)
);
CREATE INDEX IF NOT EXISTS idx_episode_project ON episode(project_id);

CREATE TABLE IF NOT EXISTS panel (
  id         TEXT PRIMARY KEY,
  episode_id TEXT NOT NULL REFERENCES episode(id) ON DELETE CASCADE,
  ord        INTEGER NOT NULL,
  scene      TEXT NOT NULL DEFAULT '',  -- LLM visual description of the cut
  characters TEXT,                      -- JSON: [{"name","appearance_label"}]
  prompt     TEXT NOT NULL DEFAULT '',  -- assembled image prompt (P6b)
  image_path TEXT,                      -- generated image, relative to app_data_dir (P6b)
  lettered_path TEXT,                   -- image with dialogue bubbles composited (P7)
  dialogue   TEXT,                      -- JSON: [{"speaker","text"}]
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_panel_episode ON panel(episode_id);

CREATE TABLE IF NOT EXISTS global_memory (
  project_id  TEXT PRIMARY KEY REFERENCES project(id) ON DELETE CASCADE,
  world_bible TEXT NOT NULL DEFAULT '',
  updated_at  TEXT NOT NULL
);

-- app-wide non-secret settings (e.g. free_mode toggle). Secrets live in keyring.
CREATE TABLE IF NOT EXISTS app_config (
  key   TEXT PRIMARY KEY,
  value TEXT
);
"""


def _backfill_default_appearances() -> None:
    """Give pre-existing characters a '기본' appearance from their old fields.

    Characters created before appearances existed stored one description +
    reference image directly on the row; migrate those into the new table so
    every character has at least one look.
    """
    import json
    import uuid
    from datetime import datetime, timezone

    with connect() as conn:
        rows = conn.execute(
            "SELECT c.id, c.traits, c.ref_image_path FROM character c "
            "LEFT JOIN character_appearance a ON a.character_id = c.id "
            "WHERE a.id IS NULL"
        ).fetchall()
        for r in rows:
            desc = ""
            if r["traits"]:
                try:
                    parsed = json.loads(r["traits"])
                    if isinstance(parsed, dict):
                        desc = str(parsed.get("description", ""))
                except json.JSONDecodeError:
                    pass
            conn.execute(
                "INSERT INTO character_appearance"
                "(id, character_id, label, description, ref_image_path,"
                " source_episode_number, is_default, created_at)"
                " VALUES (?, ?, '기본', ?, ?, NULL, 1, ?)",
                (
                    uuid.uuid4().hex,
                    r["id"],
                    desc,
                    r["ref_image_path"],
                    datetime.now(timezone.utc).isoformat(),
                ),
            )


def _migrate_panel_columns() -> None:
    """Add columns to a panel table created before P6/P7."""
    with connect() as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(panel)")}
        if "scene" not in cols:
            conn.execute("ALTER TABLE panel ADD COLUMN scene TEXT NOT NULL DEFAULT ''")
        if "characters" not in cols:
            conn.execute("ALTER TABLE panel ADD COLUMN characters TEXT")
        if "lettered_path" not in cols:
            conn.execute("ALTER TABLE panel ADD COLUMN lettered_path TEXT")


def _drop_legacy_columns() -> None:
    """Remove columns from earlier phases that are no longer used."""
    with connect() as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(project)")}
        if "image_model_ref" in cols:
            conn.execute("ALTER TABLE project DROP COLUMN image_model_ref")


def _drop_legacy_vector_store() -> None:
    """Remove the unused sqlite-vec tables from DBs created before it was cut.

    Embeddings were never populated (consistency is text-driven), so these are
    always empty. character_vec was a vec0 virtual table needing the extension;
    it was never created in practice, but drop it guardedly just in case.
    """
    with connect() as conn:
        conn.execute("DROP TABLE IF EXISTS vec_meta")
        try:
            conn.execute("DROP TABLE IF EXISTS character_vec")
        except sqlite3.OperationalError:
            pass  # vec0 table present but extension unavailable — leave it


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
    _migrate_panel_columns()
    _drop_legacy_columns()
    _drop_legacy_vector_store()
    _backfill_default_appearances()
