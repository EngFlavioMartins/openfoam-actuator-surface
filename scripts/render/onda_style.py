"""Render style shared by the website figures, after the OpenONDA tutorial renders.

Import from ParaView's pvpython (view and material helpers) or from plain
Python (colour maps only); ParaView is imported lazily.

Rules:
- black background; the low end of each sequential map fades into it;
- one-hue OpenONDA maps: thesis_blue for magnitudes, thesis_signed for signed
  fields with a meaningful zero (signed_dark on black), thesis_amber for streamlines and trajectories;
- solids are matte grey PBR; no outlines, axes or floors;
- OpenGL with the OpenONDA light kit and filmic tone mapping;
- text and the single colour bar are added afterwards by overlay.py (LaTeX,
  New PX), large enough to read at the figure's display size.
"""

STOPS = {
    "thesis_blue": ["#0D3D45", "#156074", "#41A6C4", "#C8EDF5"],
    "thesis_amber": ["#6B3019", "#B45D1E", "#EF9C1F", "#FFF0CA"],
    "thesis_signed": ["#156074", "#F5F6F5", "#BF2326"],
    # thesis_signed for black backgrounds: same end hues, zero fades into the black
    "signed_dark": ["#C8EDF5", "#41A6C4", "#156074", "#000000", "#8E1A1C", "#BF2326", "#F6B9A6"],
}
GREY = [96 / 255, 104 / 255, 108 / 255]          # OpenONDA surface grey
LIGHT_GREY = [0.64, 0.64, 0.64]                    # OpenONDA arrow grey
BLACK = [0.0, 0.0, 0.0]


def _hex(c):
    return [int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def colour(name, t, fade_from_black=0.0):
    """RGB of map ``name`` at t in [0, 1]. With fade_from_black > 0 the lowest
    fraction of the map blends linearly into black (for glowing on black)."""
    stops = [_hex(c) for c in STOPS[name]]
    x = min(max(t, 0.0), 1.0) * (len(stops) - 1)
    i = min(int(x), len(stops) - 2)
    f = x - i
    rgb = [a + f * (b - a) for a, b in zip(stops[i], stops[i + 1])]
    if fade_from_black > 0 and t < fade_from_black:
        rgb = [c * t / fade_from_black for c in rgb]
    return rgb


def rgb_points(name, vmin, vmax, n=33, fade_from_black=0.0):
    """ParaView RGBPoints for map ``name`` over [vmin, vmax]."""
    out = []
    for k in range(n):
        t = k / (n - 1)
        out += [vmin + t * (vmax - vmin), *colour(name, t, fade_from_black)]
    return out


def setup_view(width, height):
    """Black OpenGL view with the OpenONDA light kit and filmic tone mapping."""
    from paraview.simple import GetActiveViewOrCreate
    view = GetActiveViewOrCreate("RenderView")
    view.ViewSize = [width, height]
    view.OrientationAxesVisibility = 0
    view.UseColorPaletteForBackground = 0
    view.Background = BLACK
    view.EnableRayTracing = 0
    for name, value in {
        "UseEnvironmentLighting": 0, "UseLight": 1, "UseToneMapping": 1, "ToneMappingType": 3,
        "UseFXAA": 1, "Exposure": 1.5, "Contrast": 1.6773, "Shoulder": 0.9714,
        "MidIn": 0.18, "MidOut": 0.18, "KeyLightIntensity": 0.75, "KeyLightAzimuth": 10,
        "KeyLightElevation": 50, "KeyLightWarmth": 0.6, "FillLightAzimuth": -10,
        "FillLightElevation": -75, "FillLightWarmth": 0.4, "BackLightAzimuth": 110,
        "BackLightElevation": 0, "BackLightWarmth": 0.5, "HeadLightWarmth": 0.5,
        "FillLightKFRatio": 3, "BackLightKBRatio": 3.5, "HeadLightKHRatio": 3,
    }.items():
        setattr(view, name, value)
    return view


def solid(display, rgb=GREY, roughness=0.35, opacity=1.0):
    """Matte PBR surface in a flat colour."""
    display.Representation = "Surface"
    display.ColorArrayName = ["POINTS", ""]
    display.DiffuseColor = display.AmbientColor = rgb
    display.Interpolation = "PBR"
    display.Metallic = 0.04
    display.Roughness = roughness
    display.Opacity = opacity


def mapped(display, array, lut, assoc="POINTS", roughness=0.35):
    """PBR surface coloured by ``array`` through ``lut``."""
    from paraview.simple import ColorBy
    display.Representation = "Surface"
    ColorBy(display, (assoc, array))
    display.LookupTable = lut
    display.Interpolation = "PBR"
    display.Metallic = 0.0
    display.Roughness = roughness


def lut(array, name, vmin, vmax, fade_from_black=0.0):
    from paraview.simple import GetColorTransferFunction
    t = GetColorTransferFunction(array)
    t.AutomaticRescaleRangeMode = "Never"
    t.ColorSpace = "RGB"
    t.RGBPoints = rgb_points(name, vmin, vmax, fade_from_black=fade_from_black)
    return t


def save(view, path, width, height):
    from paraview.simple import SaveScreenshot
    view.Update()
    SaveScreenshot(str(path), view, ImageResolution=[width, height],
                   TransparentBackground=0, CompressionLevel=0)
