"""Generate the image for one panel: assemble the prompt, call the image
generator, save the file, and record it on the panel.
"""
from __future__ import annotations

import secrets

from ..image import factory
from ..image.base import ImageError
from ..llm import factory as llm_factory
from ..llm.base import LLMError
from ..storage import files
from ..storage import repository as repo
from .prompt_engine import build_panel_prompt

_TRANSLATE_SYSTEM = (
    "너는 이미지 생성 AI(Flux/Stable Diffusion)용 프롬프트 번역기다. "
    "한국어 만화 컷 묘사를 영어 이미지 프롬프트로 바꾼다. "
    "각 등장인물의 외형 묘사(머리색·헤어스타일·눈·나이·복장)는 반드시 그대로 살려서, "
    "같은 인물이 컷마다 일관된 모습으로 보이도록 그 특징을 강조한다. "
    "쉼표로 구분된 간결한 영어 구절들로만, 설명·따옴표 없이 프롬프트만 출력한다."
)


def _to_image_prompt(korean_prompt: str) -> str:
    """Translate the assembled Korean prompt to English (Flux understands English
    far better). Falls back to the Korean prompt if the LLM is unavailable."""
    try:
        provider = llm_factory.get_provider()
        out = provider.generate_text(korean_prompt, system=_TRANSLATE_SYSTEM, max_tokens=400)
    except LLMError:
        return korean_prompt
    out = out.strip()
    return out or korean_prompt


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

    prompt_ko = build_panel_prompt(project, panel)
    prompt = _to_image_prompt(prompt_ko)  # English → Flux understands the scene
    generator = factory.get_generator()
    # fresh seed each call → distinct composition per cut, and re-generate varies
    seed = secrets.randbelow(2_000_000_000)
    data = generator.generate(prompt, width=1024, height=1024, seed=seed)

    rel = files.save_bytes(project.id, "panels", f"{panel_id}.jpg", data)
    repo.update_panel(panel_id, prompt=prompt, image_path=rel)
    repo.add_usage(project.id, "image", generator.name, None, None, images=1)
    return {"generator": generator.name, "prompt": prompt, "image_path": rel}
