"""ParaView (pvpython) animation frames: the four-wing wake drawn out downstream.

Usage: pvpython render_animation.py <case dir> <frame directory> [frames]
Same scene as the still figure (render_wake.scene). The amber streamlines from the wing tips
grow downstream from the rotor, and each cross-flow plane of the velocity deficit lights up
as the streamlines reach it. The camera is the still figure's.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import onda_style as style  # noqa: E402
from render_wake import CAMERA, scene  # noqa: E402

case, out = Path(sys.argv[1]), Path(sys.argv[2])
frames = int(sys.argv[3]) if len(sys.argv) > 3 else 120
width, height = 1920, 600                    # the still figure's 3.2 : 1 frame
L_MAX = 11.0

view, slices, st = scene(case, width, height)
for key, value in CAMERA.items():
    setattr(view, key, value)
out.mkdir(parents=True, exist_ok=True)
s = np.linspace(0, 1, frames)
for k, f in enumerate(s * s * (3 - 2 * s)):
    length = 0.05 + (L_MAX - 0.05) * f
    st.MaximumStreamlineLength = length
    for xd, d in slices.items():
        d.Visibility = int(length >= xd)
    style.save(view, out / f"frame_{k:03d}.png", width, height)
    print(k, end=" ", flush=True)
print()
