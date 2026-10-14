#!/usr/bin/env python3
"""
A dipping cup to go with the samosa, and the sauce that sits in it.  Two
parts, each printed on its own in one colour, so no AMS is needed:

    dip_cup     white.  A small tapered sauce cup (a katori) with a lip
    dip_sauce   red.  A disc shaped to the inside of the cup that drops in
                and fills it two thirds of the way up, with a meniscus
                round the edge and a gentle swirl on top

    python3 build_dip.py            -> stl/dip_cup.stl, dip_sauce.stl, dip_assembled.stl
"""
import math, os
import numpy as np, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- cup
CUP_TOP_R = 33.0            # outside radius at the rim (66 mm across), wide enough to dip a samosa corner in
CUP_BOT_R = 25.0            # outside radius at the bottom
CUP_H = 30.0
WALL = 2.2                  # measured across, horizontally
FLOOR = 2.4
FILLET = 3.0                # inside, where the wall meets the floor
LIP = 1.2                   # the rim sticks out this much, with a 45 degree underside
FOOT_CHAMFER = 0.6          # stops elephant's foot

# ---------------------------------------------------------------- sauce
SAUCE_LEVEL = 18.0          # height of the sauce above the cup's inside floor
FIT = 0.35                  # gap all round between the sauce and the cup
MENISCUS = 0.8              # the sauce creeps up the cup wall this much
SWIRL = 0.35                # mm; a gentle swirl on the surface

SEGMENTS = 256
MAX_OVERHANG = 45.0         # degrees from vertical

INNER_TOP_R = CUP_TOP_R - WALL
INNER_BOT_R = CUP_BOT_R + (CUP_TOP_R - CUP_BOT_R) * FLOOR / CUP_H - WALL


def inner_r(z):
    """the cup's inside radius at height z (above the bed), ignoring the fillet"""
    t = (z - FLOOR) / (CUP_H - FLOOR)
    return INNER_BOT_R + (INNER_TOP_R - INNER_BOT_R) * t


def arc(cx, cy, r, a0, a1, n=16):
    return [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in np.linspace(a0, a1, n)]


def cup():
    # half cross-section (x = radius, y = height), anticlockwise
    slope = math.atan2(CUP_TOP_R - CUP_BOT_R, CUP_H)          # the wall's lean from vertical
    pts = [(0, 0), (CUP_BOT_R - FOOT_CHAMFER, 0), (CUP_BOT_R, FOOT_CHAMFER)]
    lip_lo = CUP_H - 1.0 - 2.2 * LIP                            # lip: steps out under 45 degrees, then rounded over
    pts += [(CUP_BOT_R + (CUP_TOP_R - CUP_BOT_R) * lip_lo / CUP_H, lip_lo),
            (CUP_TOP_R + LIP, CUP_H - 1.0)]
    # round over the top of the rim, from the outside of the lip to the inside of the wall
    rim_r = (CUP_TOP_R + LIP - INNER_TOP_R) / 2
    pts += arc(INNER_TOP_R + rim_r, CUP_H - 1.0, rim_r, 0, math.pi, 24)[1:]
    # down the inside wall to the fillet, round it, along the floor
    fz = FLOOR + FILLET
    fr = inner_r(fz)
    pts += [(fr, fz)]
    pts += arc(fr - FILLET, fz, FILLET, -slope, -math.pi / 2, 12)[1:]
    pts += [(0, FLOOR)]
    cs = mf.CrossSection([pts])
    return mf.Manifold.revolve(cs, SEGMENTS)


def sauce():
    """revolved profile, bottom centre to top centre, with the swirl added to the top"""
    z0 = FLOOR + 0.05                                           # rests on the cup floor
    top = FLOOR + SAUCE_LEVEL
    r_at = lambda z: inner_r(z) - FIT
    # a 45 degree chamfer round the bottom clears the cup's fillet (and needs no support)
    c = FILLET + FIT + 0.5
    prof = [(0.0, z0)]
    prof += [(r, z0) for r in np.linspace(0, r_at(z0 + c) - c, 30)[1:]]
    prof += [(r_at(z), z) for z in np.linspace(z0 + c, top - 0.6, 40)[1:]]
    R = r_at(top)
    prof += [(R - 0.15, top + MENISCUS * 0.9)]                  # up the wall, then the meniscus curls over
    rs = np.linspace(R - 0.3, 0, 60)
    prof += [(r, top + MENISCUS * math.exp(-(R - r) / 1.5)) for r in rs]
    prof = np.array(prof)

    n = SEGMENTS
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    verts, rings = [], []
    for i, (r, z) in enumerate(prof):
        if r < 1e-9:
            rings.append([len(verts)]); verts.append((0, 0, z)); continue
        ring = []
        on_top = i >= len(prof) - len(rs)
        for a in th:
            dz = 0.0
            if on_top:                                          # a soft three-armed swirl
                u = r / R
                dz = SWIRL * math.sin(3 * a + 9 * u) * 4 * u * (1 - u)
            ring.append(len(verts)); verts.append((r * math.cos(a), r * math.sin(a), z + dz))
        rings.append(ring)
    faces = []
    for A, B in zip(rings[:-1], rings[1:]):
        if len(A) == 1:
            faces += [(A[0], B[(j + 1) % n], B[j]) for j in range(n)]
        elif len(B) == 1:
            faces += [(A[j], A[(j + 1) % n], B[0]) for j in range(n)]
        else:
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


def overhang(m, above=1.0):
    fn, cz = m.face_normals, m.triangles_center[:, 2]
    sel = (cz > above) & (fn[:, 2] < 0)
    return float(np.degrees(np.arcsin(-fn[sel, 2].min()))) if sel.any() else 0.0


def build():
    c = to_trimesh(cup())
    s = sauce()
    for name, t in (("cup", c), ("sauce", s)):
        assert t.is_watertight and t.volume > 0, f"the {name} isn't a closed solid"
    # the sauce prints upright, standing on its flat bottom
    s_print = s.copy(); s_print.apply_translation([0, 0, -s.bounds[0][2]])
    for name, t in (("cup", c), ("sauce", s_print)):
        oh = overhang(t, FOOT_CHAMFER + 0.2)
        assert oh <= MAX_OVERHANG, f"the {name} overhangs {oh:.0f} deg; it would need support"
    # the cup's underside (inside the cup) is the inside floor: only check outside faces of the cup
    clash = (to_manifold(c) ^ to_manifold(s)).volume()
    assert clash < 1e-3, f"the sauce doesn't fit in the cup ({clash:.2f} mm3 overlap)"
    return c, s_print, c + s


def main():
    c, s, both = build()
    out = os.path.join(HERE, "stl")
    os.makedirs(out, exist_ok=True)
    c.export(os.path.join(out, "dip_cup.stl"))
    s.export(os.path.join(out, "dip_sauce.stl"))
    both.export(os.path.join(out, "dip_assembled.stl"))
    for name, t in (("cup", c), ("sauce", s)):
        lo, hi = t.bounds
        print(f"{name}: {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, {t.volume/1000:.1f} cm3, "
              f"worst overhang {overhang(t, FOOT_CHAMFER + 0.2):.0f} deg")


if __name__ == "__main__":
    main()
