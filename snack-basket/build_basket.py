#!/usr/bin/env python3
"""
A little brown wicker basket with a handle, and the things that go in
it: two apples, a chocolate-chip cookie, a bag of snacks and a thank-you card.  Each part prints on
its own, all but the card in one colour, and none needs supports.

    basket      brown.  A woven basket with a twisted rim, 84 mm across at
                its widest (the samosa is 86 mm), with a socket inside the
                rim on each side for the handle
    handle      brown.  An arch with wrapped grooves.  It prints flat and its
                two pegs push into the sockets
    apple       red (print two).  Stands on a flat spot on its bottom, with a
                short stem in a dimple on top
    cookie      tan.  Domed, slightly uneven, with chocolate chips on top
    snack_bag   any bright colour.  A puffy bag with crimped, zigzag-cut
                seals and SNACKS on the front.  It prints lying on its back
    card        white with 感謝 in black (AMS).  A flat thank-you card; the
                characters are inlaid flush in its top two layers

The script places the treats (both apples) and the card in the basket the way they're shown in
the pictures and stops with an error if any of them pokes through the basket
or the handle, or into each other.

    python3 build_basket.py     -> stl/basket.stl, handle.stl, apple.stl, cookie.stl,
                                   snack_bag.stl, card.stl, card_ink.stl,
                                   and assembled.stl (for viewing)
"""
import math, os
import numpy as np, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- basket
BOT_A, BOT_B = 37.5, 30.5   # outside half-length and half-width at the bottom (75 x 61 mm)
TOP_A, TOP_B = 40.5, 33.5   # ... at the top of the wall (81 x 67 mm); the rim adds 1.2 mm all round
SQUARE = 4.0                # shape of the outline: 2 is an oval, higher is more like a rounded rectangle
WALL_H = 30.0               # height of the woven wall to the middle of the rim
WALL = 2.2                  # wall thickness
FLOOR = 2.4
FILLET = 2.5                # inside, where the wall meets the floor
FOOT_CHAMFER = 0.6          # stops elephant's foot

STAKES = 36                 # upright stakes the weave goes over and under (keep it even)
ROWS = 8                    # woven rows up the wall
WEAVE = 0.7                 # mm; how far each strand stands out
INNER_WEAVE = 0.35          # mm; the weave shows faintly inside too
WEAVE_FROM = 2.0            # plain band at the bottom, mm
RIM_DEPTH = 4.0             # the rim bead takes up the top of the wall
RIM_OUT = 1.2               # how far the rim sticks out past the wall
RIM_TWISTS = 60             # twists of the rope round the rim
RIM_TWIST = 0.35            # mm

# ---------------------------------------------------------------- handle
HANDLE_W = 5.0              # width of the band
HANDLE_T = 4.0              # thickness (it prints flat, so this is its height on the bed)
HANDLE_RISE = 36.0          # height of the arch above the rim
HANDLE_AT = 26.5            # the pegs sit this far either side of the middle
PEG_W, PEG_L = 3.6, 10.0    # the pegs on the ends of the handle
FIT = 0.2                   # gap all round the pegs in their sockets
GROOVE_PITCH = 3.2          # the wrapped grooves along the handle

# ---------------------------------------------------------------- apple
APPLE_R = 13.0              # radius (about 25 mm across at the shoulders)
APPLE_SHOULDER = 0.06       # how much fuller the top is than the bottom
APPLE_CUT = -44.0           # degrees; the flat spot it stands on, where the side is at 45 degrees
APPLE_DIMPLE = 3.0          # mm; the dip round the stem
STEM_L, STEM_R = 4.5, 1.1

# ---------------------------------------------------------------- cookie
COOKIE_R = 14.0             # 28 mm across
COOKIE_H = 5.0              # thickness in the middle (4 mm at the edge)
CHIPS = 11
SEED = 3

