"""Global memory: the project's persistent context re-injected every episode.

This is what makes episode 5 consistent with episode 1. It is assembled from
data we own (style + character bank + world bible + rolling episode summaries),
NOT from model memory — so switching providers degrades text quality, never the
consistency mechanism.

CACHING CONTRACT: the returned string is sent as the LLM `system` prefix and is
cached by the provider. It must be byte-stable across calls for the same project
state — never interpolate timestamps, UUIDs, or randomly-ordered collections.
Volatile per-episode text belongs in the user message, not here.
"""
from __future__ import annotations

from ..storage import repository as repo

MEMORY_HEADER = (
    "너는 소설을 웹툰으로 각색하는 작업을 돕는다. "
    "아래는 이 프로젝트의 고정 설정(화풍·세계관·캐릭터·지난 줄거리)이다. "
    "모든 작업에서 이 설정을 일관되게 유지하라.\n"
)


def build_global_memory(project_id: str, before_episode_number: int | None = None) -> str:
    """Assemble the project's stable context.

    `before_episode_number`: include only summaries of episodes BEFORE this one
    (so episode 2 sees episode 1's summary, not its own).
    """
    project = repo.get_project(project_id)
    if project is None:
        raise ValueError("프로젝트를 찾을 수 없습니다")

    parts: list[str] = [MEMORY_HEADER]

    # 1) locked art style
    parts.append("\n## 화풍 (프로젝트 고정)")
    parts.append(project.style_prompt.strip() or "(미지정)")

    # 2) world bible
    gm = repo.get_global_memory(project_id)
    world = (gm.world_bible if gm else "").strip()
    parts.append("\n## 세계관")
    parts.append(world or "(미지정)")

    # 3) character bank — stable order (repository sorts by created_at).
    # Each character can have several looks (present / flashback / after injury);
    # list them all so the model knows which look a given scene calls for.
    parts.append("\n## 캐릭터 뱅크")
    chars = repo.list_characters(project_id)
    if chars:
        for c in chars:
            parts.append(f"- {c.name}")
            looks = repo.list_appearances(c.id)
            if not looks:
                parts.append("  - (등록된 모습 없음)")
                continue
            for a in looks:
                tags = []
                if a.is_default:
                    tags.append("기본")
                if a.source_episode_number is not None:
                    tags.append(f"{a.source_episode_number}화")
                tags.append("참조이미지 있음" if a.ref_image_path else "참조이미지 없음")
                parts.append(
                    f"  - [{a.label}] {a.description or '(특징 미기재)'} ({', '.join(tags)})"
                )
    else:
        parts.append("(아직 등록된 캐릭터 없음)")

    # 4) rolling summaries of prior episodes (summaries, not raw text)
    parts.append("\n## 지난 회차 줄거리 요약")
    episodes = repo.list_episodes(project_id)
    prior = [
        e
        for e in episodes
        if e.summary and (before_episode_number is None or e.number < before_episode_number)
    ]
    if prior:
        for e in prior:
            parts.append(f"- {e.number}화: {e.summary.strip()}")
    else:
        parts.append("(아직 요약된 이전 회차 없음)")

    return "\n".join(parts)


def _summary_instruction(text_len: int) -> str:
    """Scale the target length to the source. A fixed '4~6 sentences' makes the
    model pad out short chapters with invented plot — and because summaries
    accumulate into global memory, that fabrication would harden into 'fact'
    for every later episode.
    """
    if text_len < 300:
        target = "1~2문장"
    elif text_len < 1500:
        target = "2~4문장"
    else:
        target = "4~6문장"
    return (
        f"위 회차 본문을 {target}으로 요약하라.\n"
        "규칙:\n"
        "- 본문에 실제로 서술된 사실만 쓴다. 추측, 전개 예상, 각색, 분위기 과장을 더하지 마라.\n"
        "- 본문에 없는 사건·감정·관계를 지어내지 마라.\n"
        "- 요약은 반드시 원문보다 짧아야 한다.\n"
        "- 핵심 사건과 인물의 행동·관계 변화 위주로, 줄거리 흐름으로 쓴다.\n"
        "- 요약문만 출력한다."
    )

MAX_TEXT_CHARS = 20000


def summarize_episode(episode_id: str) -> dict:
    """Generate + persist this episode's summary, with global memory as context."""
    from ..llm import factory  # local import keeps storage layer import-light
    from ..llm.base import LLMError

    episode = repo.get_episode(episode_id)
    if episode is None:
        raise LLMError("회차를 찾을 수 없습니다")
    if not episode.raw_text.strip():
        raise LLMError("회차 본문이 비어 있습니다")

    # stable cached prefix: everything before this episode
    system = build_global_memory(episode.project_id, before_episode_number=episode.number)
    text = episode.raw_text[:MAX_TEXT_CHARS]
    prompt = f"[{episode.number}화 본문]\n{text}\n\n{_summary_instruction(len(text))}"

    provider = factory.get_provider()
    summary = provider.generate_text(prompt, system=system, max_tokens=1024).strip()
    if not summary:
        raise LLMError("요약 생성에 실패했습니다 (빈 응답)")

    repo.set_episode_summary(episode_id, summary)
    repo.set_episode_status(episode_id, "summarized")
    return {
        "summary": summary,
        "provider": provider.name,
        "usage": getattr(provider, "last_usage", None),
    }
