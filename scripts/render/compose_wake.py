"""Stack the rotor-only and four-wing renders and add the LaTeX overlay.

Usage: python compose_wake.py <rotor-only png> <four-wing png> <output stem>
"""
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overlay import compose  # noqa: E402

DEFICIT_MAX = 0.62      # same as render_wake.py

top, bottom, stem = (Path(a) for a in sys.argv[1:4])
a, b = Image.open(top), Image.open(bottom)
stack = Image.new("RGB", (a.width, a.height + b.height))
stack.paste(a, (0, 0))
stack.paste(b, (0, a.height))
raw = Path(tempfile.mkdtemp()) / "stack.png"
stack.save(raw)
compose(raw, stem,
        bar=dict(name="thesis_blue", vmin=0, vmax=DEFICIT_MAX, fade=0.35, x=69, y=30, height=18,
                 title=r"$1-u_x/U_\infty$", ticks=[(0.0, "0"), (1.0, f"{DEFICIT_MAX:.1f}")]),
        labels=[(4, 53, "Rotor only", "north west"), (4, 25.5, "Four wings", "north west")])