# ---------------------------------------------------------------- snack bag
BAG_W, BAG_L = 30.0, 42.0   # flat size, including the seals
BAG_PUFF = 9.0              # how far the front puffs up from the flat back
SEAL = 4.0                  # the crimped seals at each end
SEAL_T = 1.6                # their thickness
LABEL = "SNACKS"

# ---------------------------------------------------------------- thank-you card
CARD_W, CARD_H = 26.0, 42.0 # a portrait card: the characters run top to bottom
CARD_T = 1.2                # thickness (six layers at 0.2 mm)
CARD_CORNER = 1.0           # corner rounding
INK = 0.4                   # the characters are inlaid this deep, flush with the face (two layers)
CARD_TEXT = "感謝"          # "gratitude": 感 above 謝
CHAR_SIZE = 17.0            # height of each character
CARD_LEAN = 12.0            # degrees; it leans back against the basket wall
CARD_AT = (-19.0, 18.5)     # where the bottom edge of the card stands, middle of its front face
# a font with Japanese characters; the first one found is used
CJK_FONTS = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",               # Linux: fonts-ipafont-gothic
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",              # Linux: fonts-noto-cjk
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",                   # macOS
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "C:/Windows/Fonts/YuGothB.ttc",                                     # Windows
    "C:/Windows/Fonts/msgothic.ttc",
]

MAX_OVERHANG = 45.0         # degrees from vertical
N = 432                     # points round the basket


# ================================================================ mesh helpers
def loft(rings):
    """Close a stack of rings (each an (n, 3) array, or a single point (3,))
    into a solid."""
    verts, idx = [], []
    for r in rings:
        r = np.asarray(r, float)
        if r.ndim == 1:
            idx.append([len(verts)]); verts.append(r)
        else:
            idx.append(list(range(len(verts), len(verts) + len(r)))); verts.extend(r)
    faces = []
    for A, B in zip(idx[:-1], idx[1:]):
        if len(A) == 1:
            n = len(B); faces += [(A[0], B[(j + 1) % n], B[j]) for j in range(n)]
        elif len(B) == 1:
            n = len(A); faces += [(A[j], A[(j + 1) % n], B[0]) for j in range(n)]
        else:
            n = len(A)
            for j in range(n):
                k = (j + 1) % n
                faces += [(A[j], A[k], B[k]), (A[j], B[k], B[j])]
    m = trimesh.Trimesh(np.array(verts), np.array(faces), process=True)
    if m.volume < 0:
        m.invert()
    return m


def to_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


def to_manifold(t):
    return mf.Manifold(mf.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))


def overhang(m, above):
    fn, cz = m.face_normals, m.triangles_center[:, 2]
    sel = (cz > above) & (fn[:, 2] < 0)
    return float(np.degrees(np.arcsin(-fn[sel, 2].min()))) if sel.any() else 0.0


def check(name, t, above=FOOT_CHAMFER + 0.2):
    assert t.is_watertight and t.is_winding_consistent and t.volume > 0, f"the {name} isn't a closed solid"
    oh = overhang(t, above)
    assert oh <= MAX_OVERHANG + 0.5, f"the {name} overhangs {oh:.0f} deg; it would need support"
    return oh


# ================================================================ basket
def superellipse(theta, a, b):
    c, s = np.abs(np.cos(theta)), np.abs(np.sin(theta))
    return (np.power(c / a, SQUARE) + np.power(s / b, SQUARE)) ** (-1 / SQUARE)


def even_angles(n):
    """angles round the outline, evenly spaced by distance rather than angle,
    so the stakes are evenly spaced; and u, the fraction of the way round"""
    th = np.linspace(0, 2 * math.pi, 20001)
    r = superellipse(th, TOP_A, TOP_B)
    p = np.c_[r * np.cos(th), r * np.sin(th)]
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    u = np.arange(n) / n
    return np.interp(u * s[-1], s, th), u


def wall_r(theta, z):
    t = z / WALL_H
    return superellipse(theta, BOT_A + (TOP_A - BOT_A) * t, BOT_B + (TOP_B - BOT_B) * t)


def inner_r(theta, z):
    return wall_r(theta, z) - WALL


