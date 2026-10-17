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
    brownie     brown and black (AMS).  A cut square with a cracked crust, fudge
                in the cracks and chocolate chunks in the top and the sides
    pretzel     brown, black and white (AMS).  A knotted pretzel, half dipped in
                chocolate with a white drizzle, and coarse salt on the other half
    cheese      yellow and black (AMS).  A wedge of aged gouda in black wax,
                with a few small holes in the cut faces
    card        white with 感謝 in black (AMS).  A flat thank-you card; the
                characters are inlaid flush in its top two layers

The script places the treats (both apples) and the card in the basket the way they're shown in
the pictures (the brownie, the pretzel and the cheese are extras: each is checked to fit in the basket on its own) and stops with an error if any of them pokes through the basket
or the handle, or into each other.

    python3 build_basket.py     -> stl/basket.stl, handle.stl, apple.stl, cookie.stl,
                                   snack_bag.stl, card.stl, card_ink.stl, brownie.stl, brownie_choc.stl,
                                   pretzel.stl, pretzel_choc.stl, pretzel_white.stl, cheese.stl, cheese_wax.stl,
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

# ---------------------------------------------------------------- brownie
BROWNIE_W = 22.0            # a square cut from the pan
BROWNIE_H = 12.0            # height to the top of the crust
BROWNIE_CORNER = 0.8        # knife-cut corners, barely rounded
CRUST_CELLS = 11            # plates of the crackly crust
CRACK_W = (0.5, 0.9)        # mm; how wide the cracks are (they show the dark fudge)
CRACK_DEEP = 0.5            # mm; how far the cracks sink into the crust
FUDGE = 1.0                 # mm; how deep the black fudge goes under the cracks
PUFF = 0.35                 # mm; each crust plate puffs up in the middle
TOP_CHUNKS = 5              # chocolate chunks melting out of the top
SIDE_CHUNKS = 10            # chunks showing in the cut sides (each adds colour changes on its layers)
CRUMB = 0.22                # mm; the crumbly texture of the cut sides
BROWNIE_SEED = 5

# ---------------------------------------------------------------- chocolate-dipped pretzel
PRETZEL_W = 32.0            # across the two lobes
STRAND = 4.6                # strand width at its fattest (the ends taper)
STRAND_H = 3.4              # strand height; it's flat underneath so it prints lying down
COATING = 0.45              # how thick the chocolate is
DIP_AT = -0.12              # where the dip line crosses, as a fraction of the width below the middle
DRIZZLE_W = 0.6             # the white drizzle lines
SALT = 16                   # salt crystals on the undipped half
PRETZEL_SEED = 2

# ---------------------------------------------------------------- cheese wedge
WHEEL_R = 40.0              # the wheel the wedge was cut from
WHEEL_H = 16.0
WEDGE_ANGLE = 42.0          # degrees
WHEEL_BULGE = 1.6           # mm; the wheel's sides bulge out a little
WAX = 0.8                   # the black wax on the rind, top and bottom
EYES = 7                    # small holes in the cut faces
CHEESE_SEED = 4

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


