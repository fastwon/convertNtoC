"""Plain dataclasses mirroring the DB rows. JSON columns are parsed to dict/list."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Project:
    id: str
    name: str
    style_prompt: str
    image_model_ref: str | None
    font_settings: dict[str, Any] | None
    created_at: str


@dataclass
class Character:
    id: str
    project_id: str
    name: str
    traits: dict[str, Any] | None
    ref_image_path: str | None
    created_at: str


@dataclass
class Episode:
    id: str
    project_id: str
    number: int
    raw_text: str
    summary: str | None
    status: str
    created_at: str


@dataclass
class Panel:
    id: str
    episode_id: str
    order: int
    prompt: str
    image_path: str | None
    dialogue: Any | None
    created_at: str


@dataclass
class GlobalMemory:
    project_id: str
    world_bible: str
    updated_at: str