def weave(u, z):
    """how far the woven strands stand out at (u round, z up)"""
    top = WALL_H - RIM_DEPTH
    h = (top - WEAVE_FROM) / ROWS
    f = (z - WEAVE_FROM) / h
    row = np.floor(f)
    inside = (z > WEAVE_FROM) & (z < top)
    strand = np.sin(math.pi * (f - row))                        # each row is a round strand
    over = 0.5 + 0.5 * np.cos(2 * math.pi * STAKES * u + math.pi * row)   # over a stake, then under the next
    return np.where(inside, WEAVE * strand * (0.2 + 0.8 * over), 0.0)


def basket_shell():
    th, u = even_angles(N)
    c, s = np.cos(th), np.sin(th)
    ring = lambda r, z: np.c_[r * c, r * s, np.broadcast_to(z, r.shape)]
    rings = [np.array([0, 0, 0.0])]
    rings.append(ring(wall_r(th, 0) - FOOT_CHAMFER, 0.0))
    top = WALL_H - RIM_DEPTH
    for z in np.r_[FOOT_CHAMFER, np.linspace(WEAVE_FROM, top, ROWS * 12 + 1)]:
        rings.append(ring(wall_r(th, z) + weave(u, z), z))
    # the rim: a rope bead, stepping out under 40 degrees then rounding over to the inside
    rb = (RIM_OUT + WALL) / 2                                    # bead radius
    zc = WALL_H - rb + 0.2
    a0 = math.radians(-40)
    z_start = zc + rb * math.sin(a0)
    out0 = RIM_OUT - rb + rb * math.cos(a0)          # offset from the wall at the bead start
    for z in np.linspace(top, z_start, 6)[1:-1]:
        rings.append(ring(wall_r(th, z) + out0 * (z - top) / (z_start - top), z))
    for a in np.linspace(a0, math.pi, 48):
        e = math.sin(math.pi * (a - a0) / (math.pi - a0)) ** 2
        d = RIM_TWIST * e * np.cos(2 * math.pi * RIM_TWISTS * u - 2 * a)
        z = zc + rb * math.sin(a)
        r = wall_r(th, z) + RIM_OUT - rb + (rb + d) * math.cos(a)
        rings.append(np.c_[r * c, r * s, z + d * math.sin(a)])
    # down the inside, round the fillet and across the floor
    for z in np.linspace(zc, FLOOR + FILLET, 60)[1:]:
        rings.append(ring(inner_r(th, z) - INNER_WEAVE / WEAVE * weave(u + 0.5 / STAKES, z), z))
    for a in np.linspace(0, math.pi / 2, 10)[1:]:
        z = FLOOR + FILLET * (1 - math.sin(a))
        rings.append(ring(inner_r(th, FLOOR + FILLET) - FILLET * (1 - math.cos(a)), z))
    for f in np.linspace(1, 0, 12)[1:-1]:
        rings.append(ring((inner_r(th, FLOOR + FILLET) - FILLET) * f, FLOOR))
    rings.append(np.array([0, 0, FLOOR]))
    return loft(rings)


def socket_post(sign):
    """a thick stake inside the rim on each long side, with a socket for the handle's peg"""
    yi = HANDLE_AT - PEG_W / 2 - FIT - 2.0                       # the post's inside face
    top = WALL_H - 0.5
    def slab(z):
        yo = float(inner_r(math.pi / 2, z)) + 1.0                # its back is buried in the wall
        pts = [(-5, yo), (-5, yi + 1.5), (-3.5, yi), (3.5, yi), (5, yi + 1.5), (5, yo)]
        return mf.Manifold.extrude(mf.CrossSection([pts]), 0.01).translate((0, 0, z))
    post = mf.Manifold.batch_hull([slab(FLOOR - 0.5), slab(top - 0.01)])
    hole = mf.Manifold.cube((HANDLE_T + 2 * FIT, PEG_W + 2 * FIT, PEG_L + 1.0 + 5), center=False)
    hole = hole.translate((-(HANDLE_T + 2 * FIT) / 2, HANDLE_AT - (PEG_W + 2 * FIT) / 2, top - PEG_L - 1.0))
    post = post - hole
    return post if sign > 0 else post.mirror((0, 1, 0))