# ================================================================ brownie
def crust_cracks(rng):
    """the crack network on top: Voronoi cells, each edge a crack of its own width.
    Returns a function giving E(x, y), the distance into the nearest plate (negative in a
    crack), and the cracks as a CrossSection."""
    half = BROWNIE_W / 2
    seeds = rng.uniform(-half, half, (CRUST_CELLS, 2))
    for _ in range(30):                                          # spread them out a little
        d = seeds[:, None] - seeds[None]
        r2 = (d ** 2).sum(-1) + np.eye(len(seeds)) * 1e9
        push = (d / r2[..., None] ** 1.5).sum(1)
        seeds = np.clip(seeds + 6.0 * push, -half * 0.9, half * 0.9)
    # mirror the seeds over each edge so the cracks run out to the sides
    pts = [seeds] + [seeds * m + o for m, o in (((-1, 1), (-2 * half, 0)), ((-1, 1), (2 * half, 0)),
                                                  ((1, -1), (0, -2 * half)), ((1, -1), (0, 2 * half)))]
    allp = np.concatenate(pts)
    n = len(allp)
    width = rng.uniform(*CRACK_W, (n, n)); width = (width + width.T) / 2
    own = np.arange(n) % len(seeds)
    width[own[:, None] == own[None]] = -10.0                     # a seed and its own mirror image: that's the side, not a crack
    def E(x, y):
        p = np.stack([x, y], -1)[..., None, :]
        d2 = ((p - allp) ** 2).sum(-1)
        i = np.argsort(d2, -1)
        a, b = np.take_along_axis(d2, i[..., :1], -1)[..., 0], np.take_along_axis(d2, i[..., 1:2], -1)[..., 0]
        sep = np.linalg.norm(allp[i[..., 0]] - allp[i[..., 1]], axis=-1)
        edge = (b - a) / (2 * sep)                               # distance to the edge between the two nearest
        w = width[i[..., 0], i[..., 1]]
        # a crack wanders a little, the way a real one does
        wob = 0.12 * np.sin(2.3 * x + 1.7 * y) + 0.08 * np.sin(4.1 * y - 3.3 * x)
        return edge + wob - w / 2
    import contourpy
    g = np.linspace(-half - 1, half + 1, 700)
    X, Y = np.meshgrid(g, g)
    pts_list, offs_list = contourpy.contour_generator(g, g, E(X, Y), fill_type="OuterOffset").filled(-10.0, 0.0)
    polys = []
    for pts, offs in zip(pts_list, offs_list):
        polys += [pts[a:b] for a, b in zip(offs[:-1], offs[1:]) if b - a > 2]
    cs = mf.CrossSection(polys, mf.FillRule.EvenOdd)
    return E, cs ^ mf.CrossSection.square((BROWNIE_W,) * 2, center=True)


