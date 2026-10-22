"""Write a list of RGB frames as a looping animation for a README.

The suffix picks the format: .webp (default; full colour, a quarter of the size of a GIF)
or .gif (one shared palette, so small and flicker-free).
"""
from pathlib import Path

import numpy as np
from PIL import Image


def save_gif(frames, path, fps=20, width=840, colours=192, quality=80, hold=0.0):
    """frames: list of HxWx3 uint8 arrays (or PIL images), resized to `width` pixels.

    hold: extra seconds on the last frame before the loop restarts.
    """
    imgs = [f if isinstance(f, Image.Image) else Image.fromarray(np.asarray(f, np.uint8)) for f in frames]
    h = round(imgs[0].height * width / imgs[0].width)
    imgs = [im.convert("RGB").resize((width, h), Image.LANCZOS) for im in imgs]
    path = Path(path)
    duration = [round(1000 / fps)] * len(imgs)
    duration[-1] += round(1000 * hold)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".webp":
        imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=duration, loop=0,
                     quality=quality, method=4)
    else:
        # one palette from a sample of frames, applied to all (avoids palette flicker)
        sample = Image.fromarray(np.concatenate([np.asarray(im) for im in imgs[:: max(1, len(imgs) // 8)]], axis=0))
        palette = sample.quantize(colours, method=Image.Quantize.MEDIANCUT)
        imgs = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in imgs]
        imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=duration, loop=0, optimize=True)
    print(path, f"{path.stat().st_size / 1e6:.1f} MB", f"{len(imgs)} frames", imgs[0].size)


save_animation = save_gif


def crop_union(frames, pad=0.03, threshold=12):
    """Crop every frame to the union of their non-black boxes, plus `pad` of the width."""
    arrs = [np.asarray(f.convert("RGB") if isinstance(f, Image.Image) else f) for f in frames]
    mask = np.zeros(arrs[0].shape[:2], bool)
    for a in arrs:
        mask |= a.max(axis=2) > threshold
    rows, cols = np.flatnonzero(mask.any(1)), np.flatnonzero(mask.any(0))
    p = round(pad * arrs[0].shape[1])
    r0, r1 = max(rows[0] - p, 0), min(rows[-1] + p + 1, mask.shape[0])
    c0, c1 = max(cols[0] - p, 0), min(cols[-1] + p + 1, mask.shape[1])
    return [a[r0:r1, c0:c1] for a in arrs]


def pvpython():
    """ParaView's Python: $PVPYTHON, pvpython on the PATH, or the newest macOS app bundle."""
    import glob
    import os
    import shutil
    found = os.environ.get("PVPYTHON") or shutil.which("pvpython")
    apps = sorted(glob.glob("/Applications/ParaView-*.app/Contents/bin/pvpython"))
    if found or apps:
        return found or apps[-1]
    raise SystemExit("ParaView's pvpython is needed for this animation: set PVPYTHON=/path/to/pvpython")
