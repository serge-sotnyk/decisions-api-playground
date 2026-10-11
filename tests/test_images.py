from PIL import Image, ImageChops

from decisions_playground.data import ROOT, load_dataset
from decisions_playground.images import load_images, render


def test_all_images_are_current_legible_size_and_not_clipped():
    data = load_dataset()
    manifest = load_images(data)
    assert len(manifest["images"]) == 16
    for e in data.examples:
        if e.block == "wording":
            continue
        full = Image.open(ROOT / manifest["images"][f"{e.id}/openai-png"]["path"])
        small = Image.open(ROOT / manifest["images"][f"{e.id}/openai-png-small"]["path"])
        assert full.width == 1200 and small.width == 600
        assert full.height == 2 * small.height
        assert full.info == {}  # No text metadata or answer key inside the PNG.
        diff = ImageChops.difference(full, Image.new("RGB", full.size, "white"))
        bbox = diff.getbbox()
        assert bbox is not None
        assert bbox[0] >= 48 and bbox[2] <= 1152
        assert bbox[1] >= 48 and bbox[3] <= full.height - 48
        expected = render(e.text, ROOT / "assets/fonts/NotoSans-Regular.ttf")
        assert ImageChops.difference(full, expected).getbbox() is None
        resized = full.resize(small.size, Image.Resampling.LANCZOS)
        assert ImageChops.difference(small, resized).getbbox() is None
