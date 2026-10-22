"""Stack the rotor-only and four-wing renders and add the LaTeX overlay.

Usage: python compose_wake.py <rotor-only png> <four-wing png> <output stem>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overlay import compose  # noqa: E402

DEFICIT_MAX = 0.62      # same as render_wake.py
top, bottom, stem = (Path(a) for a in sys.argv[1:4])
compose([(top, "Rotor only"), (bottom, "Four wings")], stem,
        bar=dict(name="thesis_blue", vmin=0, vmax=DEFICIT_MAX, fade=0.35, title=r"$1-u_x/U_\infty$",
                 ticks=[(0.0, "0"), (1.0, f"{DEFICIT_MAX:.1f}")]))