def brownie():
    """a cut square of brownie: brown cake with a crackly crust; black fudge in the cracks
    and black chocolate chunks.  Returns (cake, chocolate) in the same coordinates."""
    rng = np.random.default_rng(BROWNIE_SEED)
    E, cracks = crust_cracks(rng)
    half, H = BROWNIE_W / 2, BROWNIE_H - PUFF
    # the outline: a square with barely rounded corners, sampled evenly round it
    sq = mf.CrossSection.square((BROWNIE_W - 2 * BROWNIE_CORNER,) * 2, center=True).offset(BROWNIE_CORNER, mf.JoinType.Round, circular_segments=32)
    ring0 = np.asarray(sq.to_polygons()[0], float)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([ring0, ring0[:1]]), axis=0), axis=1))]
    n = 4 * 120
    s = np.linspace(0, seg[-1], n, endpoint=False)
    loop = np.vstack([ring0, ring0[:1]])
    ox, oy = np.interp(s, seg, loop[:, 0]), np.interp(s, seg, loop[:, 1])
    nx, ny = np.gradient(oy), -np.gradient(ox)                   # outward normals (the loop runs anticlockwise)
    nl = np.hypot(nx, ny); nx, ny = nx / nl, ny / nl
    if (ox * nx + oy * ny).mean() < 0:
        nx, ny = -nx, -ny
    P = seg[-1]
    waves = []                                                   # random little waves in every direction make crumbly lumps
    for _ in range(16):
        f = rng.uniform(0.5, 1.8)
        a = rng.uniform(0, 2 * math.pi)
        waves.append((round(f * math.cos(a) * P / (2 * math.pi)) * 2 * math.pi / P, f * math.sin(a),
                      rng.uniform(0, 2 * math.pi), 1 / f))
    norm = sum(w[3] for w in waves)
    def crumb(z):                                                # knife-cut crumb: small pits and lumps
        c = sum(amp * np.sin(kx * s + kz * z + ph) for kx, kz, ph, amp in waves) / norm
        return CRUMB * 1.6 * c
    def top_z(x, y):
        e = E(x, y)
        plate = PUFF * (1 - np.exp(-np.maximum(e, 0) / 1.2))
        groove = CRACK_DEEP * np.clip(1 - (e + 0.15) / 0.3, 0, 1)   # sinks over the crack
        dome = 0.4 * (1 - (x / half) ** 2) * (1 - (y / half) ** 2)
        return H + dome + plate - groove
    rings = [np.array([0, 0, 0.0])]
    rings.append(np.c_[ox - 0.4 * nx, oy - 0.4 * ny, np.zeros(n)])          # 45 degree foot chamfer
    for z in np.linspace(0.4, H - 1.0, 60):
        d = crumb(z) * min(1.0, (z - 0.4) / 1.0)
        rings.append(np.c_[ox + d * nx, oy + d * ny, np.full(n, z)])
    # round over the top edge into the crust
    d_top = crumb(H - 1.0)
    z_edge = top_z(ox, oy)
    for a in np.linspace(0, math.pi / 2, 6)[1:]:
        k = 0.6 * (1 - math.cos(a))
        x, y = ox + d_top * nx * math.cos(a) - k * nx, oy + d_top * ny * math.cos(a) - k * ny
        rings.append(np.c_[x, y, (H - 1.0) + (z_edge - (H - 1.0)) * math.sin(a)])
    for f in np.linspace(1, 0, 110)[1:-1]:
        x, y = (ox - 0.6 * nx) * f, (oy - 0.6 * ny) * f
        rings.append(np.c_[x, y, top_z(x, y)])
    rings.append(np.array([0, 0, float(top_z(np.array(0.0), np.array(0.0)))]))
    shell = loft(rings)
    # the outside must print without support (ignoring slivers far smaller than a nozzle's line)
    fn, cz = shell.face_normals, shell.triangles_center[:, 2]
    steep = (cz > 0.6) & (fn[:, 2] < -math.sin(math.radians(MAX_OVERHANG))) & (shell.area_faces > 0.01)
    assert not steep.any(), "the brownie overhangs more than 45 deg; it would need support"
    cake = to_manifold(shell)
    # the black: fudge under the cracks, and chocolate chunks
    fudge = mf.Manifold.extrude(cracks.offset(0.1, mf.JoinType.Round).simplify(0.02), FUDGE + CRACK_DEEP + 1.0).translate((0, 0, H - FUDGE - CRACK_DEEP))
    chunks = []
    def chunk(c, r, squash=(1.0, 1.0, 0.7)):
        # a broken chunk: a lumpy blob with a few flat faces where it snapped
        blob = mf.Manifold.sphere(1.0, 24).scale(tuple(r * q for q in squash))
        ph = rng.uniform(0, 6.3, 3)
        blob = blob.warp(lambda v: (v[0] * (1 + 0.25 * math.sin(2.5 * v[1] + ph[0])),
                                    v[1] * (1 + 0.25 * math.sin(2.5 * v[2] + ph[1])),
                                    v[2] * (1 + 0.2 * math.sin(2.5 * v[0] + ph[2]))))
        blob = blob.rotate(tuple(rng.uniform(0, 360, 3)))
        for _ in range(3):
            nrm = rng.normal(size=3); nrm /= np.linalg.norm(nrm)
            blob = blob.trim_by_plane(tuple(nrm), -0.55 * r)
        return blob.translate(tuple(c))
    placed = 0
    while placed < TOP_CHUNKS:                                   # melting out of the crust, on the plates
        x, y = rng.uniform(-half + 2.5, half - 2.5, 2)
        r = rng.uniform(1.3, 1.9)
        if E(np.array(x), np.array(y)) < 1.35 * r + 0.3:
            continue
        placed += 1
        z = float(top_z(np.array(x), np.array(y)))
        blob = mf.Manifold.sphere(1.0, 32).scale((r * 1.25, r, r * 0.55))
        ph = rng.uniform(0, 6.3)
        blob = blob.warp(lambda v: (v[0] * (1 + 0.22 * math.sin(3 * math.atan2(v[1], v[0]) + ph)),
                                    v[1] * (1 + 0.22 * math.sin(3 * math.atan2(v[1], v[0]) + ph)), v[2]))
        chunks.append(blob.rotate((0, 0, rng.uniform(0, 180))).translate((x, y, z - 0.1 * r)))
    for k in range(SIDE_CHUNKS):                                 # showing in the cut sides
        i = rng.integers(n)
        z = rng.uniform(1.6, H - 2.2)
        r = rng.uniform(0.9, 1.6)
        c = np.array([ox[i], oy[i], z]) - 0.35 * r * np.array([nx[i], ny[i], 0])
        chunks.append(chunk(c, r, (1.0, 1.0, 0.75)))
    black = fudge + mf.Manifold.batch_boolean(chunks, mf.OpType.Add)
    choc, body = cake ^ black, cake - black
    return to_trimesh(body), to_trimesh(choc)