def basket():
    shell = to_manifold(basket_shell())
    for sgn in (1, -1):
        shell = shell + socket_post(sgn)
    return to_trimesh(shell)


# ================================================================ handle
def handle():
    """built flat: x across the basket, y up; extruded HANDLE_T in z"""
    shoulder = WALL_H - 0.5
    z0 = shoulder + 3.0
    t = np.linspace(0, math.pi, 160)
    def arch(ra, rz):
        return [(ra * math.cos(a), z0 + rz * math.sin(a)) for a in t]
    hw = HANDLE_W / 2
    outer = [(HANDLE_AT + hw, shoulder)] + arch(HANDLE_AT + hw, HANDLE_RISE + hw) + [(-HANDLE_AT - hw, shoulder)]
    inner = [(-HANDLE_AT + hw, shoulder)] + arch(HANDLE_AT - hw, HANDLE_RISE - hw)[::-1] + [(HANDLE_AT - hw, shoulder)]
    band = mf.CrossSection([outer + inner])
    pw, ch = PEG_W / 2, 0.6
    for sgn in (1, -1):
        x = sgn * HANDLE_AT
        peg = [(x - pw, shoulder + 0.5), (x - pw, shoulder - PEG_L + ch), (x - pw + ch, shoulder - PEG_L),
               (x + pw - ch, shoulder - PEG_L), (x + pw, shoulder - PEG_L + ch), (x + pw, shoulder + 0.5)]
        band = band + mf.CrossSection([peg])
    m = mf.Manifold.extrude(band, HANDLE_T)
    # wrapped grooves across the top face, slanted along the band
    L = math.pi * HANDLE_AT * 1.15 + 2 * 3.0
    cuts = []
    for s in np.arange(GROOVE_PITCH / 2, L, GROOVE_PITCH):
        # walk along the centre line: up the leg, round the arch, down the other leg
        if s < 3.0:
            p, tang = (HANDLE_AT, shoulder + s), (0, 1)
        elif s > L - 3.0:
            p, tang = (-HANDLE_AT, shoulder + (L - s)), (0, -1)
        else:
            a = math.pi * (s - 3.0) / (L - 6.0)
            p = (HANDLE_AT * math.cos(a), z0 + HANDLE_RISE * math.sin(a))
            tang = (-HANDLE_AT * math.sin(a), HANDLE_RISE * math.cos(a))
        if p[1] < shoulder + 1.5:
            continue
        ang = math.degrees(math.atan2(tang[1], tang[0])) + 90 + 25   # across the band, slanted 25 degrees
        top = mf.Manifold.cube((HANDLE_W + 4, 0.6, 0.8), center=True).translate((0, 0, HANDLE_T))
        cuts.append(top.rotate((0, 0, ang)).translate((p[0], p[1], 0)))
    m = m - mf.Manifold.batch_boolean(cuts, mf.OpType.Add)
    return to_trimesh(m)


def handle_in_basket(h):
    """turn the flat-printed handle up into the basket's sockets"""
    h = h.copy()
    h.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0)))   # y -> z
    h.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (0, 0, 1)))   # x -> y
    h.apply_translation((-(h.bounds[0][0] + h.bounds[1][0]) / 2, 0, 0))
    return h


