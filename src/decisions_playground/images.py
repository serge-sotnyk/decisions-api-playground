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


def prepare_originals(dataset: Dataset, root: Path = ROOT) -> dict[str, Any]:
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


def load_images(dataset: Dataset, root: Path = ROOT, *, original: bool = False) -> dict[str, Any]:
    folder = "images" if original else "images-padded"
    manifest = read_json(root / f"assets/{folder}/manifest.json")
    if manifest["dataset_sha256"] != dataset.fingerprint:
        raise ValueError("Images are stale. Run prepare again.")
    for image in manifest["images"].values():
        if digest((root / image["path"]).read_bytes()) != image["sha256"]:
            raise ValueError(f"Image checksum mismatch: {image['path']}")
    return manifest


def prepare(dataset: Dataset, root: Path = ROOT) -> dict[str, Any]:
    """Pad the frozen original pixels, never redraw or overwrite the October 9 images."""
    original = load_images(dataset, root, original=True)
    output = root / "assets/images-padded"
    output.mkdir(parents=True, exist_ok=True)
    items = {}
    for key, source in original["images"].items():
        example_id, legacy_mode = key.split("/")
        kind = legacy_mode.removeprefix("openai-")
        with Image.open(root / source["path"]) as image:
            image = image.convert("RGB")
            width, height = max(280, image.width), max(280, image.height)
            if max(width, height) > 1568:
                raise ValueError("Image exceeds Jev's maximum dimension")
            left, top = (width - image.width) // 2, (height - image.height) // 2
            padded = Image.new("RGB", (width, height), "white")
            padded.paste(image, (left, top))
            path = output / f"{example_id}-{kind}.png"
            padded.save(path, format="PNG")
        items[f"{example_id}/{kind}"] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": digest(path.read_bytes()),
            "width": width,
            "height": height,
            "source": source,
            "padding": {
                "left": left,
                "top": top,
                "right": width - source["width"] - left,
                "bottom": height - source["height"] - top,
            },
        }
    manifest = {
        "dataset_sha256": dataset.fingerprint,
        "source_manifest_sha256": digest((root / "assets/images/manifest.json").read_bytes()),
        "font": original["font"],
        "pillow": PIL.__version__,
        "render": {
            "source_render": original["render"],
            "minimum_side": 280,
            "padding": "white, centered, applied after original 50% downsampling",
            "resampling": "none; source pixels preserved",
        },
        "images": items,
    }
    write_json(output / "manifest.json", manifest)
    return manifest
