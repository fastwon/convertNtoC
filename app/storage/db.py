"""SQLite connection + schema. Loads the sqlite-vec extension on every connection.

The relational tables are created up front; the vec0 virtual table is created
lazily on first embedding insert (see vectors.py) because the embedding
dimension isn't known until an embedding model is chosen (P4).
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import sqlite_vec

from ..paths import app_data_dir

DB_FILENAME = "convertN2C.sqlite3"


def db_path() -> Path:
    return app_data_dir() / DB_FILENAME


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open a connection with FK enforcement + sqlite-vec loaded.

    Commits on success, rolls back on exception, always closes. One connection
    per operation keeps things thread-safe under uvicorn's sync threadpool.
    """
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
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
  id              TEXT PRIMARY KEY,
  name            TEXT NOT NULL,
  style_prompt    TEXT NOT NULL DEFAULT '',
  image_model_ref TEXT,
  font_settings   TEXT,                 -- JSON
  created_at      TEXT NOT NULL
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
  prompt     TEXT NOT NULL DEFAULT '',
  image_path TEXT,                      -- relative to app_data_dir
  dialogue   TEXT,                      -- JSON
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_panel_episode ON panel(episode_id);

CREATE TABLE IF NOT EXISTS global_memory (
  project_id  TEXT PRIMARY KEY REFERENCES project(id) ON DELETE CASCADE,
  world_bible TEXT NOT NULL DEFAULT '',
  updated_at  TEXT NOT NULL
);

-- single-row table remembering the embedding dimension the vec0 table was built with
CREATE TABLE IF NOT EXISTS vec_meta (
  id  INTEGER PRIMARY KEY CHECK (id = 1),
  dim INTEGER
);
INSERT OR IGNORE INTO vec_meta(id, dim) VALUES (1, NULL);
"""


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
