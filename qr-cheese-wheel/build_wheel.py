#!/usr/bin/env python3
"""
A Swiss-cheese wheel with a wedge you slide out to find a QR code hidden
underneath, for handing over a digital gift card (or any link).

    python3 build_wheel.py                                 sample: wheel, wedge and a placeholder tile in stl/
    python3 build_wheel.py "https://your-link" [out_dir]   your tile, in private/ (git-ignored) by default

Three parts:

    wheel.stl     the wheel with a wedge-shaped notch.  At the bottom of the
                  notch is a shallow bay, closed at the rim by a lip, that
                  holds the tile.
    wedge.stl     slides into the notch, flush with the top and the rind.
                  A finger dimple on top lets you slide it out toward you.
    tile_*.stl    a thin plate that drops into the bay: the QR code and
                  ありがとう in a dark colour on cheese yellow.

Only the tile carries the link, so the wheel and wedge are the same for every
build and live in stl/.  If the link is a gift card the tile *is* the money,
so a real tile goes to private/ and never into git.

Holes that cross the cut are shared: a bubble on the notch wall leaves half a
dent in the wheel and half in the wedge, and they line up when it's closed.
"""
import os, sys
import numpy as np, qrcode, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- parameters (mm) -------------------------------------------------------
SAMPLE_URL = "https://www.olympiaprovisions.com/"
ECC = qrcode.constants.ERROR_CORRECT_M
MAX_MODULE = 1.6      # cap for short links
MIN_MODULE = 1.1      # refuse links that would print finer than this
QUIET = 2             # light border around the code, in modules

WHEEL_D = 210         # fits the A1's 256 mm bed
HEIGHT = 36
ANGLE = 80            # the wedge, degrees
BASE = 2.4            # wheel floor under the tile
TILE_T = 1.6          # tile plate
QR_HEIGHT = 0.8       # dark modules and letters above the plate
LIP = 3.0             # wall at the rim that keeps the tile from sliding out with the wedge
WEDGE_CLEAR = 0.3     # gap between the wedge and the notch walls
TILE_CLEAR = 0.25     # gap around the tile in its bay
DIMPLE_R = 11         # finger dimple on the wedge
SEED = 11
THANKS = "ありがとう"   # on the tile above the code; "" to omit
THANKS_FONT = ["/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
               "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
               "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
               "C:/Windows/Fonts/msgothic.ttc"]

R = WHEEL_D / 2
HALF = np.radians(ANGLE / 2)
TILE_TOP = BASE + TILE_T + QR_HEIGHT          # the wedge rests here, on the code and the lip
WEDGE_H = HEIGHT - TILE_TOP

# ---- helpers ---------------------------------------------------------------
def to_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)

def sector(radius, n=128, angle=ANGLE):
    a = np.radians(np.linspace(-angle / 2, angle / 2, n))
    return mf.CrossSection([[(0.0, 0.0)] + [(radius * np.cos(t), radius * np.sin(t)) for t in a]])

def teardrop(r):
    """A sphere with a 45-degree roof, so a hole in a wall needs no support."""
    tip = mf.Manifold.cylinder(r * np.sqrt(2), r / np.sqrt(2), 0.0, 32).translate([0, 0, r / np.sqrt(2)])
    return mf.Manifold.batch_hull([mf.Manifold.sphere(r, 48), tip])

