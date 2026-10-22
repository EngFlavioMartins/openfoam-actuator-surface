"""Render style shared by the website figures, after the OpenONDA tutorial renders.

Import from ParaView's pvpython (view and material helpers) or from plain
Python (colour maps only); ParaView is imported lazily.

Rules:
- black background; the low end of each sequential map fades into it;
- one-hue OpenONDA maps: thesis_blue for magnitudes, thesis_signed for signed
  fields with a meaningful zero (signed_dark on black), thesis_amber for streamlines and trajectories;
- solids are matte grey PBR; metal parts use metal() (brushed, grainy metal);
  no outlines, axes or floors;
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


def _grain_textures(directory, size=512, seed=3):
    """Brushed-metal textures: an ORM map (occlusion, roughness, metallic) with
    streaky roughness, and a matching normal map. Written as PNG with VTK."""
    from pathlib import Path

    import numpy as np
    from vtkmodules.util.numpy_support import numpy_to_vtk
    from vtkmodules.vtkCommonDataModel import vtkImageData
    from vtkmodules.vtkIOImage import vtkPNGWriter
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal((size, size))
    # streaks: smooth strongly along u (the brushing direction), lightly along v
    k = np.exp(-np.linspace(-3, 3, 61) ** 2)
    streak = np.apply_along_axis(lambda r: np.convolve(np.r_[r[-30:], r, r[:30]], k / k.sum(), "valid"), 1, noise)
    fine = rng.standard_normal((size, size)) * 0.35
    h = streak / streak.std() + fine
    rough = np.clip(0.32 + 0.10 * h, 0.12, 0.7)
    orm = np.stack([np.ones_like(h), rough, np.full_like(h, 0.2)], -1)   # partly metallic: a black
    # background gives a fully metallic surface nothing to reflect, so keep some diffuse shading
    gy, gx = np.gradient(h)
    n = np.stack([-0.2 * gx, -0.2 * gy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    paths = {}
    for name, arr in (("metal_orm", orm), ("metal_normal", 0.5 * n + 0.5)):
        img = vtkImageData()
        img.SetDimensions(size, size, 1)
        img.GetPointData().SetScalars(numpy_to_vtk((arr * 255).astype(np.uint8).reshape(-1, 3), deep=1))
        path = Path(directory) / f"{name}.png"
        w = vtkPNGWriter()
        w.SetFileName(str(path))
        w.SetInputData(img)
        w.Write()
        paths[name] = str(path)
    return paths


def metal(source, view, mapping="cylinder", rgb=(0.92, 0.93, 0.95), repeat=(4.0, 1.0)):
    """Show ``source`` as brushed metal: metallic PBR with grainy roughness and
    micro-normals. mapping: how texture coordinates are laid on (cylinder,
    plane or sphere). Returns the display."""
    import tempfile
    from pathlib import Path as _P
    from paraview.simple import (CreateTexture, ExtractSurface, Show, SurfaceNormals, SurfaceTangents,
                                 TextureMaptoCylinder, TextureMaptoPlane, TextureMaptoSphere, Triangulate)
    mapper = {"cylinder": TextureMaptoCylinder, "plane": TextureMaptoPlane, "sphere": TextureMaptoSphere}[mapping]
    tc = mapper(Input=SurfaceNormals(Input=ExtractSurface(Input=source)))   # any dataset -> polygons
    if mapping == "cylinder":
        tc.PreventSeam = 0
    tangents = SurfaceTangents(Input=Triangulate(Input=tc))   # tangents need triangles
    tex = _grain_textures(_P(tempfile.mkdtemp()))
    d = Show(tangents, view)
    d.Representation = "Surface"
    d.ColorArrayName = ["POINTS", ""]
    d.DiffuseColor = d.AmbientColor = list(rgb)
    d.Interpolation = "PBR"
    d.Metallic = 1.0                       # scaled by the ORM texture's metallic channel
    d.Roughness = 1.0                      # scaled by the ORM texture's roughness channel
    d.MaterialTexture = CreateTexture(tex["metal_orm"])
    d.NormalTexture = CreateTexture(tex["metal_normal"])
    d.NormalScale = 1.0
    d.RepeatTextures = 1
    d.InterpolateTextures = 1
    d.TextureTransform = "Transform2"
    d.TextureTransform.Scale = [repeat[0], repeat[1], 1.0]
    return d
