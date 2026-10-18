#!/usr/bin/env python3
"""
A halftone of a photo for the floor of the arch design's pocket, like a
newspaper picture: the photo drawn in dots, or in dashes, that are bigger
where it's dark. They're inlaid flush in the floor in the name's colour, so
it shows in any light (no backlight needed) and the cup still sits flat.

    python3 halftone.py photo.jpg            -> private/ (git-ignored), both styles
    python3 halftone.py photo.jpg dots       just one: dots or dashes

    dots     a hexagonal grid of round dots, bigger where it's darker
    dashes   rows of lines, thicker where it's darker, broken into dashes
             where it's light (an engraving look; it keeps more detail
             across the rows than dots do)

Like portrait.py, the photo and everything made from it are someone's
likeness, so it all goes in private/ and never gets committed. Writes, per style:

    private/halftone_<style>.png                the pattern, to check before printing
    private/stl/halftone_<style>.stl, _ink.stl  the base and the dots and name
    private/images/halftone_<style>*.png        renders
    private/emilys_cup_halftone_<style>.3mf     the Bambu Studio project, two AMS filaments

The face is framed like portrait.py's and the background fades to nothing.
Needs the same packages as portrait.py.
"""
import os, sys
import numpy as np
import cv2
import manifold3d as mf
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as B
import portrait as P
import lithophane as L

PRIVATE = P.PRIVATE

# ---------------------------------------------------------------- parameters
ART_R = P.ART_R                 # mm; the pattern fills this circle in the pocket floor
FRAME = P.FRAME                 # mm; the ring round it
INLAY = P.INLAY                 # mm deep, flush with the floor
MIN_MARK = 0.8                  # mm; the smallest dot or thinnest dash (two nozzle widths)
DROP = 0.55                     # mm; marks that would be smaller than this are left out, between
                                # this and MIN_MARK they're printed at MIN_MARK
GAMMA = 1.15                    # darkness is raised to this: above 1 lightens the midtones (skin),
                                # so the face isn't buried in dots
SHARPEN = (1.2, 1.5)            # unsharp mask (amount, mm): makes the eyes, brows and smile stand out
STRETCH = (5, 99)               # percentiles of the person's darkness that become white and black

DOT_PITCH = 1.4                 # mm between dot centres (a hexagonal grid)
DOT_MAX = 0.58                  # the darkest dot's radius, in pitches (over 0.5, so they merge into black)

DASH_PITCH = 1.3                # mm between rows
DASH_MAX = 1.25                 # the thickest dash, in pitches (over 1, so rows merge into black)
DASH_STEP = 0.25                # mm; how finely the thickness follows the photo along a row
DASH_WAVE = (0.35, 9.0)         # mm; a gentle wave in the rows (height, wavelength); (0, 1) for straight

COLOURS = ["#BDA8E2", "#4B2E83"]       # lilac base, dark purple dots and name
STEP = 0.1                              # mm; the photo's sampling grid
STYLES = ("dots", "dashes")


def darkness(photo):
    """0 (white) .. 1 (black) on a STEP grid over the art circle, and a lookup for any (x, y) in mm"""
    light = L.picture(photo, frame_r=ART_R - FRAME, half=ART_R, step=STEP)
    dark = np.clip(1 - light, 0, 1)
    lo, hi = np.percentile(dark[dark > 0.05], STRETCH)     # over the person, not the faded background
    dark = np.clip((dark - lo) / (hi - lo), 0, 1)
    amount, size = SHARPEN
    dark = dark + amount * (dark - cv2.GaussianBlur(dark, (0, 0), size / STEP))
    dark = np.clip(dark, 0, 1) ** GAMMA
    n = dark.shape[0]
    def at(x, y):
        i = np.clip(np.round(y / STEP + (n - 1) / 2).astype(int), 0, n - 1)
        j = np.clip(np.round(x / STEP + (n - 1) / 2).astype(int), 0, n - 1)
        return dark[i, j]
    return at


def mark_size(want):
    """sizes below DROP vanish, ones between DROP and MIN_MARK are raised to MIN_MARK"""
    return np.where(want < DROP, 0.0, np.maximum(want, MIN_MARK))


def dots(at):
    inner = ART_R - FRAME - 0.4
    p = DOT_PITCH
    rows = np.arange(-inner, inner + p, p * np.sqrt(3) / 2)
    cells = []
    for k, y in enumerate(rows):
        xs = np.arange(-inner, inner + p, p) + (p / 2 if k % 2 else 0)
        cells += [(x, y) for x in xs]
    c = np.array(cells)
    c = c[np.hypot(c[:, 0], c[:, 1]) < inner]
    # a dot's area is the cell's area times the darkness, up to DOT_MAX
    cell = p * p * np.sqrt(3) / 2
    r = np.minimum(np.sqrt(at(c[:, 0], c[:, 1]) * cell / np.pi), DOT_MAX * p)
    d = mark_size(2 * r)
    circles = [mf.CrossSection.circle(di / 2, 20).translate((x, y)) for (x, y), di in zip(c, d) if di > 0]
    return mf.CrossSection.batch_boolean(circles, mf.OpType.Add)


