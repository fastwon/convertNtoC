"""Generate the image for one panel: assemble the prompt, call the image
generator, save the file, and record it on the panel.
"""
from __future__ import annotations

import secrets

from ..image import factory
from ..image.base import ImageError
from ..storage import files
from ..storage import repository as repo
from .prompt_engine import build_panel_prompt


def generate_panel_image(panel_id: str) -> dict:
    panel = repo.get_panel(panel_id)
    if panel is None:
        raise ImageError("컷을 찾을 수 없습니다")
    episode = repo.get_episode(panel.episode_id)
    if episode is None:
        raise ImageError("회차를 찾을 수 없습니다")
    project = repo.get_project(episode.project_id)
    if project is None:
        raise ImageError("프로젝트를 찾을 수 없습니다")

    prompt = build_panel_prompt(project, panel)
    generator = factory.get_generator()
    # fresh seed each call → distinct composition per cut, and re-generate varies
    seed = secrets.randbelow(2_000_000_000)
    data = generator.generate(prompt, width=1024, height=1024, seed=seed)

    rel = files.save_bytes(project.id, "panels", f"{panel_id}.jpg", data)
    repo.update_panel(panel_id, prompt=prompt, image_path=rel)
    return {"generator": generator.name, "prompt": prompt, "image_path": rel}
