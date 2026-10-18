#!/usr/bin/env python3
"""
Paka's basket: a countertop basket for cat supplies, woven in an open
hexagonal cane pattern, with a hexagonal plaque on the front carrying a paw
print and the name "Paka".

    python3 build_basket.py        -> stl/basket.stl (and stl/treat_bag.stl, a stand-in for the renders)

The wall is three sets of round-ish reeds, one horizontal and two at 60
degrees, laid out like a cane chair seat (a kagome weave: hexagons with a
small triangle at each corner). Every reed goes over, then under, the reeds
it crosses, and neighbours overlap by 0.8 mm where they cross, so the
whole wall fuses into one solid when printed.

Printing: one piece, one colour, no supports. The 60-degree reeds hold
themselves up; the horizontal reeds have flat bottoms and bridge the short
gaps between crossings; the rim flares out at 45 degrees; the plaque's flat
bottom edge sits on a horizontal reed and its raised face is bevelled at 45
degrees. The script checks the solid is closed and that nothing downward-
facing is steeper than 45 degrees apart from the flat bridges and the
lettering (1.2 mm raised).

Needs: numpy, trimesh, manifold3d, matplotlib (for the lettering), shapely.
"""
import math, os, sys
import numpy as np, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))

# ================================================================ parameters (mm)
W, D, R = 200.0, 140.0, 28.0      # wall centre line: outside width, depth, corner radius
NAME = "Paka"
FONT = ("Inter", "black")         # matplotlib family and weight for the name

CELL = 15.6                       # distance between parallel reeds (hexagons are about 11 mm across inside)
REED_W, REED_T = 4.0, 2.0         # reed width in the wall, and thickness through it
WEAVE_AMP = 0.6                   # each reed goes this far in/out from the wall centre at a crossing
Z_SHIFT = 4.2                     # moves the lattice up so a horizontal reed runs through the plaque's middle

BASE_H = 11.0                     # solid band round the bottom
BASE_IN, BASE_OUT = 2.0, 2.0      # how far it reaches inside and outside the wall centre line
FOOT_CHAMFER = 0.5                # elephant's-foot relief on the outside bottom edge
FLOOR_T = 1.2                     # floor thickness (6 layers at 0.2 mm)

RIM_FLARE = 3.4                   # rim half-width (it flares out and in at 45 degrees)
RIM_COLLAR = 3.4                  # straight bit of band between the top reed and the flare

PLAQUE_ROWS = 4                   # plaque height in reed rows (4 x 15.6 = 62.5 mm)
PLAQUE_W = 122.0                  # plaque width, corner to corner
PLAQUE_PROUD = 1.4                # raised face stands this far out from the reeds
RELIEF = 1.2                      # paw, name and border stand out this much from the plaque face

MAX_OVERHANG = 45.0               # degrees from vertical

# ================================================================ derived
A_HALF, B_HALF = W / 2, D / 2
SEG = [A_HALF - R, math.pi * R / 2, 2 * (B_HALF - R), math.pi * R / 2,
       2 * (A_HALF - R), math.pi * R / 2, 2 * (B_HALF - R), math.pi * R / 2, A_HALF - R]
L = sum(SEG)                                      # length round the wall centre line
N_DIAG = round(math.sqrt(3) * L / (2 * CELL))     # reeds in each diagonal set
S = math.sqrt(3) * L / (2 * N_DIAG)               # actual spacing, so the pattern closes round the basket
K3 = 2 / math.sqrt(3)
PHASE = 1 / 6                                     # the three sets' offsets sum to 1/2, so no three reeds meet at a point
WALL_HALF = WEAVE_AMP + REED_T / 2                # the weave's depth either side of the centre line


def h_rows():
    """heights of the horizontal reeds"""
    return [S * (n + PHASE) + Z_SHIFT for n in range(-2, 12)]


ROWS = [z for z in h_rows() if BASE_H < z]
TOP_ROW = [z for z in ROWS if z > 95][0]          # the rim sits on this one
ROWS = [z for z in ROWS if z <= TOP_ROW]
Z_LO, Z_HI = BASE_H - 1.0, TOP_ROW + 0.5          # crossings inside this range are woven
Z_DIAG = (BASE_H - 3.0, TOP_ROW + RIM_COLLAR - 0.5)   # diagonal reeds run from inside the base to inside the rim
RIM_Z0 = TOP_ROW
RIM_TOP = RIM_Z0 + RIM_COLLAR + RIM_FLARE - WALL_HALF + 0.8 + RIM_FLARE
PLAQUE_Z0 = [z for z in ROWS if z > 15][0]
PLAQUE_Z1 = PLAQUE_Z0 + PLAQUE_ROWS * S
PLAQUE_ZC = (PLAQUE_Z0 + PLAQUE_Z1) / 2