# ================================================================ apple
def apple():
    # the outline in (radius, height), going round from the flat bottom to the top: a ball
    # that's fuller at the shoulders and narrower at the bottom
    phi = np.linspace(math.radians(APPLE_CUT), math.pi / 2, 160)
    rho = APPLE_R * (1 + APPLE_SHOULDER * np.sin(phi) - 0.04 * np.cos(2 * phi))
    rs, zs = rho * np.cos(phi), rho * np.sin(phi)
    rs[-1] = 0
    # resample by length along the outline, then sink the dimple the stem grows out of
    seg = np.r_[0, np.cumsum(np.hypot(np.diff(rs), np.diff(zs)))]
    t = np.linspace(0, seg[-1], 140)
    rs, zs = np.interp(t, seg, rs), np.interp(t, seg, zs)
    zs = zs - APPLE_DIMPLE * np.exp(-(rs / (0.38 * APPLE_R)) ** 2)
    zs -= zs[0]
    H = zs.max()
    n = 160
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    rings = [np.array([0, 0, 0.0])]
    for r, z in zip(rs[:-1], zs[:-1]):
        low = max(0.0, 1 - z / (0.6 * H))                        # five soft lobes round the bottom
        lump = 1 + 0.035 * low * np.cos(5 * th) + 0.02 * np.sin(2 * th + 0.7) * math.sin(math.pi * z / H)
        rings.append(np.c_[r * lump * np.cos(th), r * lump * np.sin(th), np.full(n, z)])
    rings.append(np.array([0, 0, zs[-1]]))
    body = to_manifold(loft(rings))
    # the stem: short, thin and slightly curved, rising out of the dimple
    base = np.array([0, 0, zs[-1] - 1.0])
    srings = []
    for f in np.linspace(0, 1, 16):
        cen = base + np.array([1.2 * f * f, 0, (STEM_L + 1.0) * f])
        r = STEM_R * (1 - 0.25 * f)
        srings.append(np.c_[cen[0] + r * np.cos(th[::8]), cen[1] + r * np.sin(th[::8]), np.full(n // 8, cen[2])])
    srings = [srings[0].mean(0)] + srings + [srings[-1].mean(0) + (0, 0, 0.3)]
    return to_trimesh(body + to_manifold(loft(srings)))


# ================================================================ cookie
def cookie():
    rng = np.random.default_rng(SEED)
    n, nr = 240, 60
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    edge = COOKIE_R * (1 + 0.03 * np.sin(3 * th + 1) + 0.02 * np.sin(5 * th + 2) + 0.012 * np.sin(11 * th))
    chips = []
    while len(chips) < CHIPS:
        p = rng.uniform(-COOKIE_R, COOKIE_R, 2) * 0.8
        if np.hypot(*p) < COOKIE_R * 0.78 and all(np.hypot(*(p - q[:2])) > 3.6 for q in chips):
            chips.append(np.r_[p, rng.uniform(0.8, 1.3), rng.uniform(1.1, 1.6)])
    e_h = COOKIE_H - 1.0                                          # thickness at the edge
    rr = 1.4                                                       # rounding of the top edge
    def top_z(x, y, rho):
        z = e_h + (COOKIE_H - e_h) * (1 - rho ** 2)
        z += 0.12 * np.sin(1.3 * x + 0.8 * y) * np.sin(0.9 * y - 1.1 * x)    # a little rough
        for cx, cy, hgt, sig in chips:
            d2 = ((x - cx) ** 2 + (y - cy) ** 2) / sig ** 2
            z += hgt * np.exp(-d2 ** 1.6)                          # flat-topped chips
        return z
    c, s = np.cos(th), np.sin(th)
    rings = [np.array([0, 0, 0.0]), np.c_[(edge - 0.5) * c, (edge - 0.5) * s, np.zeros(n)],
             np.c_[edge * c, edge * s, np.full(n, 0.5)]]
    for a in np.linspace(0, math.pi / 2, 8):
        R = edge - rr + rr * math.cos(a)
        rings.append(np.c_[R * c, R * s, np.full(n, e_h - rr + rr * math.sin(a))])
    for f in np.linspace(1, 0, nr)[1:-1]:
        R = (edge - rr) * f
        x, y = R * c, R * s
        rho = f * (edge - rr) / COOKIE_R
        rings.append(np.c_[x, y, top_z(x, y, rho)])
    rings.append(np.array([0, 0, float(top_z(0.0, 0.0, 0.0))]))
    return loft(rings)


# ================================================================ snack bag
def bag_height(x, y, ye):
    """top surface of the bag lying on its flat back"""
    yb = BAG_L / 2 - SEAL
    tx = np.clip(np.abs(x) / (BAG_W / 2), 0, 1)
    ty = np.clip(np.abs(y) / yb, 0, 1)
    body = SEAL_T + (BAG_PUFF - SEAL_T) * (1 - tx ** 4) ** 0.6 * (1 - ty ** 2.5) ** 0.7
    # soft pleats where the bag pinches into the seals
    pleat = 0.35 * np.sin(2 * math.pi * x / 4.2 + 0.6 * np.sign(y)) * np.clip((ty - 0.55) / 0.45, 0, 1) ** 1.5 \
        * (1 - tx ** 2) * (ty < 1)
    seal = SEAL_T + 0.25 * np.abs(np.sin(math.pi * x / 0.9))       # crimp ridges
    return np.where(np.abs(y) <= yb, body + pleat, seal)


def bag_surface(offset=0.0, nu=181, nv=141):
    u = np.linspace(-1, 1, nu)
    v = np.linspace(-1, 1, nv)
    x = u * BAG_W / 2
    tri = np.abs(((x / 1.2) % 2) - 1)                              # zigzag-cut ends
    ye = BAG_L / 2 - 0.7 * tri
    X = np.repeat(x[:, None], nv, 1)
    # keep the seal band evenly spaced: v from -1..1 maps the seal and the body separately
    yb = BAG_L / 2 - SEAL
    Y = np.where(np.abs(v) <= 0.8, v / 0.8 * yb,
                 np.sign(v) * (yb + (np.abs(v) - 0.8) / 0.2 * (ye[:, None] - yb)))
    Z = bag_height(X, Y, ye[:, None]) + offset
    top = np.stack([X, Y, Z], -1)
    bot = np.stack([X, Y, np.zeros_like(Z)], -1)
    vid = lambda i, j, k: (k * nu + i) * nv + j
    verts = np.r_[top.reshape(-1, 3), bot.reshape(-1, 3)]
    faces = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            a, b, c, d = vid(i, j, 0), vid(i + 1, j, 0), vid(i + 1, j + 1, 0), vid(i, j + 1, 0)
            faces += [(a, b, c), (a, c, d)]
            a, b, c, d = vid(i, j, 1), vid(i + 1, j, 1), vid(i + 1, j + 1, 1), vid(i, j + 1, 1)
            faces += [(a, c, b), (a, d, c)]
    border = [(i, 0) for i in range(nu - 1)] + [(nu - 1, j) for j in range(nv - 1)] + \
             [(i, nv - 1) for i in range(nu - 1, 0, -1)] + [(0, j) for j in range(nv - 1, 0, -1)]
    for (i, j), (i2, j2) in zip(border, border[1:] + border[:1]):
        a, b = vid(i, j, 0), vid(i2, j2, 0)
        c, d = vid(i2, j2, 1), vid(i, j, 1)
        faces += [(a, d, c), (a, c, b)]
    m = trimesh.Trimesh(verts, np.array(faces), process=True)
    if m.volume < 0:
        m.invert()
    return m


def text_outline(text, height):
    """letter outlines as a CrossSection, centred on the origin"""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), text, size=height, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    polys = [p for p in tp.to_polygons(closed_only=True) if len(p) > 2]
    cs = mf.CrossSection([np.asarray(p) for p in polys], mf.FillRule.EvenOdd)
    (x0, y0), (x1, y1) = cs.bounds()[:2], cs.bounds()[2:]
    return cs.translate((-(x0 + x1) / 2, -(y0 + y1) / 2))


def snack_bag():
    m = to_manifold(bag_surface())
    # a raised oval label panel with the word on it, both following the puffed front
    panel = mf.CrossSection.circle(1.0, 96).scale((BAG_W * 0.36, 7.0))
    word = text_outline(LABEL, 5.5)
    w = word.bounds()
    word = word.scale((min(1.0, BAG_W * 0.62 / (w[2] - w[0])), 1.0))
    raised = lambda off: to_manifold(bag_surface(off, 121, 101))
    m = m + (mf.Manifold.extrude(panel, 30) ^ raised(0.4))
    m = m + (mf.Manifold.extrude(word, 30) ^ raised(1.2))
    return to_trimesh(m)


# ================================================================ thank-you card
def cjk_font():
    for f in CJK_FONTS:
        if os.path.exists(f):
            return f
    raise SystemExit("no Japanese font found for the card: install one (e.g. fonts-ipafont-gothic) "
                     "or add its path to CJK_FONTS")


def glyph(ch, size):
    """one character's outline as a CrossSection, scaled to `size` tall and centred on the origin"""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), ch, size=100, prop=FontProperties(fname=cjk_font()))
    polys = [np.asarray(p) for p in tp.to_polygons(closed_only=True) if len(p) > 2]
    cs = mf.CrossSection(polys, mf.FillRule.EvenOdd)
    x0, y0, x1, y1 = cs.bounds()
    k = size / max(x1 - x0, y1 - y0)
    return cs.translate((-(x0 + x1) / 2, -(y0 + y1) / 2)).scale((k, k))


