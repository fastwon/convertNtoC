"""Character extraction endpoint. Returns extracted characters for user
confirmation; persisting into the bank happens in P4d."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..llm.base import LLMError
from ..services import characters as svc

router = APIRouter(tags=["characters"])


@router.post("/api/episodes/{episode_id}/extract-characters")
def extract(episode_id: str) -> dict:
    try:
        return svc.extract_characters(episode_id)
    except LLMError as e:
        # 400: user-actionable (missing key, empty text, bad model output)
        raise HTTPException(status_code=400, detail=str(e)) from e
