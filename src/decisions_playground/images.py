"""Deterministic rendering; never use generated images or OCR for the evidence."""

from pathlib import Path
from typing import Any

import PIL
from PIL import Image, ImageDraw, ImageFont, features

from .data import ROOT, Dataset, digest, read_json, verify_files, write_json

WIDTH, SIZE, MARGIN, LINE_HEIGHT = 1200, 28, 48, 40


def render(text: str, font_path: Path) -> Image.Image:
    font = ImageFont.truetype(str(font_path), SIZE, layout_engine=ImageFont.Layout.BASIC)
    lines: list[str] = []
    for paragraph in text.splitlines():
        line = ""
        for word in paragraph.split():
            if font.getlength(word) > WIDTH - 2 * MARGIN:
                raise ValueError("A word exceeds image width")
            candidate = f"{line} {word}" if line else word
            if font.getlength(candidate) > WIDTH - 2 * MARGIN:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    if not lines:
        raise ValueError("Empty text")
    image = Image.new("RGB", (WIDTH, 2 * MARGIN + LINE_HEIGHT * len(lines)), "white")
    draw = ImageDraw.Draw(image)
    for n, line in enumerate(lines):
        origin = (MARGIN, MARGIN + LINE_HEIGHT * n)
        bbox = draw.textbbox(origin, line, font=font, anchor="lt")
        if bbox[0] < 0 or bbox[2] > WIDTH - MARGIN or bbox[3] > image.height - MARGIN:
            raise ValueError("Text would be clipped")
        draw.text(origin, line, fill="black", font=font, anchor="lt")
    return image


def prepare(dataset: Dataset, root: Path = ROOT) -> dict[str, Any]:
    font_info = verify_files(root / "assets/fonts")
    output = root / "assets/images"
    output.mkdir(parents=True, exist_ok=True)
    items = {}
    for e in dataset.examples:
        if e.block == "wording":
            continue
        full = render(e.text, root / "assets/fonts/NotoSans-Regular.ttf")
        small = full.resize((full.width // 2, full.height // 2), Image.Resampling.LANCZOS)
        for mode, img in (("openai-png", full), ("openai-png-small", small)):
            path = output / f"{e.id}-{mode}.png"
            img.save(path, format="PNG")
            items[f"{e.id}/{mode}"] = {
                "path": path.relative_to(root).as_posix(),
                "sha256": digest(path.read_bytes()),
                "width": img.width,
                "height": img.height,
            }
    manifest = {
        "dataset_sha256": dataset.fingerprint,
        "font": font_info,
        "pillow": PIL.__version__,
        "freetype": features.version("freetype2"),
        "render": {
            "width": WIDTH,
            "font_size": SIZE,
            "margin": MARGIN,
            "line_height": LINE_HEIGHT,
            "layout": "BASIC",
            "scale": 0.5,
        },
        "images": items,
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def load_images(dataset: Dataset, root: Path = ROOT) -> dict[str, Any]:
    manifest = read_json(root / "assets/images/manifest.json")
    if manifest["dataset_sha256"] != dataset.fingerprint:
        raise ValueError("Images are stale. Run prepare again.")
    for image in manifest["images"].values():
        if digest((root / image["path"]).read_bytes()) != image["sha256"]:
            raise ValueError(f"Image checksum mismatch: {image['path']}")
    return manifest
