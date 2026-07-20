"""Character face/feature embeddings via sqlite-vec (vec0 virtual table).

The vec0 table is created lazily on first upsert with the incoming vector's
dimension (recorded in vec_meta). Search is always scoped by project_id so a
project never sees another project's characters.
"""
from __future__ import annotations

import sqlite3

from sqlite_vec import serialize_float32

from . import db

VEC_TABLE = "character_vec"


def _dim(conn: sqlite3.Connection) -> int | None:
    row = conn.execute("SELECT dim FROM vec_meta WHERE id = 1").fetchone()
    return row["dim"] if row else None


def _ensure_table(conn: sqlite3.Connection, dim: int) -> None:
    current = _dim(conn)
    if current is None:
        conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS {VEC_TABLE} USING vec0("
            f"character_id TEXT PRIMARY KEY, embedding float[{dim}], project_id TEXT)"
        )
        conn.execute("UPDATE vec_meta SET dim = ? WHERE id = 1", (dim,))
    elif current != dim:
        raise ValueError(f"임베딩 차원 불일치: 저장된 {current}, 입력 {dim}")


def upsert(project_id: str, character_id: str, embedding: list[float]) -> None:
    with db.connect() as conn:
        _ensure_table(conn, len(embedding))
        conn.execute(f"DELETE FROM {VEC_TABLE} WHERE character_id = ?", (character_id,))
        conn.execute(
            f"INSERT INTO {VEC_TABLE}(character_id, embedding, project_id) VALUES (?, ?, ?)",
            (character_id, serialize_float32(embedding), project_id),
        )


def search(project_id: str, embedding: list[float], k: int = 5) -> list[tuple[str, float]]:
    """Return up to k (character_id, distance) nearest within the project."""
    with db.connect() as conn:
        if _dim(conn) is None:
            return []
        rows = conn.execute(
            f"SELECT character_id, distance FROM {VEC_TABLE} "
            f"WHERE embedding MATCH ? AND project_id = ? AND k = {int(k)} ORDER BY distance",
            (serialize_float32(embedding), project_id),
        ).fetchall()
        return [(r["character_id"], r["distance"]) for r in rows]


def delete(character_id: str) -> None:
    with db.connect() as conn:
        if _dim(conn) is None:
            return
        conn.execute(f"DELETE FROM {VEC_TABLE} WHERE character_id = ?", (character_id,))