# ================================================================ outside check for multi-colour parts
def check_outside(name, solid):
    """the outside of a part made of several colours must print without support,
    ignoring slivers far smaller than a nozzle's line"""
    t = to_trimesh(solid)
    fn, cz = t.face_normals, t.triangles_center[:, 2]
    steep = (cz > 0.6) & (fn[:, 2] < -math.sin(math.radians(MAX_OVERHANG + 0.5))) & (t.area_faces > 0.01)
    assert not steep.any(), f"the {name} overhangs more than {MAX_OVERHANG:.0f} deg; it would need support"


# ================================================================ chocolate-dipped pretzel
PRETZEL_PATH = [                # the strand's centre line, in units of half the width; one end to the other
    (-1.07, 0.04), (-0.62, -0.20), (-0.22, -0.40), (0.0, -0.50), (0.25, -0.62), (0.62, -0.74),
    (0.98, -0.52), (1.12, -0.05), (1.0, 0.42), (0.62, 0.68), (0.24, 0.58), (0.0, 0.36),
    (-0.24, 0.58), (-0.62, 0.68), (-1.0, 0.42), (-1.12, -0.05), (-0.98, -0.52), (-0.62, -0.74),
    (-0.25, -0.62), (0.0, -0.50), (0.22, -0.40), (0.62, -0.20), (1.07, 0.04)]


def pretzel_strand(grow=0.0, n=260):
    """the knotted strand: a chain of flat-bottomed half-ellipsoids hulled together.
    grow makes it fatter all round (for the chocolate coating and the drizzle)."""
    from scipy.interpolate import CubicSpline
    k = PRETZEL_W / 2 / 1.12 * (1 - STRAND / PRETZEL_W)
    pts = np.array(PRETZEL_PATH) * k
    t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    spl = CubicSpline(t, pts)
    ts = np.linspace(0, t[-1], n)
    c = spl(ts)
    L = t[-1]
    cross = t[3]                                                  # the first pass over the crossing goes on top
    blobs = []
    for ti, (x, y) in zip(ts, c):
        end = min(ti, L - ti) / L
        r = STRAND / 2 * (0.62 + 0.38 * min(1.0, end / 0.18)) + grow
        # the first pass over the crossing rides on top, and each end sits up on the loop it's pressed onto
        lift = 0.32 * math.exp(-((ti - cross) / 3.0) ** 2) + 0.35 * math.exp(-(min(ti, L - ti) / 2.2) ** 2)
        h = STRAND_H * (0.7 + 0.3 * min(1.0, end / 0.18)) * (1 + lift) + grow
        blobs.append(mf.Manifold.sphere(1.0, 20).scale((r, r, h)).translate((x, y, 0)))
    segs = [mf.Manifold.batch_hull([a, b]) for a, b in zip(blobs[:-1], blobs[1:])]
    m = mf.Manifold.batch_boolean(segs, mf.OpType.Add)
    return m.trim_by_plane((0, 0, 1), 0.0), c