def card():
    """the card lying face up: a white body and the black characters inlaid in its face.
    Returns (body, ink), both in the same coordinates."""
    r = CARD_CORNER
    outline = mf.CrossSection.square((CARD_W - 2 * r, CARD_H - 2 * r), center=True).offset(r, mf.JoinType.Round)
    text = mf.CrossSection()
    gap = (CARD_H - len(CARD_TEXT) * CHAR_SIZE) / (len(CARD_TEXT) + 1)
    for i, ch in enumerate(CARD_TEXT):                           # top to bottom
        y = CARD_H / 2 - gap * (i + 1) - CHAR_SIZE * (i + 0.5)
        text = text + glyph(ch, CHAR_SIZE).translate((0, y))
    # strokes and gaps thinner than the nozzle wouldn't print; check none get lost
    thin = text.area() - text.offset(-0.2).offset(0.2).area()
    assert thin < 0.02 * text.area(), "the characters have strokes too thin to print; make CHAR_SIZE bigger"
    plate = mf.Manifold.extrude(outline, CARD_T)
    ink = mf.Manifold.extrude(text, INK + 0.01).translate((0, 0, CARD_T - INK))
    ink = ink ^ plate                                            # flush with the face
    body = plate - ink
    return to_trimesh(body), to_trimesh(ink)


