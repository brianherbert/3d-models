#!/usr/bin/env python3
"""
A life-size samosa, standing up on its flat triangular bottom the way it sits
on a plate.  One solid part in one colour, printed with no supports.

The shape is built as a stack of rounded-triangle rings that shrink towards a
pointed top, with the faces bulging out where the filling pushes the pastry.
On top of that:

    seam      the overlapping flap where the pastry cone was folded and
              sealed, running from the tip down one face to the bottom
    lumps     gentle unevenness, because it's folded by hand
    blisters  the small bubbles a fried pastry gets

The bottom 2 mm stay smooth and flat so it sits on the bed (and the plate).

    python3 build_samosa.py            -> stl/samosa.stl
"""
import math, os
import numpy as np, trimesh
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- size (a real Punjabi samosa)
SIDE = 100.0                # length of each side of the triangular bottom, corner to corner
HEIGHT = 65.0               # bottom to tip
CORNER_R = 0.16             # corner rounding, as a fraction of the bottom's inradius
FACE_BULGE = 0.20           # how far the faces bulge out between the corners (fraction of the radius)
BELLY = 0.85                # how much fuller the middle is than a plain pyramid
TIP_R = 2.5                 # rounding of the tip
CHAMFER = 1.0               # 45 degree chamfer round the bottom edge (stops elephant's foot)

# ---------------------------------------------------------------- surface
SEAM_STEP = 1.3             # thickness of the overlapping flap's edge
SEAM_AT = 0.42              # where the seam runs, as a fraction of the way across one face
SEAM_WOBBLE = 1.2           # mm; a hand-folded seam isn't quite straight
LUMP_AMP = 0.7              # mm; low, broad unevenness
BLISTERS = 900              # how many small bubbles
BLISTER_AMP = (0.25, 0.75)  # mm high
BLISTER_SIZE = (1.2, 3.0)   # mm, the bubble's radius (gaussian sigma)
SMOOTH_FOOT = 2.0           # mm; no texture below this height
SEED = 7                    # change for a differently blistered samosa

# ---------------------------------------------------------------- mesh resolution
N_THETA = 540
N_Z = 180

MAX_OVERHANG = 40.0         # degrees from vertical; the build checks the shape stays printable

INRADIUS = SIDE / (2 * math.sqrt(3))


def rounded_triangle(theta):
    """Distance from the centre to the edge of a unit-inradius equilateral
    triangle with rounded corners, in each direction theta (a corner points
    along theta = 90 degrees)."""
    rho = CORNER_R
    a = 1.0 - rho                               # the triangle we round off
    corners = np.array([[math.cos(math.radians(90 + 120 * k)), math.sin(math.radians(90 + 120 * k))]
                        for k in range(3)]) * 2 * a

    def outside(p):                             # signed distance to the rounded triangle
        d = np.full(len(p), np.inf)
        inside = np.ones(len(p), bool)
        for i in range(3):
            A, B = corners[i], corners[(i + 1) % 3]
            ab = B - A
            t = np.clip(((p - A) @ ab) / (ab @ ab), 0, 1)
            d = np.minimum(d, np.linalg.norm(p - (A + t[:, None] * ab), axis=1))
            inside &= (ab[0] * (p[:, 1] - A[1]) - ab[1] * (p[:, 0] - A[0])) > 0
        return np.where(inside, -d, d) - rho

    u = np.stack([np.cos(theta), np.sin(theta)], 1)
    lo, hi = np.zeros(len(theta)), np.full(len(theta), 3.0)
    for _ in range(60):                         # bisect along each ray
        mid = (lo + hi) / 2
        out = outside(u * mid[:, None]) > 0
        hi = np.where(out, mid, hi)
        lo = np.where(out, lo, mid)
    return (lo + hi) / 2


def profile(z):
    """How big the cross-section is at height z, as a fraction of the bottom."""
    t = np.clip(z / HEIGHT, 0, 1)
    e = TIP_R / HEIGHT
    d = 1 - t                                                   # 1 at the bottom, 0 at the tip
    cone = np.sqrt(d * d + 2 * e * d) / math.sqrt(1 + 2 * e)    # straight sides, rounded tip
    return cone * (1 + BELLY * t)


def base_shape():
    theta = np.linspace(0, 2 * math.pi, N_THETA, endpoint=False)
    r_unit = rounded_triangle(theta)
    psi = (theta - math.pi / 2) % (2 * math.pi / 3)            # 0 at a corner, 2pi/3 at the next
    face = (1 - np.cos(3 * psi)) / 2                            # 0 at the corners, 1 mid-face

    # rings: dense near the bottom (chamfer, flat foot) and the tip
    t = np.linspace(0, 1, N_Z)
    z = HEIGHT * (t - 0.5 * np.sin(math.pi * t) / math.pi * 0.6)
    z = np.unique(np.concatenate([[0, CHAMFER * 0.5, CHAMFER], z]))
    z = z[z < HEIGHT - 1e-6]
    s = profile(z)
    bulge = 1 + FACE_BULGE * face[None, :] * np.sin(np.pi * np.clip(z / HEIGHT, 0, 1) * 0.85 + 0.25)[:, None]
    r = INRADIUS * s[:, None] * r_unit[None, :] * bulge
    r -= np.clip(CHAMFER - z, 0, None)[:, None]                 # the chamfer
    x = r * np.cos(theta)[None, :]
    y = r * np.sin(theta)[None, :]
    zz = np.repeat(z[:, None], N_THETA, 1)
    verts = np.stack([x, y, zz], -1).reshape(-1, 3)

    nr, nt = len(z), N_THETA
    idx = lambda i, j: i * nt + (j % nt)
    faces = []
    for i in range(nr - 1):
        for j in range(nt):
            a, b, c, d = idx(i, j), idx(i, j + 1), idx(i + 1, j + 1), idx(i + 1, j)
            faces += [(a, b, c), (a, c, d)]
    bottom = len(verts)
    top = bottom + 1
    verts = np.vstack([verts, [0, 0, 0], [0, 0, HEIGHT]])
    for j in range(nt):
        faces.append((bottom, idx(0, j + 1), idx(0, j)))
        faces.append((idx(nr - 1, j), idx(nr - 1, j + 1), top))
    m = trimesh.Trimesh(verts, np.array(faces), process=False)
    return m, theta, psi


