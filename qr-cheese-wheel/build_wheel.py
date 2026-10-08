#!/usr/bin/env python3
"""
A Swiss-cheese wheel with a wedge you slide out to find a QR code hidden
underneath, for handing over a digital gift card (or any link).

    python3 build_wheel.py                                 sample in stl/ (placeholder link)
    python3 build_wheel.py "https://your-link" [out_dir]   your build, in private/ (git-ignored) by default

Three parts:

    wheel.stl     the wheel with a quarter-wedge notch.  The notch has a floor
                  2.4 mm thick; on it sits the tile, and a low lip at the rim
                  stops the tile sliding out with the wedge.
    wedge.stl     a quarter of the wheel that sits on the tile, flush with the
                  wheel's top and rind.  A finger dimple on top lets you slide
                  it out toward you.
    tile_*.stl    a thin plate in the notch floor: the QR code and ありがとう
                  in a dark colour on cheese yellow.

The wheel is as small as the code allows.  The code is turned 45 degrees so it
sits square in the notch's right-angled corner (a diamond, seen from the rim),
which is the tightest fit of a square in a wedge; the wheel's radius is then
the code's diagonal plus its light border, the lip and clearances.  The lip is
yellow too, so it counts toward that border.

Module size, error correction and relief height come from scan_test.py: 1.2 mm
modules at ECC M, standing 0.48 mm proud, decoded in about 94% of simulated
single camera frames across tilts up to 35 degrees, wall shadows and print
spread.  Below 1.2 mm reliability drops off quickly; above it the wheel grows
for little gain.

If the link is a gift card the tile *is* the money: real builds go to
private/ and never into git.  The sample is built for a 41 x 41 code (any link
up to 106 characters), so the committed wheel and wedge suit most links; a
shorter link makes a smaller code and, built privately, a smaller wheel.
"""
import os, sys
import numpy as np, qrcode, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- parameters (mm) -------------------------------------------------------
SAMPLE_URL = "https://www.olympiaprovisions.com/"
SAMPLE_VERSION = 6    # 41 x 41: what a ~90-character gift-card link needs
ECC = qrcode.constants.ERROR_CORRECT_M          # the minimum; raised to Q or H when that doesn't grow the code
MODULE = 1.2          # see scan_test.py
QUIET = 2             # light border on the tile, in modules; the lip and the rest of the floor add to it
QR_HEIGHT = 0.48      # three 0.16 mm layers: dark enough to hide the yellow, low enough not to fatten at an angle

HEIGHT = 32
ANGLE = 90            # the wedge; the code's diamond fit needs exactly 90
BASE = 2.4            # notch floor under the tile
TILE_T = 1.6          # tile plate
LIP = 2.5             # wall at the rim that holds the tile in
WEDGE_CLEAR = 0.3     # gap between the wedge and the notch walls
TILE_CLEAR = 0.25     # gap around the tile in its bay
EDGE = 0.5            # extra margin from the tile edge to the code's border
DIMPLE_R = 10         # finger dimple on the wedge
# Magnets hold the wedge in: one pair across each notch wall, a pocket in the
# wall facing a pocket in the wedge's side.  Glued in after printing.
MAGNET_D = 6.0        # 6 x 3 mm neodymium discs
MAGNET_H = 3.0
MAGNET_FIT = 0.15     # extra on the pocket radius; PLA holes print a little small
MAGNET_SINK = 0.2     # magnet face below the surface, so a glue bead can't stand proud
MAGNET_AT = 0.55      # along each wall, as a fraction of the radius
SEED = 11
THANKS = "ありがとう"   # on the tile beside the code; "" to omit
TEXT_H = 6.0          # letter height, shrunk if it doesn't fit
THANKS_FONT = ["/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
               "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
               "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
               "C:/Windows/Fonts/msgothic.ttc"]

HALF = np.radians(ANGLE / 2)
TILE_TOP = BASE + TILE_T + QR_HEIGHT          # the wedge rests here, on the code and the lip
WEDGE_H = HEIGHT - TILE_TOP
# the notch's two walls run along these directions from the centre; (u, v) are
# distances along them, and (u, v) -> (x, y) is a rotation, so nothing is mirrored
E_U = np.array([np.cos(-HALF), np.sin(-HALF)])
E_V = np.array([np.cos(HALF), np.sin(HALF)])

