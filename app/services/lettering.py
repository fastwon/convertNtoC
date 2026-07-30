"""Dialogue lettering: composite speech bubbles onto a panel's cut image.

Bubbles are drawn at the positions the user placed them (each dialogue item
carries normalized x,y in 0..1). No automatic placement — the user is in control.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..storage import files
from ..storage import repository as repo


class LetteringError(Exception):
    pass


_REGULAR = ["C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/gulim.ttc", "C:/Windows/Fonts/batang.ttc"]
_BOLD = ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf"]


def _load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: float) -> list[str]:
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


def _measure(draw, dtype, speaker, text, body_font, name_font, max_w):
    is_narration = dtype == "narration"
    is_thought = dtype == "thought"
    pad = max(8, int(body_font.size * 0.5))
    line_h = int(body_font.size * 1.32)
    lines = _wrap(draw, text, body_font, max_w)
    text_w = max((draw.textlength(ln, font=body_font) for ln in lines), default=0)
    label = ""
    if not is_narration and speaker:
        label = f"{speaker} (생각)" if is_thought else speaker
    name_h = 0
    if label:
        name_h = int(name_font.size * 1.3)
        text_w = max(text_w, draw.textlength(label, font=name_font))
    bw = int(text_w + pad * 2)
    bh = int(name_h + len(lines) * line_h + pad * 2)
    return {"bw": bw, "bh": bh, "lines": lines, "label": label, "name_h": name_h,
            "pad": pad, "line_h": line_h}


def _draw(draw, x, y, dtype, m, body_font, name_font):
    is_narration = dtype == "narration"
    is_thought = dtype == "thought"
    if is_narration:
        fill, outline, radius, ow = (255, 248, 225), (60, 60, 60), 6, 2
    elif is_thought:
        fill, outline, radius, ow = (255, 255, 255), (120, 120, 120), int(m["bh"] * 0.5), 2
    else:
        fill, outline, radius, ow = (255, 255, 255), (20, 20, 20), max(10, int(body_font.size * 0.7)), max(2, int(body_font.size * 0.09))
    draw.rounded_rectangle([x, y, x + m["bw"], y + m["bh"]], radius=radius, fill=fill, outline=outline, width=ow)
    ty = y + m["pad"]
    if m["label"]:
        draw.text((x + m["pad"], ty), m["label"], font=name_font, fill=(90, 90, 90))
        ty += m["name_h"]
    color = (70, 60, 40) if is_narration else (15, 15, 15)
    for ln in m["lines"]:
        draw.text((x + m["pad"], ty), ln, font=body_font, fill=color)
        ty += m["line_h"]


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
    max_bubble_w = W * 0.55

    count = 0
    for i, d in enumerate(panel.dialogue or []):
        text = str(d.get("text", "")).strip()
        if not text:
            continue
        count += 1
        dtype = str(d.get("type", "speech")).strip().lower()
        speaker = str(d.get("speaker", "")).strip()
        m = _measure(draw, dtype, speaker, text, body, name, max_bubble_w)

        xr, yr = d.get("x"), d.get("y")
        if isinstance(xr, (int, float)) and isinstance(yr, (int, float)):
            x, y = int(xr * W), int(yr * H)
        else:  # no saved position → simple stagger as a starting point
            x = margin
            y = margin + (i % 6) * (m["bh"] + int(margin * 0.6))
        x = max(0, min(x, W - m["bw"]))
        y = max(0, min(y, H - m["bh"]))
        _draw(draw, x, y, dtype, m, body, name)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    rel = files.save_bytes(_project_id(panel), "panels", f"{panel_id}_lettered.jpg", buf.getvalue())
    repo.update_panel(panel_id, lettered_path=rel)
    return {"lettered_path": rel, "bubbles": count}


def _project_id(panel) -> str:
    ep = repo.get_episode(panel.episode_id)
    return ep.project_id if ep else "unknown"
