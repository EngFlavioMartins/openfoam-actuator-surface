"""LaTeX overlay for the website renders, after the OpenONDA tutorial figures.

Puts a raw render on a fixed 16:10 canvas (90 mm x 56.25 mm) and adds white
New PX text at 10.95 pt plus at most one vertical colour bar with end ticks.
At the 600 px card width that text is about 26 px high, so it stays legible.
Writes <stem>.pdf, <stem>.png (2400 px wide) and <stem>.webp (quality 85).

    compose("raw.png", "out/figure", bar=dict(name="thesis_blue", vmin=0, vmax=5,
            title=r"$|\\omega|$ [1/s]"), labels=[(60, 40, r"$\\mathbf{U}$")])
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from onda_style import colour

WIDTH_MM, HEIGHT_MM = 90.0, 56.25
PIXELS = 2400


def _num(v):
    return f"{v:.2g}".replace("e+0", "e").replace("-", "$-$") if isinstance(v, float) else str(v)


def compose(raw, stem, bar=None, labels=(), crop=None):
    """bar: dict(name, vmin, vmax, title, fade=0.0, x=4, y=14, height=24, ticks=None)
    labels: (x_mm, y_mm, latex, anchor) from the lower-left corner.
    crop: (left, top, right, bottom) fractions removed from the raw image."""
    raw, stem = Path(raw).resolve(), Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp())
    img = Image.open(raw).convert("RGB")
    if crop:
        w, h = img.size
        img = img.crop((int(crop[0] * w), int(crop[1] * h), int(w - crop[2] * w), int(h - crop[3] * h)))
    # fill the canvas: scale to cover 16:10, centred
    target = WIDTH_MM / HEIGHT_MM
    w, h = img.size
    if w / h > target:
        nw = int(h * target)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    img.save(work / "raw.png")

    body = [rf"\node[anchor=south west,inner sep=0] at (0,0) {{\includegraphics[width={WIDTH_MM}mm,height={HEIGHT_MM}mm]{{raw.png}}}};"]
    if bar:
        x, y, hgt, wid = bar.get("x", 4.0), bar.get("y", 14.0), bar.get("height", 24.0), 3.2
        n = 64
        for k in range(n):
            r, g, b = colour(bar["name"], (k + 0.5) / n, bar.get("fade", 0.0))
            body.append(rf"\definecolor{{c{k}}}{{rgb}}{{{r:.4f},{g:.4f},{b:.4f}}}")
            body.append(rf"\fill[c{k}] ({x},{y + hgt * k / n:.4f}) rectangle ({x + wid},{y + hgt * (k + 1) / n:.4f});")
        body.append(rf"\draw[white,line width=0.6pt] ({x},{y}) rectangle ({x + wid},{y + hgt});")
        ticks = bar.get("ticks") or [(0.0, _num(bar["vmin"])), (1.0, _num(bar["vmax"]))]
        for f, text in ticks:
            yy = y + hgt * f
            body.append(rf"\draw[white,line width=0.6pt] ({x + wid},{yy}) -- ({x + wid + 1.2},{yy});")
            body.append(rf"\node[anchor=west,white,inner sep=0.6mm] at ({x + wid + 1.2},{yy}) {{{text}}};")
        body.append(rf"\node[anchor=south west,white,inner sep=0] at ({x - 0.4},{y + hgt + 2.4}) {{{bar['title']}}};")
    for lab in labels:
        xx, yy, text = lab[:3]
        anchor = lab[3] if len(lab) > 3 else "center"
        body.append(rf"\node[anchor={anchor},white,inner sep=0.5mm] at ({xx},{yy}) {{{text}}};")
    tex = (r"""\documentclass[tikz,border=0pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{newpxtext,newpxmath}
\usepackage{graphicx}
\begin{document}
\begin{tikzpicture}[x=1mm,y=1mm,font=\fontsize{10.95}{13.1}\selectfont]
\clip (0,0) rectangle (%s,%s);
\fill[black] (0,0) rectangle (%s,%s);
%s
\end{tikzpicture}
\end{document}
""" % (WIDTH_MM, HEIGHT_MM, WIDTH_MM, HEIGHT_MM, "\n".join(body)))
    (work / "fig.tex").write_text(tex)
    run = subprocess.run(["pdflatex", "-interaction=nonstopmode", "fig.tex"], cwd=work, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(run.stdout[-2000:])
    shutil.copy(work / "fig.pdf", stem.with_suffix(".pdf"))
    dpi = PIXELS / (WIDTH_MM / 25.4)
    subprocess.run(["pdftoppm", "-png", "-r", f"{dpi:.3f}", "-singlefile", "fig.pdf", "out"], cwd=work, check=True)
    out = Image.open(work / "out.png").convert("RGB")
    out = out.resize((PIXELS, round(PIXELS * HEIGHT_MM / WIDTH_MM)), Image.LANCZOS)
    out.save(stem.with_suffix(".png"), optimize=True)
    out.save(stem.with_suffix(".webp"), quality=85, method=6)
    shutil.rmtree(work)
    for ext in (".png", ".webp"):
        print(stem.with_suffix(ext), f"{stem.with_suffix(ext).stat().st_size / 1e3:.0f} kB", out.size)