def texture(m, theta, psi):
    """Move the surface out along its normals: seam flap, lumps and blisters."""
    rng = np.random.default_rng(SEED)
    v = m.vertices.copy()
    n = m.vertex_normals.copy()
    nr = (len(v) - 2) // N_THETA
    z = v[:, 2]
    foot = np.clip((z - SMOOTH_FOOT) / 8.0, 0, 1)               # fade the texture in gently above the foot
    foot = foot * foot * (3 - 2 * foot)
    tipfade = np.clip((HEIGHT - z) / 4.0, 0, 1)                 # and out at the very tip
    disp = np.zeros(len(v))

    # seam: on the face starting at the corner at theta = 90 deg (going round
    # anticlockwise), the flap covers the face from the corner to SEAM_AT of
    # the way across, ending in a crisp edge
    sector = 2 * math.pi / 3
    ps = np.tile(psi, nr)
    ps = np.concatenate([ps, [0, 0]])
    in_face = np.concatenate([np.tile((theta - math.pi / 2) % (2 * math.pi) < sector, nr), [False, False]])
    # wobble the seam line a little with height
    wob = SEAM_WOBBLE * (np.sin(z * 0.21 + 1.3) * 0.6 + np.sin(z * 0.53) * 0.4)
    r_here = np.maximum(np.hypot(v[:, 0], v[:, 1]), 1e-3)
    edge = SEAM_AT * sector + wob / r_here                      # seam line, as an angle from the corner
    rise = np.clip(ps / np.maximum(edge, 1e-3), 0, 1)           # flap thickens from the corner...
    rise = rise * rise * (3 - 2 * rise)
    drop = np.clip((edge - ps) * r_here / 0.5, 0, 1)            # ...to its edge, then drops off over 0.5 mm
    disp += np.where(in_face, SEAM_STEP * rise * drop, 0)

    # lumps: a few broad random waves
    for _ in range(6):
        k = rng.normal(size=3); k /= np.linalg.norm(k)
        f = rng.uniform(0.06, 0.12)
        disp += LUMP_AMP / 6 * 2 * np.sin(f * (v @ k) + rng.uniform(0, 2 * math.pi))

    # blisters: random small gaussian bubbles scattered over the surface
    side = np.where((z > SMOOTH_FOOT + 3) & (z < HEIGHT - 3))[0]
    centres = side[rng.choice(len(side), BLISTERS * 4, replace=True)]
    # keep them roughly evenly spread: drop any too close to an earlier one
    tree_pts, kept = [], []
    for c in centres:
        p = v[c]
        if all(np.linalg.norm(p - q) > 3.0 for q in tree_pts[-400:]):
            tree_pts.append(p); kept.append(c)
        if len(kept) >= BLISTERS:
            break
    tree = cKDTree(v)
    for c in kept:
        sig = rng.uniform(*BLISTER_SIZE)
        amp = rng.uniform(*BLISTER_AMP)
        near = tree.query_ball_point(v[c], 3 * sig)
        d2 = np.sum((v[near] - v[c]) ** 2, 1)
        disp[near] += amp * np.exp(-d2 / (2 * sig * sig))

    disp *= foot * tipfade * np.clip(r_here / 10.0, 0, 1)      # less near the narrow tip
    disp[-2:] = 0
    v += n * disp[:, None]
    v[:, 2] = np.where(z <= 1e-9, 0.0, v[:, 2])                 # keep the bottom dead flat
    return trimesh.Trimesh(v, m.faces, process=True)


def overhang(m):
    """the worst downward-facing slope, in degrees from vertical, above the chamfer"""
    fn = m.face_normals
    cz = m.triangles_center[:, 2]
    sel = (cz > CHAMFER + 0.2) & (fn[:, 2] < 0)
    if not sel.any():
        return 0.0
    return float(np.degrees(np.arcsin(-fn[sel, 2].min())))


def build():
    m, theta, psi = base_shape()
    assert m.is_watertight, "base shape isn't closed"
    m = texture(m, theta, psi)
    assert m.is_watertight, "textured shape isn't closed"
    assert m.is_winding_consistent and m.volume > 0
    oh = overhang(m)
    assert oh <= MAX_OVERHANG, f"part of it overhangs {oh:.0f} deg; it would need support"
    return m


def main():
    m = build()
    out = os.path.join(HERE, "stl")
    os.makedirs(out, exist_ok=True)
    m.export(os.path.join(out, "samosa.stl"))
    lo, hi = m.bounds
    print(f"samosa: {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, "
          f"{m.volume/1000:.0f} cm3, worst overhang {overhang(m):.0f} deg, {len(m.faces)} triangles")


if __name__ == "__main__":
    main()