# ================================================================ the wall's centre line
def perim(s):
    """point and outward normal at distance s round the wall (s = 0 is the front centre, going towards +x)"""
    s = np.mod(np.asarray(s, float), L)
    x, y, nx, ny = (np.zeros_like(s) for _ in range(4))
    a, b = A_HALF - R, B_HALF - R
    pieces = [("line", (0, -B_HALF), (1, 0)), ("arc", (a, -b), -math.pi / 2),
              ("line", (A_HALF, -b), (0, 1)), ("arc", (a, b), 0.0),
              ("line", (a, B_HALF), (-1, 0)), ("arc", (-a, b), math.pi / 2),
              ("line", (-A_HALF, b), (0, -1)), ("arc", (-a, -b), math.pi),
              ("line", (-a, -B_HALF), (1, 0))]
    start = 0.0
    for seg_len, (kind, p, q) in zip(SEG, pieces):
        m = (s >= start) & (s < start + seg_len + 1e-9)
        t = s[m] - start
        if kind == "line":
            x[m] = p[0] + q[0] * t; y[m] = p[1] + q[1] * t
            nx[m], ny[m] = q[1], -q[0]
        else:
            ang = q + t / R
            x[m] = p[0] + R * np.cos(ang); y[m] = p[1] + R * np.sin(ang)
            nx[m], ny[m] = np.cos(ang), np.sin(ang)
        start += seg_len
    return x, y, nx, ny


def outline(d, n=720):
    """the wall outline offset by d (outwards positive), as a CrossSection"""
    x, y, nx, ny = perim(np.linspace(0, L, n, endpoint=False))
    return mf.CrossSection([np.stack([x + nx * d, y + ny * d], 1)])


# ================================================================ mesh helpers
def to_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)


def to_manifold(t):
    return mf.Manifold(mf.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))


def sweep(u, z, d, section, closed=False):
    """Sweep a 2D section along a path on the wall. The path is given in wall
    coordinates (u round the wall, z up, d out). The section's points are
    (across, through): 'across' lies in the wall at right angles to the path,
    positive towards +z (or +u for a vertical path); 'through' points out of the wall."""
    x, y, nx, ny = perim(u)
    P = np.stack([x + nx * d, y + ny * d, z], 1)
    T = (np.roll(P, -1, 0) - np.roll(P, 1, 0)) if closed else np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True)
    Nr = np.stack([nx, ny, np.zeros_like(nx)], 1)
    Nr -= (Nr * T).sum(1, keepdims=True) * T
    Nr /= np.linalg.norm(Nr, axis=1, keepdims=True)
    B = np.cross(Nr, T)                        # in the wall, across the path; +z for a path going +u
    sec = np.asarray(section, float)
    V = P[:, None, :] + B[:, None, :] * sec[None, :, 0, None] + Nr[:, None, :] * sec[None, :, 1, None]
    n, k = V.shape[:2]
    verts = V.reshape(-1, 3)
    faces = []
    for i in (range(n) if closed else range(n - 1)):
        j = (i + 1) % n
        for a in range(k):
            b = (a + 1) % k
            faces += [(i * k + a, j * k + a, j * k + b), (i * k + a, j * k + b, i * k + b)]
    if not closed:
        c0, c1 = len(verts), len(verts) + 1
        verts = np.vstack([verts, P[0], P[-1]])
        for a in range(k):
            b = (a + 1) % k
            faces += [(c0, a, b), (c1, (n - 1) * k + b, (n - 1) * k + a)]
    t = trimesh.Trimesh(verts, np.array(faces), process=True)
    if t.volume < 0:
        t.invert()
    return t


def ellipse(w, t, n=12):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([w / 2 * np.cos(a), t / 2 * np.sin(a)], 1)


def flat_bottom_reed(w, t, n=12):
    """a horizontal reed: square-edged underneath, so it bridges flat, and rounded on top"""
    out = [(-w / 2, -t / 2), (0.0, -t / 2)]
    for a in np.linspace(-np.pi / 2, np.pi / 2, n + 1)[1:-1]:
        out.append((w / 2 * math.cos(a), t / 2 * math.sin(a)))
    return out + [(0.0, t / 2), (-w / 2, t / 2)]