def dashes(at):
    inner = ART_R - FRAME - 0.4
    p = DASH_PITCH
    amp, wavelength = DASH_WAVE
    pieces = []
    for y0 in np.arange(-inner + p / 2, inner, p):
        half = np.sqrt(max(inner * inner - y0 * y0, 0))
        x = np.arange(-half, half + DASH_STEP, DASH_STEP)
        y = y0 + amp * np.sin(2 * np.pi * x / wavelength)
        w = mark_size(np.minimum(at(x, y), 1) * DASH_MAX * p)
        on = w > 0
        # each run of samples with ink becomes one dash: its top edge out, its bottom edge back
        edges = np.flatnonzero(np.diff(np.concatenate([[0], on.astype(int), [0]])))
        for a, b in zip(edges[::2], edges[1::2]):
            if b - a < 2:                                  # a single sample: make it a round dot
                pieces.append(mf.CrossSection.circle(w[a] / 2, 16).translate((x[a], y[a])))
                continue
            top = np.column_stack([x[a:b], y[a:b] + w[a:b] / 2])
            bot = np.column_stack([x[a:b], y[a:b] - w[a:b] / 2])[::-1]
            dash = mf.CrossSection([np.vstack([top, bot])], mf.FillRule.NonZero)
            # round the ends, so the dashes look drawn rather than cut
            ends = (mf.CrossSection.circle(w[a] / 2, 16).translate((x[a], y[a])) +
                    mf.CrossSection.circle(w[b - 1] / 2, 16).translate((x[b - 1], y[b - 1])))
            pieces.append(dash + ends)
    return mf.CrossSection.batch_boolean(pieces, mf.OpType.Add)


def frame_ring():
    return mf.CrossSection.circle(ART_R, B.SEG * 2) - mf.CrossSection.circle(ART_R - FRAME, B.SEG * 2)


def save_png(cs, path, px=0.05):
    n = int(2 * ART_R / px) + 2
    img = np.full((n, n), 255, np.uint8)
    polys = [np.round((np.asarray(p) * [1, -1] + ART_R) / px).astype(np.int32) for p in cs.to_polygons()]
    cv2.fillPoly(img, polys, 0)                 # even-odd, like the CrossSection
    cv2.imwrite(path, img)


def build(style, at):
    raw = (dots(at) if style == "dots" else dashes(at)) + frame_ring()
    name = f"halftone_{style}"
    # drop near-duplicate points (see portrait.py); where marks only just touch, that can take a
    # few goes, and a slightly bigger tolerance (still far below what prints) sorts it out
    for eps in (0.005, 0.01, 0.02, 0.04):
        art = raw.simplify(eps)
        base, ink = B.arch(hearts=False, floor_art=art, inlay=INLAY)
        ink = ink - base
        ok = True
        for n, m in ((name, base), (name + "_ink", ink)):
            B.to_trimesh(m).export(os.path.join(PRIVATE, "stl", n + ".stl"))
            ok &= trimesh.load(os.path.join(PRIVATE, "stl", n + ".stl")).is_watertight
        if ok:
            break
    else:
        raise SystemExit(f"{name}: the STLs come out broken")
    save_png(art, os.path.join(PRIVATE, f"halftone_{style}.png"))
    print(f"{style:7s} 122 x 122 x {B.BASE_H + B.LETTER_H:.1f} mm, "
          f"{len(art.to_polygons())} marks, ink {ink.volume() / 1000:.2f} cm3")
    render(name)
    project(name, style)


def render(name):
    import render as R
    out = os.path.join(PRIVATE, "images")
    os.makedirs(out, exist_ok=True)
    rgb = lambda h: tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    stl = lambda n: os.path.join(PRIVATE, "stl", n + ".stl")
    parts = lambda: [R.actor(stl(name), rgb(COLOURS[0])),
                     R.actor(stl(name + "_ink"), rgb(COLOURS[1]), (0, 0, 0.02), 0.4)]   # lifted for the renderer
    R.shot(parts(), os.path.join(out, name + "_top.png"), (0, 0, 3), 0, 89.9, 1.3, size=(1100, 1100))
    R.shot(parts(), os.path.join(out, name + ".png"), (0, 0, 3), 0, 48, 1.25)
    R.shot(parts() + [R.actor(R.cup(), R.CUP, (0, 0, B.FLOOR), 0.6, 0.55)], os.path.join(out, name + "_cup.png"),
           (0, 0, 30), 15, 22, 1.15, size=(1000, 1100))


def project(name, style):
    sys.path.insert(0, os.path.join(HERE, "..", "tools"))
    from bambu3mf import Part, write_project, BED
    from make_3mf import PROCESS, SETTINGS
    load = lambda n: trimesh.load(os.path.join(PRIVATE, "stl", n + ".stl"))
    c = BED / 2
    out = write_project(os.path.join(PRIVATE, f"emilys_cup_{name}.3mf"),
                        [Part(f"Emily's Cup ({style})", load(name), c, c,
                              extra=[(f"{style} and name", load(name + "_ink"), 2)])],
                        PROCESS, SETTINGS, title=f"Emily's Cup: halftone {style}",
                        description="Load lilac PLA as filament 1 and dark purple as filament 2. "
                                    f"The {style} are inlaid flush in the pocket floor; the name stands 1.2 mm proud.",
                        thumbnail_png=os.path.join(PRIVATE, "images", name + "_top.png"), filament_colour=COLOURS)
    print("wrote", out)


def main():
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] not in STYLES):
        raise SystemExit(__doc__)
    os.makedirs(os.path.join(PRIVATE, "stl"), exist_ok=True)
    at = darkness(sys.argv[1])
    for style in (sys.argv[2:] or STYLES):
        build(style, at)


if __name__ == "__main__":
    main()