def text_2d(text, height):
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    font = next((f for f in THANKS_FONT if os.path.exists(f)), None)
    if font is None:
        print("  no Japanese font found; leaving the text off"); return None
    tp = TextPath((0, 0), text, size=10, prop=FontProperties(fname=font))
    polys = [p for p in tp.to_polygons(closed_only=True) if len(p) >= 3]
    cs = mf.CrossSection([[tuple(v) for v in p[:-1]] for p in polys], mf.FillRule.EvenOdd)
    b = cs.bounds()
    s = height / (b[3] - b[1])
    return cs.translate([-(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2]).scale([s, s]).offset(0.15, mf.JoinType.Round)

def tile_outline():
    """The bay floor: the notch sector inside the lip, shrunk by the clearance."""
    return (sector(R - LIP) ).offset(-TILE_CLEAR, mf.JoinType.Miter)

def qr_square():
    """The largest square (code + quiet zone) that fits on the tile, pushed
    toward the rim to leave room for the text in front of it.
    Returns (side, x of the edge nearest the centre)."""
    inset = TILE_CLEAR + 1.5
    lo, hi = 20.0, 120.0
    for _ in range(50):
        s = (lo + hi) / 2
        x_front = (s / 2 + inset / np.cos(HALF)) / np.tan(HALF)
        ok = np.hypot(x_front + s, s / 2) <= R - LIP - inset
        lo, hi = (s, hi) if ok else (lo, s)
    s = lo
    x_back = np.sqrt((R - LIP - inset) ** 2 - (s / 2) ** 2)
    return s, x_back - s

# ---- parts -----------------------------------------------------------------
def bubbles():
    """Holes: (centre, radius, kind).  kind is 'cut' for bubbles on the two
    notch walls (shared by wheel and wedge), 'rind' / 'top' for the outside."""
    rng = np.random.default_rng(SEED)
    out = []

    def free(p, r):
        return all(np.linalg.norm(p - q) > r + rq + 3 for q, rq, _ in out)

    # on the notch walls: the planes at +/-HALF through the axis
    for sgn in (1, -1):
        along = np.array([np.cos(HALF), sgn * np.sin(HALF), 0])
        n = 0
        for _ in range(500):
            if n >= 4: break
            r = rng.uniform(3.5, 7.5)
            d = rng.uniform(20, R - 12)
            z = rng.uniform(TILE_TOP + r + 2, HEIGHT - r * 1.5 - 2)
            # centred in the 0.3 mm gap, not on either face, which would leave slivers
            p = along * d + np.array([np.sin(HALF), -sgn * np.cos(HALF), 0]) * WEDGE_CLEAR / 2; p[2] = z
            if free(p, r): out.append((p, r, "cut")); n += 1
    # around the rind, the wheel's and the wedge's
    n = 0
    for _ in range(800):
        if n >= 16: break
        r = rng.uniform(3, 7)
        t = rng.uniform(-np.pi, np.pi)
        if abs(abs(t) - HALF) * R < r + 2: continue                 # not across the seam
        z = rng.uniform(r + 2, HEIGHT - r * 1.5 - 2)
        if abs(t) < HALF: z = max(z, TILE_TOP + r + 2)              # wedge: keep clear of its bottom edge
        if z > HEIGHT - r * 1.5 - 2: continue
        rr = R + rng.uniform(-0.4, 0.4) * r
        p = np.array([rr * np.cos(t), rr * np.sin(t), z])
        if free(p, r): out.append((p, r, "rind")); n += 1
    # craters on top
    n = 0
    for _ in range(800):
        if n >= 9: break
        r = rng.uniform(2.5, 5)
        rad = rng.uniform(15, R - r - 4); t = rng.uniform(-np.pi, np.pi)
        p = np.array([rad * np.cos(t), rad * np.sin(t), HEIGHT + rng.uniform(-0.2, 0.3) * r])
        # off the seam, and on the wedge not where the finger dimple goes
        da = abs(abs(t) - HALF)
        seam = rad * np.sin(da) if da < np.pi / 2 else rad
        if seam < r + 3: continue
        if abs(t) < HALF and np.hypot(p[0] - (R - 24), p[1]) < DIMPLE_R + r + 4: continue
        if free(p, r): out.append((p, r, "top")); n += 1
    return out

def cutter(p, r, kind):
    return (mf.Manifold.sphere(r, 48) if kind == "top" else teardrop(r)).translate(p.tolist())

def build_wheel_and_wedge(holes):
    tall = mf.CrossSection.circle(R, 256).extrude(HEIGHT)
    notch = sector(R + 2).extrude(HEIGHT).translate([0, 0, TILE_TOP])
    bay = sector(R - LIP).extrude(TILE_TOP).translate([0, 0, BASE])
    wheel = tall - notch - bay

    wedge2d = sector(R + 2).offset(-WEDGE_CLEAR, mf.JoinType.Miter) ^ mf.CrossSection.circle(R, 256)
    wedge = wedge2d.extrude(WEDGE_H).translate([0, 0, TILE_TOP])

    for p, r, kind in holes:
        c = cutter(p, r, kind)
        wheel = wheel - c
        wedge = wedge - c
    dimple = mf.Manifold.sphere(DIMPLE_R, 64).translate([R - 24, 0, HEIGHT + 5])
    wedge = wedge - dimple
    return wheel, wedge

def qr_matrix(url):
    q = qrcode.QRCode(error_correction=ECC, border=0)
    q.add_data(url); q.make(fit=True)
    return np.array(q.get_matrix(), bool)

def build_tile(url):
    M = qr_matrix(url); n = M.shape[0]
    side, x_front = qr_square()
    m = min(MAX_MODULE, side / (n + 2 * QUIET))
    if m < MIN_MODULE:
        sys.exit(f"the link needs a {n}x{n} code: {m:.2f} mm modules, too fine to print. Use a shorter link or a bigger wheel.")
    code = n * m
    # The code reads upright for someone at the rim looking in (where the wedge
    # comes out): page-down is +x (toward the rim), page-right is +y.
    cx = x_front + side / 2
    x0, y0 = cx - code / 2, -code / 2
    rects = []
    for i in range(n):
        j = 0
        while j < n:
            if M[i, j]:
                k = j
                while k < n and M[i, k]: k += 1
                xa, xb = x0 + i * m, x0 + (i + 1) * m
                ya, yb = y0 + j * m, y0 + k * m
                rects.append([(xa, ya), (xb, ya), (xb, yb), (xa, yb)])
                j = k
            else:
                j += 1
    ink = mf.CrossSection(rects, mf.FillRule.NonZero).offset(0.02, mf.JoinType.Miter)   # corner-touching modules overlap
    text_h = 0
    if THANKS:
        t = text_2d(THANKS, 7.5)
        if t is not None:
            # text x -> +y, text y -> -x: upright for the same viewer, in front of the code
            gap = 3.0
            b = t.bounds(); w, h = b[2] - b[0], b[3] - b[1]
            tx = x_front + QUIET * m - gap - h / 2
            t = t.transform([[0, -1, tx], [1, 0, 0]])
            width_there = 2 * ((tx - h / 2) * np.tan(HALF) - TILE_CLEAR - 1.5)
            if w > width_there:
                s = width_there / w                     # shrink about its centre to fit
                t = t.translate([-tx, 0]).scale([s, s]).translate([tx, 0])
            ink = ink + t
            text_h = h
    plate = tile_outline().extrude(TILE_T)
    ink3 = ink.extrude(QR_HEIGHT).translate([0, 0, TILE_T])
    print(f"tile: {n}x{n} code at {m:.2f} mm modules = {code:.1f} mm square"
          f"{', with ' + THANKS if text_h else ''}; colour change at z = {TILE_T:.2f} mm")
    return plate, ink3

# ---- output ----------------------------------------------------------------
def export(parts, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for name, m in parts:
        path = os.path.join(out_dir, name + ".stl")
        to_trimesh(m).export(path)
        assert trimesh.load(path).is_watertight, name + " is not watertight once written as STL"
        print(f"  {name}.stl  {to_trimesh(m).volume / 1000:.0f} cm3")

def build(url, out_dir, with_wheel):
    os.makedirs(out_dir, exist_ok=True)
    parts = []
    if with_wheel:
        wheel, wedge = build_wheel_and_wedge(bubbles())
        # each part sits on z = 0 as printed
        parts += [("wheel", wheel), ("wedge", wedge.translate([0, 0, -TILE_TOP]))]
    plate, ink = build_tile(url)
    parts += [("tile_plate", plate), ("tile_qr", ink), ("tile", plate + ink)]
    export(parts, out_dir)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else SAMPLE_URL
    sample = url == SAMPLE_URL
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "stl" if sample else "private")
    print(f"wheel {WHEEL_D} x {HEIGHT} mm, wedge {ANGLE} deg")
    build(url, out, with_wheel=sample)
