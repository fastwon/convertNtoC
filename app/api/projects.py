"""Project CRUD endpoints. The project's style_prompt is the locked default
reused by every episode generation."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.cost import is_priced, token_cost
from ..storage import repository as repo

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    style_prompt: str = ""
    font_settings: dict[str, Any] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    style_prompt: str | None = None
    font_settings: dict[str, Any] | None = None


@router.get("")
def list_projects() -> list[dict]:
    return [asdict(p) for p in repo.list_projects()]


@router.post("")
def create_project(body: ProjectCreate) -> dict:
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="프로젝트 이름을 입력하세요")
    p = repo.create_project(body.name.strip(), body.style_prompt, body.font_settings)
    return asdict(p)


@router.get("/{project_id}")
def get_project(project_id: str) -> dict:
    p = repo.get_project(project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return asdict(p)


@router.patch("/{project_id}")
def update_project(project_id: str, body: ProjectUpdate) -> dict:
    if repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    fields = body.model_dump(exclude_unset=True)
    if "name" in fields and (fields["name"] is None or not str(fields["name"]).strip()):
        raise HTTPException(status_code=400, detail="프로젝트 이름은 비울 수 없습니다")
    p = repo.update_project(project_id, **fields)
    return asdict(p)


@router.delete("/{project_id}")
def delete_project(project_id: str) -> dict:
    if repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    repo.delete_project(project_id)
    return {"ok": True}


_OP_LABELS = {
    "extract": "인물 추출", "summarize": "회차 요약", "storyboard": "콘티 생성",
    "describe": "외형 추출", "image": "이미지 생성",
}


@router.get("/{project_id}/usage")
def project_usage(project_id: str) -> dict:
    """Token usage + rough cost estimate for cost transparency (user pays)."""
    if repo.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    rows = repo.get_usage_rows(project_id)
    tot = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "images": 0}
    est = 0.0
    priced = False  # any priced (paid) model was used
    by_op: dict[str, dict] = {}
    for r in rows:
        for k in tot:
            tot[k] += r[k] or 0
        est += token_cost(r["model"], r["input"], r["output"], r["cache_read"], r["cache_write"])
        priced = priced or is_priced(r["model"])
        op = r["operation"]
        agg = by_op.setdefault(op, {"operation": op, "label": _OP_LABELS.get(op, op),
                                    "calls": 0, "input": 0, "output": 0, "images": 0})
        agg["calls"] += r["calls"] or 0
        agg["input"] += r["input"] or 0
        agg["output"] += r["output"] or 0
        agg["images"] += r["images"] or 0
    return {
        "totals": tot,
        "by_operation": list(by_op.values()),
        "est_cost_usd": round(est, 4),
        "priced": priced,  # false → free provider only, cost ≈ $0
    }
