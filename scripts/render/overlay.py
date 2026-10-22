"""LaTeX overlay for the website and README figures, after the OpenONDA tutorial figures.

Figure spec
- Canvas 125 mm wide (the OpenONDA figure width), height set by the content.
- Text: New PX at 10.95 pt, white on black. That is about 3 % of the image
  width, so it reads as ~12.5 pt where READMEs show the figure 560 px wide and
  ~10.5 pt on the 475 px website cards.
- Each panel is trimmed to its content (anything brighter than the background)
  plus a small margin, so there is no empty headroom.
- Panel labels sit in a strip above their panel; the single colour bar is short
  and sits in the bottom-right corner, in its own column. Neither may cover
  the drawing: compose() checks that every pixel the overlay changes was
  background, and fails otherwise.
Writes <stem>.pdf, <stem>.png (2400 px wide) and <stem>.webp (quality 85).

    compose([("raw.png", "Rotor only"), ("raw2.png", "Four wings")], "out/fig",
            bar=dict(name="thesis_blue", vmin=0, vmax=0.6, title=r"$1-u_x/U_\\infty$"))
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from onda_style import colour

WIDTH_MM = 125.0
PIXELS = 2400
PX_PER_MM = PIXELS / WIDTH_MM
MARGIN_MM = 2.5            # around the canvas edge and between panels
LABEL_MM = 6.5             # strip above a labelled panel
BAR = dict(width=2.2, height=16.0, column=17.0, labels=6.0)   # bar size, its column, room for tick labels [mm]
BACKGROUND = 18            # grey level below which a pixel counts as background


def trim(img, pad_mm=1.0, box_only=False):
    """Crop to pixels brighter than the background, plus pad_mm (box_only: return the box)."""
    a = np.asarray(img.convert("L"))
    rows, cols = np.where(a > BACKGROUND)
    pad = int(pad_mm * PX_PER_MM)
    box = (max(cols.min() - pad, 0), max(rows.min() - pad, 0),
           min(cols.max() + pad + 1, img.width), min(rows.max() + pad + 1, img.height))
    return box if box_only else img.crop(box)


def _num(v):
    return f"{v:g}".replace("-", "$-$")


def compose(panels, stem, bar=None, layout="column", check=True, notes=()):
    """panels: list of (image path, label or None); layout: "column" or "row".
    notes: point annotations on the first panel, (fx, fy, text, anchor, dx_mm, dy_mm) with
    fx, fy fractions of the raw image from its lower-left corner. Notes are meant to sit
    on the drawing, so the overlap check ignores them.
    bar: dict(name, vmin, vmax, title, fade=0.0, ticks=[(fraction, text), ...])."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    raws = [Image.open(p).convert("RGB") for p, _ in panels]
    boxes = [trim(r, box_only=True) for r in raws]
    imgs = [r.crop(b) for r, b in zip(raws, boxes)]
    labels = [lab for _, lab in panels]
    bar_mm = BAR["column"] if bar else 0.0
    avail = WIDTH_MM - 2 * MARGIN_MM - bar_mm
    if layout == "column":
        widths = [avail] * len(imgs)
    else:   # row: equal heights, total width = avail
        gaps = MARGIN_MM * (len(imgs) - 1)
        k = sum(i.width / i.height for i in imgs)
        widths = [(avail - gaps) * (i.width / i.height) / k for i in imgs]
    heights = [w * i.height / i.width for w, i in zip(widths, imgs)]
    lab_mm = LABEL_MM if any(labels) else 0.0
    if layout == "column":
        H = MARGIN_MM + sum(h + lab_mm for h in heights) + MARGIN_MM * len(imgs)
    else:
        H = 2 * MARGIN_MM + lab_mm + max(heights)
    if bar:
        H = max(H, BAR["height"] + 12.0)
    H = round(H, 2)

    # base raster: panels on black, positions in mm from the top-left
    W_px, H_px = PIXELS, int(round(H * PX_PER_MM))
    base = Image.new("RGB", (W_px, H_px))
    places, y, x = [], MARGIN_MM, MARGIN_MM
    for img, w, h in zip(imgs, widths, heights):
        if layout == "column":
            px, py = MARGIN_MM, y + lab_mm
            y = py + h + MARGIN_MM
        else:
            px, py = x, MARGIN_MM + lab_mm + (max(heights) - h) / 2
            x += w + MARGIN_MM
        places.append((px, py, w, h))
        base.paste(img.resize((int(w * PX_PER_MM), int(h * PX_PER_MM)), Image.LANCZOS),
                   (int(px * PX_PER_MM), int(py * PX_PER_MM)))

    work = Path(tempfile.mkdtemp())
    base.save(work / "base.png")
    body = []
    for (px, py, w, h), lab in zip(places, labels):
        if lab:   # in a row, all labels share one baseline above the tallest panel
            top = MARGIN_MM + lab_mm if layout == "row" else py
            body.append(rf"\node[anchor=base west,white,inner sep=0] at ({px + 0.5},{H - top + 2.0}) {{{lab}}};")
    if bar:
        bw, bh = BAR["width"], BAR["height"]
        # tucked into the bottom-right corner: tick labels end at the right margin
        bx = WIDTH_MM - MARGIN_MM - BAR["labels"] - 0.9 - bw
        by = MARGIN_MM
        n = 64
        for k in range(n):
            r, g, b = colour(bar["name"], (k + 0.5) / n, bar.get("fade", 0.0))
            body.append(rf"\definecolor{{c{k}}}{{rgb}}{{{r:.4f},{g:.4f},{b:.4f}}}")
            body.append(rf"\fill[c{k}] ({bx},{by + bh * k / n:.4f}) rectangle ({bx + bw},{by + bh * (k + 1) / n:.4f});")
        body.append(rf"\draw[white,line width=0.5pt] ({bx},{by}) rectangle ({bx + bw},{by + bh});")
        ticks = bar.get("ticks") or [(0.0, _num(bar["vmin"])), (1.0, _num(bar["vmax"]))]
        for f, text in ticks:
            yy = by + bh * f
            body.append(rf"\draw[white,line width=0.5pt] ({bx + bw},{yy}) -- ({bx + bw + 0.9},{yy});")
            body.append(rf"\node[anchor=west,white,inner sep=0.5mm] at ({bx + bw + 0.9},{yy}) {{{text}}};")
        body.append(rf"\node[anchor=south east,white,inner sep=0] at ({WIDTH_MM - MARGIN_MM},{by + bh + 2.2}) {{{bar['title']}}};")
    def latex(name, lines):
        tex = r"""\documentclass[tikz,border=0pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{newpxtext,newpxmath}
\usepackage{graphicx}
\begin{document}
\begin{tikzpicture}[x=1mm,y=1mm,font=\fontsize{10.95}{13.1}\selectfont]
\clip (0,0) rectangle (%s,%s);
\node[anchor=south west,inner sep=0] at (0,0) {\includegraphics[width=%smm,height=%smm]{base.png}};
%s
\end{tikzpicture}
\end{document}
""" % (WIDTH_MM, H, WIDTH_MM, H, "\n".join(lines))
        (work / f"{name}.tex").write_text(tex)
        run = subprocess.run(["pdflatex", "-interaction=nonstopmode", f"{name}.tex"], cwd=work, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(run.stdout[-2000:])
        subprocess.run(["pdftoppm", "-png", "-r", f"{PX_PER_MM * 25.4:.3f}", "-singlefile", f"{name}.pdf", name],
                       cwd=work, check=True)
        return Image.open(work / f"{name}.png").convert("RGB").resize((W_px, H_px), Image.LANCZOS)

    note_lines = []
    if notes:
        (px, py, w, h), (x0, y0, x1, y1), raw0 = places[0], boxes[0], raws[0]
        for fx, fy, text, anchor, dx, dy in notes:
            ix, iy = fx * raw0.width, (1 - fy) * raw0.height          # raw pixels from the top-left
            mx = px + (ix - x0) / (x1 - x0) * w + dx
            my = H - (py + (iy - y0) / (y1 - y0) * h) + dy
            note_lines.append(rf"\node[anchor={anchor},white,inner sep=0.4mm] at ({mx:.2f},{my:.2f}) {{{text}}};")
    out = latex("fig", body + note_lines)
    shutil.copy(work / "fig.pdf", stem.with_suffix(".pdf"))
    if check:   # every pixel the overlay changes must have been background
        plain = latex("plain", [])
        furniture = latex("furniture", body) if note_lines else out
        a, b = np.asarray(plain.convert("L")).astype(int), np.asarray(furniture.convert("L")).astype(int)
        changed = np.abs(a - b) > 40
        clash = changed & (a > BACKGROUND + 12)
        if clash.sum() > 0.002 * max(changed.sum(), 1):
            ys, xs = np.where(clash)
            raise RuntimeError(f"overlay covers the drawing near x = {xs.mean() / PX_PER_MM:.0f} mm, "
                               f"y = {ys.mean() / PX_PER_MM:.0f} mm from the top-left ({clash.sum()} px)")
    out.save(stem.with_suffix(".png"), optimize=True)
    out.save(stem.with_suffix(".webp"), quality=85, method=6)
    shutil.rmtree(work)
    print(stem.with_suffix(".webp"), f"{stem.with_suffix('.webp').stat().st_size / 1e3:.0f} kB", out.size,
          f"{WIDTH_MM:g} x {H:g} mm")