def ease(t, t_cross, sign, amp, period=None):
    """depth along a reed: +amp or -amp at each crossing, eased between them"""
    tc = np.asarray(t_cross, float); sg = np.asarray(sign, float)
    if period:                                     # a closed loop: repeat the crossings either side
        tc = np.concatenate([tc - period, tc, tc + period]); sg = np.tile(sg, 3)
    else:
        step = np.diff(tc).mean()
        tc = np.concatenate([[tc[0] - step], tc, [tc[-1] + step]]); sg = np.concatenate([[-sg[0]], sg, [-sg[-1]]])
    i = np.clip(np.searchsorted(tc, t) - 1, 0, len(tc) - 2)
    f = np.clip((t - tc[i]) / (tc[i + 1] - tc[i]), 0, 1)
    e = (1 - np.cos(np.pi * f)) / 2
    return amp * (sg[i] * (1 - e) + sg[i + 1] * e)


# ================================================================ the weave
def reeds():
    """the three sets of reeds as (kind, value, slope): horizontal z = value, or diagonal u = value + slope * z"""
    out = [("h", z, 0.0) for z in ROWS]
    for n in range(N_DIAG):
        c = K3 * S * (n + PHASE)
        out.append(("d", c - K3 / 2 * Z_SHIFT, K3 / 2))      # leaning right (60 degrees)
        out.append(("d", -c + K3 / 2 * Z_SHIFT, -K3 / 2))    # leaning left
    return out


def crossings(rs):
    """for each reed, its crossings in order along it (parameter: u for horizontal reeds, z for diagonal ones)"""
    cross = [[] for _ in rs]
    for i, (ki, ci, mi) in enumerate(rs):
        for j in range(i + 1, len(rs)):
            kj, cj, mj = rs[j]
            if ki == "h" and kj == "h":
                continue
            if ki == "d" and kj == "d":
                if mi == mj:
                    continue
                for k in range(-3, 4):
                    z = (cj - ci + k * L) / (mi - mj)
                    if Z_LO < z < Z_HI:
                        cross[i].append((z, j)); cross[j].append((z, i))
            else:
                (hz, hi), (dc, dm, di) = ((ci, i), (cj, mj, j)) if ki == "h" else ((cj, j), (ci, mi, i))
                if Z_LO < hz < Z_HI:
                    cross[hi].append((float(np.mod(dc + dm * hz, L)), di)); cross[di].append((hz, hi))
    return [sorted(c) for c in cross]


def over_under(rs, cross):
    """Choose each reed's starting side so that at every crossing one reed is
    over and the other under, with each reed alternating along its length."""
    n = len(rs); parent = list(range(n)); par = [0] * n

    def find(x):
        if parent[x] == x:
            return x, 0
        r, p = find(parent[x]); parent[x] = r; par[x] ^= p
        return r, par[x]
    index = [{o: k for k, (_, o) in enumerate(c)} for c in cross]
    for i in range(n):
        for k, (_, j) in enumerate(cross[i]):
            if j < i:
                continue
            need = 1 ^ (k & 1) ^ (index[j][i] & 1)
            (ri, pi), (rj, pj) = find(i), find(j)
            if ri == rj:
                assert pi ^ pj == need, "the reeds can't all go over-and-under"
            else:
                parent[ri] = rj; par[ri] = pi ^ pj ^ need
    for i, (k, _, _) in enumerate(rs):
        assert k != "h" or len(cross[i]) % 2 == 0, "a horizontal reed has an odd number of crossings"
    return [find(i)[1] for i in range(n)]


def weave():
    rs = reeds()
    cross = crossings(rs)
    parity = over_under(rs, cross)
    out = []
    for (kind, c, m), cr, p in zip(rs, cross, parity):
        tc = [t for t, _ in cr]
        sign = [(-1) ** (k + p) for k in range(len(cr))]
        if kind == "h":
            u = np.linspace(0, L, 1100, endpoint=False)
            d = ease(u, tc, sign, WEAVE_AMP, period=L)
            out.append(sweep(u, np.full_like(u, c), d, flat_bottom_reed(REED_W, REED_T), closed=True))
        else:
            z = np.linspace(*Z_DIAG, 120)
            d = ease(z, tc, sign, WEAVE_AMP)
            out.append(sweep(c + m * z, z, d, ellipse(REED_W, REED_T)))
    return out


