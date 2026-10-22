"""Animation for the README: the wake of the four-wing rotor drawn out downstream.

Needs a run and reconstructed four-wing case (see the README; examples/quick_start.py prepares
one). Renders the frames with ParaView (render_animation.py) and writes
docs/assets/animation.webp.
Run:  python scripts/render/make_animation.py <four-wing case>   (set PVPYTHON if ParaView is not found)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from gif import crop_union, pvpython, save_gif  # noqa: E402

FRAMES = 120

if len(sys.argv) != 2:
    sys.exit(__doc__)
case = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([pvpython(), str(HERE / "render_animation.py"), str(case), tmp, str(FRAMES)], check=True)
    frames = crop_union([Image.open(p) for p in sorted(Path(tmp).glob("frame_*.png"))])
save_gif(frames, ROOT / "docs" / "assets" / "animation.webp", fps=20, width=840, hold=2.0)