# ---- helpers ---------------------------------------------------------------
def to_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)

def sector(radius, n=128):
    a = np.radians(np.linspace(-ANGLE / 2, ANGLE / 2, n))
    return mf.CrossSection([[(0.0, 0.0)] + [(radius * np.cos(t), radius * np.sin(t)) for t in a]])

def uv(u, v):
    return u * E_U + v * E_V

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

ECC_NAMES = {qrcode.constants.ERROR_CORRECT_L: "L", qrcode.constants.ERROR_CORRECT_M: "M",
             qrcode.constants.ERROR_CORRECT_Q: "Q", qrcode.constants.ERROR_CORRECT_H: "H"}

def qr_code(url, version=None, ecc=ECC):
    """The smallest code for url at error correction ECC or better; then the
    strongest correction that still fits that size, which is free."""
    q = qrcode.QRCode(version=version, error_correction=ecc, border=0)
    q.add_data(url); q.make(fit=version is None)
    best = (q, ecc)
    for stronger in (qrcode.constants.ERROR_CORRECT_Q, qrcode.constants.ERROR_CORRECT_H):
        if list(ECC_NAMES).index(stronger) <= list(ECC_NAMES).index(ecc):
            continue
        t = qrcode.QRCode(version=q.version, error_correction=stronger, border=0)
        t.add_data(url)
        try:
            t.make(fit=False)
            best = (t, stronger)
        except qrcode.exceptions.DataOverflowError:
            break
    return np.array(best[0].get_matrix(), bool), ECC_NAMES[best[1]]

def qr_matrix(url, version=None):
    return qr_code(url, version)[0]

# ---- layout ----------------------------------------------------------------
def layout(n):
    """Everything sized from the code: n modules a side."""
    inset = TILE_CLEAR + EDGE + QUIET * MODULE          # wall to the first dark module
    far = inset + n * MODULE                            # wall to the last
    corner = far * np.sqrt(2)                           # centre to the code's far corner
    # the tile must hold the code with EDGE to spare; the border beyond the
    # corner may run onto the lip, but must stay on the wheel
    r_tile_edge = corner + EDGE                         # tile radius needed (to the tile's edge)
    R = max(r_tile_edge + TILE_CLEAR + LIP, corner + QUIET * MODULE * np.sqrt(2) + 0.5)
    R = np.ceil(R * 2) / 2
    return dict(n=n, inset=inset, far=far, R=R, tile_r=R - LIP - TILE_CLEAR)

# ---- parts -----------------------------------------------------------------
def magnet_spots(R):
    """(centre on the wall plane, along-wall unit vector, unit normal into the wheel) for each wall."""
    spots = []
    for sgn in (1, -1):
        along = np.array([np.cos(HALF), sgn * np.sin(HALF), 0])
        into_wheel = np.array([-np.sin(HALF), sgn * np.cos(HALF), 0])
        c = along * R * MAGNET_AT; c[2] = TILE_TOP + WEDGE_H / 2
        spots.append((c, along, into_wheel))
    return spots

def magnet_pocket(c, along, normal, start):
    """A teardrop-section hole for one magnet: round where the magnet sits, with
    a 45-degree peak on top so it prints in a vertical wall without support.
    It starts `start` mm along `normal` from the wall plane, opens 0.2 mm short
    of that (so it cuts cleanly through the face) and runs MAGNET_SINK +
    MAGNET_H deep."""
    r = MAGNET_D / 2 + MAGNET_FIT
    tip = mf.CrossSection([[(-0.01, r * np.sqrt(2)), (0.01, r * np.sqrt(2)), (0, r * np.sqrt(2) + 0.01)]])
    section = mf.CrossSection.batch_hull([mf.CrossSection.circle(r, 64), tip])
    depth = 0.2 + MAGNET_SINK + MAGNET_H
    p = section.extrude(depth)                  # local x: along the wall, local y: up, local z: into the part
    o = c + normal * (start - 0.2)
    return p.transform([[along[0], 0, normal[0], o[0]],
                        [along[1], 0, normal[1], o[1]],
                        [0,        1, 0,         o[2]]])

