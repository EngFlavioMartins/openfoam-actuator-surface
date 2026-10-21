"""ParaView (pvpython) render of the actuator-surface wake in the OpenONDA style.

Usage: pvpython render_wake.py <case dir> <output png> [width height]

Black background. Cross-flow planes show the velocity deficit 1 - u_x/U_inf
with thesis_blue; free stream fades into the black, so only the wake glows.
Streamlines from the ends of the actuators use thesis_amber; the rotor plate,
wing strips and mast are matte grey.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import onda_style as style  # noqa: E402
from paraview.simple import (AppendDatasets, Box, Calculator, CellDatatoPointData, GetOpacityTransferFunction,  # noqa: E402
                             OpenFOAMReader, Plane, PointSource, ResampleWithDataset, Show,
                             StreamTracerWithCustomSource, Tube)

case, out = Path(sys.argv[1]), Path(sys.argv[2])
width, height = (int(a) for a in (sys.argv[3:5] if len(sys.argv) > 4 else (2400, 750)))
U_INF, X_ROTOR = 4.0, 10.0
SLICES = [1, 4, 7, 10]
DEFICIT_MAX = 0.62
(case / "case.foam").touch()

reader = OpenFOAMReader(FileName=str(case / "case.foam"))
reader.MeshRegions = ["internalMesh"]
reader.CellArrays = ["U"]
t = max(reader.TimestepValues)
pdata = CellDatatoPointData(Input=reader)
deficit = Calculator(Input=pdata, ResultArrayName="deficit", Function=f"1 - U_X/{U_INF}")

view = style.setup_view(width, height)
view.ViewTime = t
lut = style.lut("deficit", "thesis_blue", 0.0, DEFICIT_MAX, fade_from_black=0.35)
lut.EnableOpacityMapping = 1
pwf = GetOpacityTransferFunction("deficit")
pwf.Points = [0.0, 0.0, 0.5, 0.0, 0.06, 0.0, 0.5, 0.0, 0.22, 0.8, 0.5, 0.0, DEFICIT_MAX, 1.0, 0.5, 0.0]

for xd in SLICES:
    x = X_ROTOR + xd
    plane = Plane(Origin=[x, 0.0, 8.5], Point1=[x, 2.9, 8.5], Point2=[x, 0.0, 11.5], XResolution=200, YResolution=200)
    s = ResampleWithDataset(SourceDataArrays=deficit, DestinationMesh=plane)
    s.CellLocator = "Static Cell Locator"
    d = Show(s, view)
    style.mapped(d, "deficit", lut)
    d.Interpolation = "Flat"
    d.Ambient, d.Diffuse = 1.0, 0.0            # unlit: the field glows
lut.RescaleTransferFunction(0.0, DEFICIT_MAX)

def box(lo, hi, rgb, opacity=1.0):
    b = Box(XLength=hi[0] - lo[0], YLength=hi[1] - lo[1], ZLength=hi[2] - lo[2],
            Center=[(a + c) / 2 for a, c in zip(lo, hi)])
    style.solid(Show(b, view), rgb, opacity=opacity)

strips = []
for lo, hi in re.findall(r"box\s*\(([^)]*)\)\s*\(([^)]*)\)", (case / "system" / "topoSetDict").read_text()):
    lo, hi = [float(v) for v in lo.split()], [float(v) for v in hi.split()]
    if hi[1] - lo[1] > 0.5:
        rotor = (lo, hi)
        box(lo, hi, style.LIGHT_GREY, 0.6)
    else:
        strips.append((lo, hi))
blades = "BladeForce = vector(0.0, 0.0, 0.0)" not in (case / "ActuatorsSetup").read_text().replace("0.00", "0.0")
if blades:
    for lo, hi in strips:
        box(lo, hi, style.LIGHT_GREY)
box([X_ROTOR - 0.012, 0.0, 9.988], [X_ROTOR + 0.012, rotor[0][1], 10.012], style.GREY)

heights = [(lo[1] + hi[1]) / 2 for lo, hi in strips] if blades else [rotor[0][1] + 0.05, rotor[1][1] - 0.05]
seeds = AppendDatasets(Input=[PointSource(Center=[X_ROTOR + 0.12, y, z], Radius=0.05, NumberOfPoints=5)
                              for y in heights for z in (rotor[0][2] + 0.02, rotor[1][2] - 0.02)])
st = StreamTracerWithCustomSource(Input=pdata, SeedSource=seeds)
st.Vectors = ["POINTS", "U"]
st.IntegrationDirection = "FORWARD"
st.MaximumStreamlineLength = 11.0
tubes = Tube(Input=st)
tubes.Radius = 0.009
tubes.NumberofSides = 12
style.solid(Show(tubes, view), style.colour("thesis_amber", 0.75), roughness=0.4)

view.CameraPosition = [8.4, 3.1, 18.2]
view.CameraFocalPoint = [15.1, 1.15, 10.0]
view.CameraViewUp = [0, 1, 0]
view.CameraViewAngle = 24
style.save(view, out, width, height)
print(out)
