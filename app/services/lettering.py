"""Dialogue lettering: composite speech bubbles onto a panel's cut image.

Bubbles are placed on the *flattest* regions of the image (low edge density) so
they avoid faces/figures, which are detail-rich. This keeps text off characters'
faces instead of always stacking at the top-left.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

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


def _busyness(edges: Image.Image, x: int, y: int, w: int, h: int) -> float:
    """Mean edge intensity under a box — high means detail (face/figure)."""
    box = (max(0, x), max(0, y), min(edges.width, x + w), min(edges.height, y + h))
    if box[2] <= box[0] or box[3] <= box[1]:
        return 1e9
    return ImageStat.Stat(edges.crop(box)).mean[0]


def _overlaps(x: int, y: int, w: int, h: int, rects: list[tuple], gap: int) -> bool:
    for rx0, ry0, rx1, ry1 in rects:
        if x < rx1 + gap and x + w > rx0 - gap and y < ry1 + gap and y + h > ry0 - gap:
            return True
    return False


def _place(edges, bw, bh, W, H, margin, occupied) -> tuple[int, int]:
    """Pick the flattest non-overlapping spot; fall back to stacking."""
    bw = min(bw, W - 2 * margin)
    xs = [margin, (W - bw) // 2, max(margin, W - margin - bw)]
    y_max = max(margin, H - bh - margin)
    step = max(24, (y_max - margin) // 9) if y_max > margin else 1
    ys = list(range(margin, y_max + 1, step))
    gap = int(margin * 0.5)

    best: tuple[int, int] | None = None
    best_score = 1e18
    for y in ys:
        for x in xs:
            if _overlaps(x, y, bw, bh, occupied, gap):
                continue
            score = _busyness(edges, x, y, bw, bh)
            if score < best_score:
                best_score = score
                best = (x, y)
    if best is not None:
        return best
    # everything overlaps: stack below the lowest occupied box
    y = (max((r[3] for r in occupied), default=margin)) + gap
    return margin, min(y, max(margin, H - bh - margin))


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
    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)

    body = _load_font(_REGULAR, max(16, W // 34))
    name = _load_font(_BOLD, max(13, W // 46))
    margin = int(W * 0.03)
    max_bubble_w = W * 0.6

    # complexity above this at the best spot => no clear empty space => use a band
    FLAT_THRESHOLD = 6.0
    gap = int(margin * 0.5)

    occupied: list[tuple] = []
    inplace: list[tuple] = []  # (x, y, dtype, m)
    band: list[tuple] = []  # (dtype, m)
    count = 0
    for d in panel.dialogue or []:
        text = str(d.get("text", "")).strip()
        if not text:
            continue
        count += 1
        dtype = str(d.get("type", "speech")).strip().lower()
        speaker = str(d.get("speaker", "")).strip()
        m = _measure(draw, dtype, speaker, text, body, name, max_bubble_w)
        x, y = _place(edges, m["bw"], m["bh"], W, H, margin, occupied)
        score = _busyness(edges, x, y, m["bw"], m["bh"])
        fits = score <= FLAT_THRESHOLD and not _overlaps(x, y, m["bw"], m["bh"], occupied, gap)
        if fits:
            inplace.append((x, y, dtype, m))
            occupied.append((x, y, x + m["bw"], y + m["bh"]))
        else:
            band.append((dtype, m))  # goes into a white band below the image

    for x, y, dtype, m in inplace:
        _draw(draw, x, y, dtype, m, body, name)

    out = img
    if band:
        band_pad = margin
        band_h = band_pad * 2 + sum(m["bh"] for _, m in band) + gap * (len(band) - 1)
        canvas = Image.new("RGB", (W, H + band_h), (255, 255, 255))
        canvas.paste(img, (0, 0))
        bd = ImageDraw.Draw(canvas)
        yy = H + band_pad
        for dtype, m in band:
            _draw(bd, margin, yy, dtype, m, body, name)
            yy += m["bh"] + gap
        out = canvas

    buf = BytesIO()
    out.save(buf, format="JPEG", quality=90)
    rel = files.save_bytes(_project_id(panel), "panels", f"{panel_id}_lettered.jpg", buf.getvalue())
    repo.update_panel(panel_id, lettered_path=rel)
    return {"lettered_path": rel, "bubbles": count}


def _project_id(panel) -> str:
    ep = repo.get_episode(panel.episode_id)
    return ep.project_id if ep else "unknown"
