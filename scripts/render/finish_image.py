"""Composite a transparent ParaView screenshot on white; write the PNG master and a WebP."""
import sys
from pathlib import Path

from PIL import Image

src, stem = Path(sys.argv[1]), Path(sys.argv[2])
rgba = Image.open(src).convert("RGBA")
img = Image.new("RGB", rgba.size, (255, 255, 255))
img.paste(rgba, mask=rgba.getchannel("A"))
img.save(stem.with_suffix(".png"), optimize=True)
img.save(stem.with_suffix(".webp"), quality=85, method=6)
for ext in (".png", ".webp"):
    print(stem.with_suffix(ext), f"{stem.with_suffix(ext).stat().st_size / 1e3:.0f} kB")