def bubbles(R):
    """Holes: (centre, radius, kind).  'cut' bubbles sit on the two notch
    walls and are shared by wheel and wedge; 'rind' and 'top' are outside."""
    rng = np.random.default_rng(SEED)
    out = []
    keep_clear = [(c, MAGNET_D) for c, _, _ in magnet_spots(R)]     # leave room round the magnets

    def free(p, r):
        return (all(np.linalg.norm(p - q) > r + rq + 3 for q, rq, _ in out) and
                all(np.linalg.norm(p - q) > r + rq + 2 for q, rq in keep_clear))

    for sgn in (1, -1):
        along = np.array([np.cos(HALF), sgn * np.sin(HALF), 0])
        n = 0
        for _ in range(500):
            if n >= 3: break
            r = rng.uniform(3, 6.5)
            d = rng.uniform(16, R - 10)
            z = rng.uniform(TILE_TOP + r + 2, HEIGHT - r * 1.5 - 2)
            # centred in the 0.3 mm gap, not on either face, which would leave slivers
            p = along * d + np.array([np.sin(HALF), -sgn * np.cos(HALF), 0]) * WEDGE_CLEAR / 2; p[2] = z
            if free(p, r): out.append((p, r, "cut")); n += 1
    n = 0
    for _ in range(800):
        if n >= 13: break
        r = rng.uniform(2.8, 6)
        t = rng.uniform(-np.pi, np.pi)
        if abs(abs(t) - HALF) * R < r + 2: continue                 # not across the seam
        lo = TILE_TOP + r + 2 if abs(t) < HALF else r + 2           # wedge: clear of its bottom edge
        if lo > HEIGHT - r * 1.5 - 2: continue
        z = rng.uniform(lo, HEIGHT - r * 1.5 - 2)
        rr = R + rng.uniform(-0.4, 0.4) * r
        p = np.array([rr * np.cos(t), rr * np.sin(t), z])
        if free(p, r): out.append((p, r, "rind")); n += 1
    n = 0
    for _ in range(800):
        if n >= 7: break
        r = rng.uniform(2.5, 4.5)
        rad = rng.uniform(12, R - r - 4); t = rng.uniform(-np.pi, np.pi)
        p = np.array([rad * np.cos(t), rad * np.sin(t), HEIGHT + rng.uniform(-0.2, 0.3) * r])
        da = abs(abs(t) - HALF)
        if (rad * np.sin(da) if da < np.pi / 2 else rad) < r + 3: continue
        if abs(t) < HALF and np.hypot(p[0] - (R - 20), p[1]) < DIMPLE_R + r + 4: continue
        if free(p, r): out.append((p, r, "top")); n += 1
    return out

def cutter(p, r, kind):
    return (mf.Manifold.sphere(r, 48) if kind == "top" else teardrop(r)).translate(p.tolist())

def build_wheel_and_wedge(R):
    tall = mf.CrossSection.circle(R, 256).extrude(HEIGHT)
    notch = sector(R + 2).extrude(HEIGHT).translate([0, 0, TILE_TOP])
    bay = sector(R - LIP).extrude(TILE_TOP).translate([0, 0, BASE])
    wheel = tall - notch - bay

    wedge2d = sector(R + 2).offset(-WEDGE_CLEAR, mf.JoinType.Miter) ^ mf.CrossSection.circle(R, 256)
    wedge = wedge2d.extrude(WEDGE_H).translate([0, 0, TILE_TOP])

    for p, r, kind in bubbles(R):
        c = cutter(p, r, kind)
        wheel = wheel - c
        wedge = wedge - c
    wedge = wedge - mf.Manifold.sphere(DIMPLE_R, 64).translate([R - 20, 0, HEIGHT + 4.5])
    for c, along, into_wheel in magnet_spots(R):
        wheel = wheel - magnet_pocket(c, along, into_wheel, 0)
        # the wedge's face is WEDGE_CLEAR in from the wall plane
        wedge = wedge - magnet_pocket(c, along, -into_wheel, WEDGE_CLEAR)
    return wheel, wedge

