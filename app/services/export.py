"""Export a finished episode's cuts as a downloadable file.

For each panel (in order) we take the lettered image if present, else the raw
generated/uploaded cut. Three shapes:
  - png : one tall webtoon strip (cuts stacked, normalized to a common width)
  - pdf : one page per cut (comic-book style)
  - zip : the individual cut image files
"""
from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

from ..paths import exports_dir
from ..storage import files
from ..storage import repository as repo


class ExportError(Exception):
    pass


def _panel_files(episode_id: str) -> list[Path]:
    """Resolved image paths for cuts that actually have an image, in order."""
    paths: list[Path] = []
    for p in repo.list_panels(episode_id):
        rel = p.lettered_path or p.image_path
        if not rel:
            continue
        path = files.resolve(rel)
        if path.exists():
            paths.append(path)
    return paths


def _load_rgb(episode_id: str) -> list[Image.Image]:
    paths = _panel_files(episode_id)
    if not paths:
        raise ExportError("내보낼 컷 이미지가 없습니다. 먼저 컷 이미지를 만들어 주세요.")
    return [Image.open(p).convert("RGB") for p in paths]


def export_png(episode_id: str) -> bytes:
    """Stack all cuts vertically into a single webtoon strip."""
    images = _load_rgb(episode_id)
    width = max(im.width for im in images)
    scaled = [
        im if im.width == width else im.resize((width, round(im.height * width / im.width)))
        for im in images
    ]
    total_h = sum(im.height for im in scaled)
    canvas = Image.new("RGB", (width, total_h), (255, 255, 255))
    y = 0
    for im in scaled:
        canvas.paste(im, (0, y))
        y += im.height
    buf = BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


def export_pdf(episode_id: str) -> bytes:
    """One cut per page."""
    images = _load_rgb(episode_id)
    buf = BytesIO()
    images[0].save(buf, format="PDF", save_all=True, append_images=images[1:])
    return buf.getvalue()


def export_zip(episode_id: str) -> bytes:
    """The individual cut image files, numbered in reading order."""
    paths = _panel_files(episode_id)
    if not paths:
        raise ExportError("내보낼 컷 이미지가 없습니다. 먼저 컷 이미지를 만들어 주세요.")
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for i, path in enumerate(paths, 1):
            z.write(path, arcname=f"{i:02d}{path.suffix.lower()}")
    return buf.getvalue()


_FORMATS = {
    "png": (export_png, "image/png", "png"),
    "pdf": (export_pdf, "application/pdf", "pdf"),
    "zip": (export_zip, "application/zip", "zip"),
}


def export_episode(episode_id: str, fmt: str) -> tuple[bytes, str, str]:
    """Return (data, media_type, file_extension) for the requested format."""
    entry = _FORMATS.get(fmt)
    if entry is None:
        raise ExportError(f"지원하지 않는 형식입니다: {fmt}")
    fn, media_type, ext = entry
    return fn(episode_id), media_type, ext


def save_export(episode_id: str, fmt: str, number: int) -> Path:
    """Write the export into the user's exports folder and return its path.

    This is the reliable path inside the PyWebView desktop shell, where browser
    blob downloads are silently dropped. Re-exporting overwrites the same file.
    """
    data, _media, ext = export_episode(episode_id, fmt)
    dest = exports_dir() / f"{number}화.{ext}"
    dest.write_bytes(data)
    return dest
