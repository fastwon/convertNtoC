"""Shared LLM helpers."""
from __future__ import annotations

import json
from typing import Any


def parse_json_lenient(text: str) -> Any:
    """Parse model JSON output, tolerating ```json code fences."""
    t = text.strip()
    if t.startswith("```"):
        # strip the opening fence (``` or ```json) and the closing fence
        inner = t[3:]
        if inner[:4].lower() == "json":
            inner = inner[4:]
        if "```" in inner:
            inner = inner[: inner.rfind("```")]
        t = inner.strip()
    return json.loads(t)