# ================================================================ base, floor and rim
def ring(profile, n=1400):
    """sweep a (d, z) profile round the wall"""
    u = np.linspace(0, L, n, endpoint=False)
    x, y, nx, ny = perim(u)
    pr = np.asarray(profile, float)
    V = np.stack([x[:, None] + nx[:, None] * pr[None, :, 0],
                  y[:, None] + ny[:, None] * pr[None, :, 0],
                  np.broadcast_to(pr[None, :, 1], (n, len(pr)))], 2)
    k = len(pr); faces = []
    for i in range(n):
        j = (i + 1) % n
        for a in range(k):
            b = (a + 1) % k
            faces += [(i * k + a, j * k + a, j * k + b), (i * k + a, j * k + b, i * k + b)]
    t = trimesh.Trimesh(V.reshape(-1, 3), np.array(faces), process=True)
    if t.volume < 0:
        t.invert()
    return t


def base():
    c = FOOT_CHAMFER; top = BASE_H
    prof = [(-BASE_IN, 0), (BASE_OUT - c, 0), (BASE_OUT, c), (BASE_OUT, top - (BASE_OUT - WALL_HALF)),
            (WALL_HALF, top), (-WALL_HALF, top), (-BASE_IN, top - (BASE_IN - WALL_HALF))]
    return ring(prof)


def floor():
    return mf.Manifold.extrude(outline(-BASE_IN + 0.6), FLOOR_T)


def rim():
    z0, z1 = RIM_Z0, RIM_Z0 + RIM_COLLAR
    z2 = z1 + RIM_FLARE - WALL_HALF                          # 45-degree flare out and in
    z3 = z2 + 0.8
    prof = [(-WALL_HALF, z0), (WALL_HALF, z0), (WALL_HALF, z1), (RIM_FLARE, z2), (RIM_FLARE, z3)]
    for a in np.linspace(0, np.pi, 17)[1:-1]:                # rounded top
        prof.append((RIM_FLARE * math.cos(a), z3 + RIM_FLARE * math.sin(a)))
    prof += [(-RIM_FLARE, z3), (-RIM_FLARE, z2), (-WALL_HALF, z1)]
    return ring(prof)


# ================================================================ the plaque
def hex_cs(width, z0, z1, inset=0.0):
    """a flat-topped hexagon whose slanted sides run at 60 degrees, like the reeds, shrunk by inset all round"""
    zc = (z0 + z1) / 2
    t60 = math.tan(math.radians(60))
    hw = width / 2 - inset / math.sin(math.radians(60))       # corner moves in along the bisector
    zb, zt = z0 + inset, z1 - inset
    top = hw - (zt - zb) / 2 / t60
    return mf.CrossSection([np.array([(-top, zb), (top, zb), (hw, zc), (top, zt), (-top, zt), (-hw, zc)])])


def paw_cs():
    def ell(cx, cy, rx, ry, rot=0.0):
        return mf.CrossSection.circle(1.0, 72).scale((rx, ry)).rotate(rot).translate((cx, cy))
    pad = ell(0, -2, 11.5, 9.0) + ell(-6.5, -5.5, 7.0, 6.0) + ell(6.5, -5.5, 7.0, 6.0) + ell(0, 1.5, 8.5, 6.5)
    toes = (ell(-13.0, 7.5, 4.3, 5.4, 25) + ell(-5.0, 13.5, 4.5, 5.8, 8)
            + ell(5.0, 13.5, 4.5, 5.8, -8) + ell(13.0, 7.5, 4.3, 5.4, -25))
    return pad + toes


