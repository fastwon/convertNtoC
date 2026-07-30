"""Dialogue lettering: composite speech bubbles onto a panel's cut image.

The storyboard already produced each cut's dialogue ([{speaker, text}]); here we
draw those as manga-style speech bubbles over the generated image and save the
result as the panel's "lettered" image (the final comic cut).
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..storage import files
from ..storage import repository as repo


class LetteringError(Exception):
    pass


# Korean-capable fonts, in preference order (Windows). Falls back to PIL default
# (Latin-only) if none are found.
_REGULAR = ["C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/gulim.ttc", "C:/Windows/Fonts/batang.ttc"]
_BOLD = ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf"]


def _load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: float) -> list[str]:
    """Character-based wrap (works for Korean, which lacks reliable word breaks)."""
    lines: list[str] = []
    cur = ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        test = cur + ch
        if draw.textlength(test, font=font) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def _draw_bubble(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    speaker: str,
    text: str,
    body_font: ImageFont.FreeTypeFont,
    name_font: ImageFont.FreeTypeFont,
    max_w: float,
) -> int:
    """Draw one bubble at (x, y). Returns its height."""
    pad = max(8, int(body_font.size * 0.5))
    line_h = int(body_font.size * 1.32)
    lines = _wrap(draw, text, body_font, max_w)
    text_w = max((draw.textlength(ln, font=body_font) for ln in lines), default=0)

    name_h = 0
    if speaker:
        name_h = int(name_font.size * 1.3)
        text_w = max(text_w, draw.textlength(speaker, font=name_font))

    bubble_w = int(text_w + pad * 2)
    bubble_h = int(name_h + len(lines) * line_h + pad * 2)

    draw.rounded_rectangle(
        [x, y, x + bubble_w, y + bubble_h],
        radius=max(10, int(body_font.size * 0.7)),
        fill=(255, 255, 255),
        outline=(20, 20, 20),
        width=max(2, int(body_font.size * 0.09)),
    )
    ty = y + pad
    if speaker:
        draw.text((x + pad, ty), speaker, font=name_font, fill=(90, 90, 90))
        ty += name_h
    for ln in lines:
        draw.text((x + pad, ty), ln, font=body_font, fill=(15, 15, 15))
        ty += line_h
    return bubble_h


def letter_panel(panel_id: str) -> dict:
    panel = repo.get_panel(panel_id)
    if panel is None:
        raise LetteringError("컷을 찾을 수 없습니다")
    if not panel.image_path:
        raise LetteringError("먼저 컷 이미지를 생성하세요")
    src = files.resolve(panel.image_path)
    if not src.exists():
        raise LetteringError("컷 이미지 파일을 찾을 수 없습니다")

    img = Image.open(src).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    body = _load_font(_REGULAR, max(16, W // 34))
    name = _load_font(_BOLD, max(13, W // 46))
    margin = int(W * 0.03)
    max_bubble_w = W * 0.6

    dialogue = panel.dialogue or []
    y = margin
    for i, d in enumerate(dialogue):
        text = str(d.get("text", "")).strip()
        if not text:
            continue
        speaker = str(d.get("speaker", "")).strip()
        # measure to position (left for even, right for odd — a bit of rhythm)
        lines = _wrap(draw, text, body, max_bubble_w)
        tw = max((draw.textlength(ln, font=body) for ln in lines), default=0)
        pad = max(8, int(body.size * 0.5))
        bw = int(min(tw, max_bubble_w) + pad * 2)
        x = margin if i % 2 == 0 else max(margin, W - margin - bw)
        h = _draw_bubble(draw, x, y, speaker, text, body, name, max_bubble_w)
        y += h + int(margin * 0.6)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    rel = files.save_bytes(_project_id(panel), "panels", f"{panel_id}_lettered.jpg", buf.getvalue())
    repo.update_panel(panel_id, lettered_path=rel)
    return {"lettered_path": rel, "bubbles": len([d for d in dialogue if str(d.get("text", "")).strip()])}


def _project_id(panel) -> str:
    ep = repo.get_episode(panel.episode_id)
    return ep.project_id if ep else "unknown"
