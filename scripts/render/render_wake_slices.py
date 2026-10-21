"""ParaView (pvpython) render of the actuator-surface wake.

Translucent cross-flow planes of streamwise velocity behind the rotor, stream
tubes seeded at the ends of each actuator strip, and the actuators themselves.

Usage: pvpython render_wake_slices.py <case dir> <output png> [width height]
The case must hold a reconstructed solution (see cases/openfoam-v2412/).
Colour: u_x / U_inf with Crameri's "lajolla" (dark red = slow wake, pale = free stream).
"""
import json
import re
import sys
from pathlib import Path

from paraview.simple import (AppendDatasets, Box, Calculator, CellDatatoPointData, ColorBy,
                             GetActiveViewOrCreate, GetColorTransferFunction, OpenFOAMReader, Plane,
                             PointSource, ResampleWithDataset, SaveScreenshot, Show,
                             StreamTracerWithCustomSource, Tube)

case, out = Path(sys.argv[1]), Path(sys.argv[2])
width, height = (int(a) for a in (sys.argv[3:5] if len(sys.argv) > 4 else (2400, 1600)))
HERE = Path(__file__).resolve().parent
U_INF, X_ROTOR = 4.0, 10.0                    # inflow speed [m/s]; rotor plane x [m] (rotor side D = 1 m)
SLICES = [1, 4, 7, 10]                        # x/D downstream of the rotor
PLANE_Y, PLANE_Z = (0.0, 2.9), (8.5, 11.5)    # extent of each plane [m]
(case / "case.foam").touch()

reader = OpenFOAMReader(FileName=str(case / "case.foam"))
reader.MeshRegions = ["internalMesh"]
reader.CellArrays = ["U"]
t = max(reader.TimestepValues)
pdata = CellDatatoPointData(Input=reader)
ux = Calculator(Input=pdata, ResultArrayName="ux_norm", Function=f"U_X/{U_INF}")

view = GetActiveViewOrCreate("RenderView")
view.ViewSize = [width, height]
view.ViewTime = t
view.OrientationAxesVisibility = 0
view.UseColorPaletteForBackground = 0
view.Background = [1, 1, 1]
view.EnableRayTracing = 1
view.BackEnd = "OSPRay raycaster"
view.SamplesPerPixel = 32
view.AmbientSamples = 8
view.Shadows = 0


def grey(display, rgb, opacity=1.0):
    display.ColorArrayName = ["POINTS", ""]
    display.AmbientColor = display.DiffuseColor = rgb
    display.Opacity = opacity
    display.Specular, display.SpecularPower = 0.45, 40


# velocity planes, resampled onto exact rectangles
lut = GetColorTransferFunction("ux_norm")
lut.RGBPoints = json.loads((HERE / "lajolla.json").read_text())["lajolla"]
lut.ColorSpace = "RGB"
lut.AutomaticRescaleRangeMode = "Never"
for xd in SLICES:
    x = X_ROTOR + xd
    plane = Plane(Origin=[x, PLANE_Y[0], PLANE_Z[0]], Point1=[x, PLANE_Y[1], PLANE_Z[0]],
                  Point2=[x, PLANE_Y[0], PLANE_Z[1]], XResolution=180, YResolution=180)
    s = ResampleWithDataset(SourceDataArrays=ux, DestinationMesh=plane)
    s.CellLocator = "Static Cell Locator"
    d = Show(s, view)
    ColorBy(d, ("POINTS", "ux_norm"))
    d.LookupTable = lut
    d.SetScalarBarVisibility(view, False)
    d.Opacity = 0.93
    d.Ambient, d.Diffuse, d.Specular = 0.35, 0.65, 0.0
lut.RescaleTransferFunction(0.33, 1.02)       # after ColorBy, which rescales to the data

# actuators from the topoSet boxes: rotor plate (translucent) and wing strips
def box(lo, hi, rgb, opacity):
    b = Box(XLength=hi[0] - lo[0], YLength=hi[1] - lo[1], ZLength=hi[2] - lo[2],
            Center=[(a + b) / 2 for a, b in zip(lo, hi)])
    grey(Show(b, view), rgb, opacity)


strips = []
for lo, hi in re.findall(r"box\s*\(([^)]*)\)\s*\(([^)]*)\)", (case / "system" / "topoSetDict").read_text()):
    lo, hi = [float(v) for v in lo.split()], [float(v) for v in hi.split()]
    if hi[1] - lo[1] > 0.5:
        box(lo, hi, [0.72, 0.74, 0.76], 0.5)                     # rotor
        rotor = (lo, hi)
    else:
        strips.append((lo, hi))
blades = "BladeForce = vector(0.0, 0.0, 0.0)" not in (case / "ActuatorsSetup").read_text().replace("0.00", "0.0")
if blades:
    for lo, hi in strips:
        box(lo, hi, [0.42, 0.45, 0.50], 1.0)
box([X_ROTOR - 0.01, 0.0, 9.98], [X_ROTOR + 0.01, rotor[0][1], 10.02], [0.48, 0.51, 0.55], 1.0)   # mast

# stream tubes seeded behind the ends of each wing strip (rotor edges without wings)
heights = [(lo[1] + hi[1]) / 2 for lo, hi in strips] if blades else [rotor[0][1] + 0.05, rotor[1][1] - 0.05]
seeds = AppendDatasets(Input=[PointSource(Center=[X_ROTOR + 0.12, y, z], Radius=0.05, NumberOfPoints=5)
                              for y in heights for z in (rotor[0][2] + 0.02, rotor[1][2] - 0.02)])
st = StreamTracerWithCustomSource(Input=pdata, SeedSource=seeds)
st.Vectors = ["POINTS", "U"]
st.IntegrationDirection = "FORWARD"
st.MaximumStreamlineLength = 11.0
tubes = Tube(Input=st)
tubes.Radius = 0.008
tubes.NumberofSides = 16
grey(Show(tubes, view), [0.40, 0.43, 0.48])

view.CameraPosition = [7.4, 4.0, 22.6]
view.CameraFocalPoint = [14.9, 1.05, 10.0]
view.CameraViewUp = [0, 1, 0]
view.CameraViewAngle = 30
SaveScreenshot(str(out), view, ImageResolution=[width, height], TransparentBackground=0)
print(out)