def text_cs(text, height):
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), text, size=height, prop=FontProperties(family=FONT[0], weight=FONT[1]))
    polys = [p for p in tp.to_polygons(closed_only=True) if len(p) > 2]
    cs = mf.CrossSection([np.asarray(p) for p in polys], mf.FillRule.EvenOdd)
    b = cs.bounds()
    return cs.translate((-(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2))


def on_front(cs, d0, d1):
    """extrude a section drawn in (x, z) on the front wall, from depth d0 out to d1"""
    return mf.Manifold.extrude(cs, d1 - d0).rotate((90, 0, 0)).translate((0, -B_HALF - d0, 0))


def plaque():
    face = WALL_HALF + PLAQUE_PROUD
    # solid through the wall, so the woven reeds behind it all join it
    panel = on_front(hex_cs(PLAQUE_W, PLAQUE_Z0, PLAQUE_Z1), -WALL_HALF, WALL_HALF)
    # the raised face, bevelled at 45 degrees all round
    outer = np.array(hex_cs(PLAQUE_W, PLAQUE_Z0, PLAQUE_Z1).to_polygons()[0])
    inner = np.array(hex_cs(PLAQUE_W, PLAQUE_Z0, PLAQUE_Z1, inset=PLAQUE_PROUD).to_polygons()[0])
    pts = [(x, -B_HALF - WALL_HALF + 0.01, z) for x, z in outer] + [(x, -B_HALF - face, z) for x, z in inner]
    bevel = to_manifold(trimesh.convex.convex_hull(np.array(pts)))
    # border, paw and name
    edge = hex_cs(PLAQUE_W, PLAQUE_Z0, PLAQUE_Z1, inset=PLAQUE_PROUD + 2.0)
    border = edge - hex_cs(PLAQUE_W, PLAQUE_Z0, PLAQUE_Z1, inset=PLAQUE_PROUD + 4.6)
    paw = paw_cs().scale((0.8, 0.8)).translate((0, PLAQUE_ZC + 7.5))
    word = text_cs(NAME, 13.5).translate((0, PLAQUE_ZC - 14.5))
    room = hex_cs(PLAQUE_W, PLAQUE_Z0, PLAQUE_Z1, inset=PLAQUE_PROUD + 5.6)
    assert (paw + word - room).area() < 1e-6, "the paw or the name runs into the plaque's border"
    relief = on_front(border + paw + word, face - 0.01, face + RELIEF)
    return panel + bevel + relief


# ================================================================ a bag of treats, for the pictures
def treat_bag(w=125.0, h=175.0, t=45.0):
    """a stand-up pouch of treats, roughly the size of a 3 oz bag"""
    body = mf.Manifold.batch_boolean(
        [mf.Manifold.sphere(5, 24).translate((sx * (w / 2 - 5), sy * (t / 2 - 5), sz))
         for sx in (-1, 1) for sy in (-1, 1) for sz in (5, h - 25)], mf.OpType.Add).hull()
    seal = mf.Manifold.cube((w, 3.0, 20.0), True).translate((0, 0, h - 10))
    return to_trimesh(body + seal)


# ================================================================ checks
def overhangs(t, plaque_relief_y):
    """Worst downward-facing slope, leaving out the flat bridges (faces pointing
    straight down), the first layer, and the lettering's 1.2 mm relief."""
    fn, c = t.face_normals, t.triangles_center
    down = fn[:, 2] < -1e-6
    flat = fn[:, 2] < -0.9995
    relief = c[:, 1] < plaque_relief_y
    sel = down & ~flat & ~relief & (c[:, 2] > FOOT_CHAMFER + 0.2)
    if not sel.any():
        return 0.0, None
    worst = np.argmin(np.where(sel, fn[:, 2], 0))
    return float(np.degrees(np.arcsin(-fn[worst, 2]))), c[worst]


def bridges():
    """longest flat span along a horizontal reed between the diagonal reeds holding it up"""
    run = K3 * S / 2                                   # spacing of crossings along a horizontal reed
    diag_w = REED_W / math.sin(math.radians(60))       # a diagonal reed's width, measured along the horizontal
    return run - diag_w


def build():
    parts = weave() + [base(), rim()]
    solid = mf.Manifold.batch_boolean([to_manifold(p) for p in parts] + [floor(), plaque()], mf.OpType.Add)
    t = to_trimesh(solid)
    assert t.is_watertight and t.is_winding_consistent and t.volume > 0, "the basket isn't a closed solid"
    assert len(t.split(only_watertight=False)) == 1, "the basket isn't all one piece"
    oh, where = overhangs(t, -B_HALF - WALL_HALF - PLAQUE_PROUD + 0.05)
    assert oh <= MAX_OVERHANG + 0.5, f"overhang of {oh:.1f} deg at {where}; it would need support"
    lo, hi = t.bounds
    assert max(hi[:2] - lo[:2]) <= 250 and hi[2] - lo[2] <= 250, "too big for the A1"
    return t, oh


def main():
    t, oh = build()
    out = os.path.join(HERE, "stl")
    os.makedirs(out, exist_ok=True)
    t.export(os.path.join(out, "basket.stl"))
    treat_bag().export(os.path.join(out, "treat_bag.stl"))
    lo, hi = t.bounds
    print(f"basket: {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, {t.volume/1000:.1f} cm3 "
          f"(about {t.volume/1000*1.24:.0f} g of PLA if solid), {len(t.faces)} triangles")
    print(f"weave: {N_DIAG} reeds in each diagonal set, {len(ROWS)} horizontal reeds, spacing {S:.2f} mm")
    print(f"inside: {W - 2*BASE_IN:.0f} x {D - 2*BASE_IN:.0f} mm at the floor, {RIM_Z0 - FLOOR_T:.0f} mm deep to the rim")
    print(f"worst overhang {oh:.0f} deg (bridges and lettering aside); longest bridge {bridges():.1f} mm")


if __name__ == "__main__":
    main()