def build_tile(M, L):
    n, m = M.shape[0], MODULE
    a = L["inset"]
    rects = []
    for i in range(n):
        j = 0
        while j < n:
            if M[i, j]:
                k = j
                while k < n and M[i, k]: k += 1
                # in (u, v), columns along u and rows along -v: the code as seen from above, unmirrored
                u0, u1 = a + j * m, a + k * m
                v0, v1 = a + (n - 1 - i) * m, a + (n - i) * m
                rects.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
                j = k
            else:
                j += 1
    # union and grow in the axis-aligned (u, v) frame, where corner-touching
    # modules meet exactly, then turn the outline into place: (u, v) -> (x, y)
    # is a rotation by -ANGLE/2
    ink = (mf.CrossSection(rects, mf.FillRule.NonZero).offset(0.03, mf.JoinType.Miter)
           .rotate(-ANGLE / 2))

    placed = ""
    if THANKS:
        # In the strip beyond the code along one wall (large u): letters run
        # along v with their tops toward the code, like a caption under it.
        t = text_2d(THANKS, TEXT_H)
        if t is not None:
            b = t.bounds(); w, h = b[2] - b[0], b[3] - b[1]
            u_lo = L["far"] + QUIET * m                     # keep the code's border clear
            for scale in np.linspace(1, 0.6, 9):
                hh, ww = h * scale, w * scale
                u_hi = u_lo + hh
                v_max = np.sqrt(max(L["tile_r"] - EDGE, 0) ** 2 - u_hi ** 2) if u_hi < L["tile_r"] else 0
                v_lo = TILE_CLEAR + EDGE + 1
                if v_max - v_lo >= ww:
                    uc, vc = u_lo + hh / 2, v_lo + (v_max - v_lo) / 2
                    # text x -> +v, text y -> -u (a rotation), then into x, y
                    Mt = np.column_stack([E_V, -E_U])
                    c = uv(uc, vc)
                    t2 = t.scale([scale, scale]).transform([[Mt[0, 0], Mt[0, 1], c[0]], [Mt[1, 0], Mt[1, 1], c[1]]])
                    ink = ink + t2
                    placed = f", {THANKS} at {hh:.1f} mm"
                    break
            else:
                print(f"  {THANKS} doesn't fit beside this code; leaving it off")
    plate = sector(L["R"] - LIP).offset(-TILE_CLEAR, mf.JoinType.Miter).extrude(TILE_T)
    ink3 = ink.extrude(QR_HEIGHT).translate([0, 0, TILE_T])
    print(f"tile: {n}x{n} code at {m:.2f} mm = {n * m:.1f} mm square, set diagonally{placed}; "
          f"colour change at z = {TILE_T:.2f} mm")
    return plate, ink3

# ---- output ----------------------------------------------------------------
def export(parts, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for name, m in parts:
        path = os.path.join(out_dir, name + ".stl")
        t = to_trimesh(m)
        t.export(path)
        assert trimesh.load(path).is_watertight, name + " is not watertight once written as STL"
        print(f"  {name}.stl  {t.volume / 1000:.0f} cm3")

def build(url, out_dir, version=None):
    M, level = qr_code(url, version)
    L = layout(M.shape[0])
    print(f"code: {M.shape[0]}x{M.shape[0]}, error correction {level}")
    print(f"wheel {2 * L['R']:.0f} mm across, {HEIGHT} mm tall; quarter wedge")
    wheel, wedge = build_wheel_and_wedge(L["R"])
    plate, ink = build_tile(M, L)
    export([("wheel", wheel), ("wedge", wedge.translate([0, 0, -TILE_TOP])),     # each part sits on z = 0
            ("tile_plate", plate), ("tile_qr", ink), ("tile", plate + ink)], out_dir)
    with open(os.path.join(out_dir, "layout.txt"), "w") as f:                  # read by render.py
        f.write(f"{L['R']}\n")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else SAMPLE_URL
    sample = url == SAMPLE_URL
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "stl" if sample else "private")
    build(url, out, SAMPLE_VERSION if sample else None)