def card_in_basket(body, ink):
    """stand the card on its bottom edge, face to the front, leaning back on the wall"""
    out = []
    for t in (body, ink):
        t = t.copy()
        t.apply_translation((0, CARD_H / 2, -CARD_T))            # bottom edge, front face at the origin
        t.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90 - CARD_LEAN), (1, 0, 0)))
        out.append(t)
    lo = np.concatenate([t.vertices for t in out]).min(0)
    for t in out:
        t.apply_translation((CARD_AT[0], CARD_AT[1], FLOOR + 0.05 - lo[2]))
    return out


# ================================================================ in the basket
def place(t, rot_y=0.0, rot_z=0.0, rot_x=0.0, at=(0, 0, 0)):
    t = t.copy()
    for ang, axis in ((rot_x, (1, 0, 0)), (rot_y, (0, 1, 0)), (rot_z, (0, 0, 1))):
        if ang:
            t.apply_transform(trimesh.transformations.rotation_matrix(math.radians(ang), axis))
    t.apply_translation(np.asarray(at, float) - [0, 0, t.bounds[0][2]])
    return t


APPLE2_AT = (-14.0, -9.0)
APPLE2_TURN = 80


def arrange(apple_m, cookie_m, bag_m):
    floor = FLOOR + 0.05
    # the bag stands on its bottom seal, front facing the middle, leaning on the left end wall
    b = bag_m.copy()
    b.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0)))    # length up
    b.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (0, 0, 1)))    # front -> +x
    b = place(b, rot_y=-9, at=(0, 0, floor))
    lo = b.vertices[b.vertices[:, 2] < floor + 0.5][:, 0].min()
    b.apply_translation((-33.0 - lo, 0, 0))
    p = place(apple_m, rot_z=200, at=(0, 0, floor))
    p.apply_translation((19.0 - p.centroid[0], -13.5 - p.centroid[1], 0))
    # the cookie leans against the right end wall
    c = place(cookie_m, rot_y=-28, at=(0, 0, floor))
    c.apply_translation((20.5 - c.centroid[0], 13.5 - c.centroid[1], 0))
    # a second apple, turned the other way, between the bag and the handle
    p2 = place(apple_m, rot_z=APPLE2_TURN, at=(0, 0, floor))
    p2.apply_translation((APPLE2_AT[0] - p2.centroid[0], APPLE2_AT[1] - p2.centroid[1], 0))
    return {"apple": p, "apple_2": p2, "cookie": c, "snack_bag": b}