def pretzel():
    """returns (dough, chocolate, white): the brown dough with its salt-free half, the black
    chocolate coating on the dipped half, and the white drizzle and salt"""
    rng = np.random.default_rng(PRETZEL_SEED)
    dough, path = pretzel_strand()
    coat, _ = pretzel_strand(COATING)
    over, _ = pretzel_strand(COATING + 0.45)
    half = PRETZEL_W / 2
    # the dip: everything below a wavy line
    xs = np.linspace(-half - 2, half + 2, 80)
    y_dip = DIP_AT * PRETZEL_W + 0.5 * np.sin(xs / 3.1 + 0.4) + 0.3 * np.sin(xs / 1.7)
    poly = np.r_[np.c_[xs, y_dip], [[half + 2, -half - 5], [-half - 2, -half - 5]]]
    dip_cs = mf.CrossSection([poly], mf.FillRule.NonZero)
    dipped = mf.Manifold.extrude(dip_cs, 20).translate((0, 0, -1))
    choc = coat ^ dipped
    dough = dough - dipped
    # white drizzle: a loose zigzag across the chocolate
    y0, y1 = -half * 0.95, DIP_AT * PRETZEL_W - 0.6
    zig, x = [], -half - 1
    while x < half + 1:                                          # flicked on by hand: uneven spacing and length
        lo, hi = y0 + rng.uniform(0, 2.5), y1 - rng.uniform(0, 1.5)
        zig.append((x, hi if len(zig) % 2 == 0 else lo))
        x += rng.uniform(1.6, 3.4)
    strokes = []
    for a, b in zip(zig[:-1], zig[1:]):
        wob = rng.uniform(-0.6, 0.6)
        mid = ((a[0] + b[0]) / 2 + wob, (a[1] + b[1]) / 2)
        for p, q in ((a, mid), (mid, b)):
            strokes.append(mf.CrossSection.batch_hull([mf.CrossSection.circle(DRIZZLE_W / 2, 12).translate(p),
                                                       mf.CrossSection.circle(DRIZZLE_W / 2, 12).translate(q)]))
    drizzle_cs = mf.CrossSection.batch_boolean(strokes, mf.OpType.Add)
    drizzle_raw = mf.Manifold.extrude(drizzle_cs, 20).translate((0, 0, 0.2)) ^ over ^ dipped   # stops just above the bed
    # coarse salt on the plain half: little white crystals sitting in the top of the dough
    salt = []
    tries = 0
    while len(salt) < SALT and tries < 2000:
        tries += 1
        i = rng.integers(len(path))
        x, y = path[i] + rng.normal(0, STRAND * 0.07, 2)
        if y < DIP_AT * PRETZEL_W + 2.5:
            continue
        if any(math.hypot(x - a, y - b) < 2.0 for a, b in salt):
            continue
        salt.append((x, y))
    crystals = []
    for x, y in salt:
        r = rng.uniform(0.55, 0.75)
        # a crystal: a little square post sunk deep into the dough, standing 0.45 mm proud of
        # its top, so nothing hangs over the dough's curve
        cube = mf.Manifold.cube((2 * r, 2 * r, 4.0), center=True).rotate((0, 0, rng.uniform(0, 90)))
        hit = dough ^ mf.Manifold.cylinder(20, 0.05).translate((x, y, -1))
        zt = hit.bounding_box()[5] if not hit.is_empty() else 0.0
        if zt < 0.8 * STRAND_H:                                  # only on the crown of the strand
            continue
        crystals.append(cube.translate((x, y, zt + rng.uniform(0.35, 0.45) - 2.0)))
    skin, _ = pretzel_strand(0.5)
    salt_raw = mf.Manifold.batch_boolean(crystals, mf.OpType.Add) ^ skin    # only where they sit in the top of the dough
    white = (drizzle_raw + salt_raw) - (dough + coat)
    check_outside("pretzel", dough + choc + drizzle_raw + salt_raw)        # the whole, before it's split by colour
    return to_trimesh(dough), to_trimesh(choc), to_trimesh(white)