def check_fit(items, bskt, hndl):
    """every item inside the basket's walls and clear of each other and the handle"""
    for name, t in items.items():
        v = t.vertices
        assert v[:, 2].min() >= FLOOR - 1e-6, f"the {name} goes through the floor"
        low = v[v[:, 2] < WALL_H - 1.0]
        th = np.arctan2(low[:, 1], low[:, 0])
        room = inner_r(th, np.maximum(low[:, 2], FLOOR + FILLET)) - 0.3
        out = np.hypot(low[:, 0], low[:, 1]) - room
        assert out.max() <= 0, f"the {name} pokes through the basket wall by {out.max():.1f} mm"
    solids = {"basket": to_manifold(bskt), "handle": to_manifold(hndl)}
    solids.update({k: to_manifold(v) for k, v in items.items()})
    names = list(solids)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            clash = (solids[a] ^ solids[b]).volume()
            assert clash < 1e-3, f"the {a} and the {b} overlap ({clash:.2f} mm3)"


# ================================================================ build
def build():
    parts = {}
    parts["basket"] = basket()
    parts["handle"] = handle()
    parts["apple"] = apple()
    parts["cookie"] = cookie()
    parts["snack_bag"] = snack_bag()
    report = {}
    for name, t in parts.items():
        t.apply_translation((0, 0, -t.bounds[0][2]))
        report[name] = check(name, t, 0.8 if name != "basket" else FOOT_CHAMFER + 0.2)
    # the card's two parts stay together: the ink sits in the top of the body
    parts["card"], parts["card_ink"] = card()
    report["card"] = check("card", parts["card"])
    assert parts["card_ink"].is_watertight, "the card's characters aren't a closed solid"
    report["card_ink"] = 0.0
    lo, hi = parts["basket"].bounds
    assert max(hi - lo) <= 86.0, "the basket is wider than the samosa"
    h_in = handle_in_basket(parts["handle"])
    items = arrange(parts["apple"], parts["cookie"], parts["snack_bag"])
    card_body, card_ink = card_in_basket(parts["card"], parts["card_ink"])
    whole_card = to_trimesh(to_manifold(card_body) + to_manifold(card_ink))
    check_fit(dict(items, card=whole_card), parts["basket"], h_in)
    items["card"], items["card_ink"] = card_body, card_ink
    scene = trimesh.util.concatenate([parts["basket"], h_in] + list(items.values()))
    return parts, scene, report, items, h_in


def main():
    parts, scene, report, _, _ = build()
    out = os.path.join(HERE, "stl")
    os.makedirs(out, exist_ok=True)
    for name, t in parts.items():
        t.export(os.path.join(out, name + ".stl"))
        lo, hi = t.bounds
        print(f"{name}: {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, {t.volume/1000:.1f} cm3, "
              f"worst overhang {report[name]:.0f} deg, {len(t.faces)} triangles")
    scene.export(os.path.join(out, "assembled.stl"))
    lo, hi = scene.bounds
    print(f"assembled: {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm")


if __name__ == "__main__":
    main()