# ================================================================ cheese wedge
def cheese():
    """an aged gouda wedge: returns (paste, wax), yellow and black"""
    rng = np.random.default_rng(CHEESE_SEED)
    # the wheel's profile through its middle, both sides of the axis, so the wax offset is even
    zs = np.linspace(0, WHEEL_H, 40)
    def r_side(z):
        return WHEEL_R + WHEEL_BULGE * np.sin(math.pi * z / WHEEL_H)
    out = [(r_side(z), z) for z in zs]
    # round the top edge and chamfer the bottom one (45 degrees, so it needs no support)
    prof = [(0, 0), (r_side(1.0) - 1.0, 0), (r_side(1.0), 1.0)] + [p for p in out if 1.0 < p[1] < WHEEL_H - 2.0]
    for a in np.linspace(0, math.pi / 2, 10):
        prof.append((r_side(WHEEL_H - 2) - 2 + 2 * math.cos(a), WHEEL_H - 2 + 2 * math.sin(a)))
    prof.append((0, WHEEL_H))
    right = np.array(prof)
    full = np.r_[right, (right * [-1, 1])[::-1]]
    outer = mf.CrossSection([full])
    inner = outer.offset(-WAX, mf.JoinType.Round)
    keep = mf.CrossSection.square((WHEEL_R * 2, WHEEL_H * 2)).translate((0, -WHEEL_H / 2))
    wedge = mf.Manifold.revolve(outer ^ keep, 256, WEDGE_ANGLE)
    # the paste is revolved a little past both cut faces and trimmed by the wedge, so the
    # two parts don't share faces that would leave slivers
    inside = mf.Manifold.revolve(inner ^ keep, 256, WEDGE_ANGLE + 2).rotate((0, 0, -1))
    paste, wax = wedge ^ inside, wedge - inside
    # small eyes in the cut faces: teardrop-shaped, so their tops slope at 45 degrees and print cleanly
    eyes = []
    for k in range(EYES):
        ang = 0.0 if k % 2 == 0 else WEDGE_ANGLE
        r = rng.uniform(0.6, 1.3)
        d = rng.uniform(6, WHEEL_R - 6)
        z = rng.uniform(WAX + r + 1.5, WHEEL_H - WAX - r * 2.5 - 1.5)
        drop = mf.Manifold.batch_hull([mf.Manifold.sphere(r, 32),
                                       mf.Manifold.sphere(0.05, 6).translate((0, 0, r * 1.45))])
        a = math.radians(ang)
        eyes.append(drop.translate((d * math.cos(a), d * math.sin(a), z)))
    paste = paste - mf.Manifold.batch_boolean(eyes, mf.OpType.Add)
    check_outside("cheese", wedge - mf.Manifold.batch_boolean(eyes, mf.OpType.Add))
    return to_trimesh(paste), to_trimesh(wax)


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
EXTRAS = {                      # treats that go in instead of (or as well as) the ones in the pictures
    "brownie": ("brownie", "brownie_choc"),
    "pretzel": ("pretzel", "pretzel_choc", "pretzel_white"),
    "cheese wedge": ("cheese", "cheese_wax"),
}


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
    parts["brownie"], parts["brownie_choc"] = brownie()
    parts["pretzel"], parts["pretzel_choc"], parts["pretzel_white"] = pretzel()
    parts["cheese"], parts["cheese_wax"] = cheese()
    for name in ("brownie", "brownie_choc", "pretzel", "pretzel_choc", "pretzel_white", "cheese", "cheese_wax"):
        assert parts[name].is_watertight and parts[name].volume > 0, f"the {name} isn't a closed solid"
        report[name] = 45.0                                      # each one checks its outside as a whole
    lo, hi = parts["basket"].bounds
    assert max(hi - lo) <= 86.0, "the basket is wider than the samosa"
    h_in = handle_in_basket(parts["handle"])
    items = arrange(parts["apple"], parts["cookie"], parts["snack_bag"])
    card_body, card_ink = card_in_basket(parts["card"], parts["card_ink"])
    whole_card = to_trimesh(to_manifold(card_body) + to_manifold(card_ink))
    check_fit(dict(items, card=whole_card), parts["basket"], h_in)
    items["card"], items["card_ink"] = card_body, card_ink
    # the extras aren't in the pictures' arrangement, but check each fits in the basket on its own
    for name, pieces in EXTRAS.items():
        whole = mf.Manifold.batch_boolean([to_manifold(parts[p]) for p in pieces], mf.OpType.Add)
        lone = place(to_trimesh(whole), at=(0, 0, FLOOR + 0.05))
        lone.apply_translation((-lone.centroid[0], -lone.centroid[1], 0))
        check_fit({name: lone}, parts["basket"], h_in)
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
