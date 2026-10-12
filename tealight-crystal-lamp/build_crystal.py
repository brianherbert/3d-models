#!/usr/bin/env python3
"""
A crystal lamp for one LED tea light (Bambu Lab LED Flame Tea Light, 37.2 mm
across, 36.6 mm tall including the flame).

Two parts, each its own plate:

    base      white.  A low hexagon with the tea light pocket, two
              finger notches and a socket the crystal drops into
    crystal   translucent blue.  One regular hexagonal crystal with a
              six-sided point.  A hollow shell two lines thick, open underneath

The base is a hexagon too, lined up with the crystal.

    python3 build_crystal.py            -> stl/base.stl, crystal.stl, assembled.stl
"""
import math, os
import numpy as np, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- tea light
TEA_D, TEA_H = 37.2, 36.6
POCKET_R = TEA_D / 2 + 0.5          # drops in and lifts out freely
POCKET_DEPTH = 8.0                  # below the socket floor
NOTCH_W, NOTCH_R = 12.0, 24.0       # two finger notches beside the tea light, out to this radius
TEA_GAP = 1.0                       # least gap between the tea light and the inside of the crystal

# ---------------------------------------------------------------- base
BASE_H = 16.0
BASE_R = 50.0                       # corner radius of the hexagon at the bottom
BASE_INSET = 4.0                    # the sides slope in by this much to the top
SOCKET_DEPTH = 5.0
SOCKET_FIT = 0.4                    # gap all round between the crystal and its socket

# ---------------------------------------------------------------- crystal
TOTAL_H = 152.0                     # assembled height (6 in)
CRYSTAL_H = TOTAL_H - (BASE_H - SOCKET_DEPTH)
CRYSTAL_R = 32.0                    # corner radius of the hexagon
SHOULDER_H = 98.0                   # where the prism ends and the point begins
TOP_SCALE = 0.95                    # the prism narrows slightly towards the point
ROTATION = 0.0                      # degrees; 0 puts a flat face (crystal and base) at the front
WALL = 0.9                          # two 0.45 mm lines
FOOT_H, FOOT_W = SOCKET_DEPTH, 1.6  # thicker band inside the bottom, hidden in the socket
MIN_SLOPE = 50.0                    # every roof facet at least this steep (the inside of the roof is an overhang)

SOCKET_FLOOR = BASE_H - SOCKET_DEPTH
POCKET_FLOOR = SOCKET_FLOOR - POCKET_DEPTH

def to_manifold(t):
    return mf.Manifold(mf.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))

def to_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)

def hull(points):
    return mf.Manifold.hull_points(np.asarray(points, np.float64).tolist())

def planes(t):
    """unique face planes of a convex mesh: (unit normal, offset) with n.x <= d inside"""
    out = []
    for n, v in zip(t.face_normals, t.vertices[t.faces[:, 0]]):
        d = float(n @ v)
        if not any(np.allclose(n, m, atol=1e-6) and abs(d - e) < 1e-4 for m, e in out):
            out.append((n, d))
    return out

def shrink(t, by, keep_bottom_open=True):
    """the convex solid t with every face moved in by `by`; the bottom face
    is dropped so the result pokes out underneath (an open shell)"""
    lo, hi = t.bounds
    m = mf.Manifold.cube((hi - lo + 20).tolist()).translate((lo - 10).tolist())
    for n, d in planes(t):
        if keep_bottom_open and n[2] < -0.999:
            continue
        m = m.trim_by_plane((-n).tolist(), -(d - by))
    # where four planes meet in one point, trimming leaves near-duplicate
    # corners; the hull of the (convex) result merges them cleanly
    return m.hull()

# ---------------------------------------------------------------- crystal
def crystal_points():
    ang = np.radians(ROTATION + 60 * np.arange(6))
    pts = [(CRYSTAL_R * math.cos(t), CRYSTAL_R * math.sin(t), 0.0) for t in ang]
    pts += [(TOP_SCALE * CRYSTAL_R * math.cos(t), TOP_SCALE * CRYSTAL_R * math.sin(t), SHOULDER_H) for t in ang]
    pts.append((0.0, 0.0, CRYSTAL_H))
    return np.array(pts)

def min_slope(t):
    """steepness (degrees from horizontal) of the shallowest upward facet"""
    up = t.face_normals[:, 2] > 1e-6
    return math.degrees(math.acos(t.face_normals[up, 2].max()))

def clearance(inner, z0, z1):
    """least distance from the tea light's axis (z) to the inside of the
    crystal between heights z0 and z1 (crystal coordinates)"""
    best = 1e9
    for z in np.linspace(z0 + 0.01, z1, 12):
        polys = inner.slice(z).to_polygons()
        for p in polys:
            q = np.roll(p, -1, axis=0)
            e = q - p
            s = np.clip(-(p * e).sum(1) / (e * e).sum(1), 0, 1)
            best = min(best, np.linalg.norm(p + e * s[:, None], axis=1).min())
    return best

def crystal():
    outer_t = to_trimesh(hull(crystal_points()))
    assert min_slope(outer_t) >= MIN_SLOPE, f"the point is too flat ({min_slope(outer_t):.0f} deg)"
    inner = shrink(outer_t, WALL)
    foot_inner = shrink(outer_t, WALL + FOOT_W)
    tea_top = POCKET_FLOOR + TEA_H - SOCKET_FLOOR            # crystal z is 0 at the socket floor
    need = TEA_D / 2 + TEA_GAP
    assert clearance(foot_inner, 0, FOOT_H) >= need and clearance(inner, FOOT_H, tea_top + 2) >= need, \
        "the crystal is too narrow for the tea light"
    outer = to_manifold(outer_t)
    slab = mf.Manifold.cube([400, 400, FOOT_H]).translate([-200, -200, 0])
    shell = (outer - inner) + ((outer ^ slab) - foot_inner)
    return shell, outer_t, foot_inner

# ---------------------------------------------------------------- base
def base(crystal_outer, foot_inner):
    ang = np.radians(ROTATION + 60 * np.arange(6))
    pts = [(BASE_R * math.cos(t), BASE_R * math.sin(t), 0.0) for t in ang]
    pts += [((BASE_R - BASE_INSET) * math.cos(t), (BASE_R - BASE_INSET) * math.sin(t), BASE_H) for t in ang]
    stone = hull(pts)
    # socket: the crystal's footprint over the socket depth, plus the fit gap
    sl = [to_manifold(crystal_outer).slice(z) for z in (0.01, SOCKET_DEPTH)]
    foot = mf.CrossSection.batch_hull(sl).offset(SOCKET_FIT, mf.JoinType.Round)
    socket = foot.extrude(SOCKET_DEPTH + 1).translate([0, 0, SOCKET_FLOOR])
    pocket = mf.Manifold.cylinder(BASE_H, POCKET_R, POCKET_R, 160).translate([0, 0, POCKET_FLOOR])
    # finger notches: the two opposite directions with the most room inside the crystal's foot
    best, best_a = -1, 0
    fi = foot_inner.slice(0.01)
    for a in np.radians(np.arange(0, 180, 2)):
        room = min(_reach(fi, a), _reach(fi, a + math.pi))
        if room > best:
            best, best_a = room, a
    assert best >= NOTCH_R + 0.5, f"no room for the finger notches ({best:.1f} mm)"
    notch = mf.Manifold.cube([NOTCH_R * 2, NOTCH_W, BASE_H]).translate([-NOTCH_R, -NOTCH_W / 2, POCKET_FLOOR])
    notch = (notch ^ mf.Manifold.cylinder(BASE_H, NOTCH_R, NOTCH_R, 160).translate([0, 0, POCKET_FLOOR]))
    notch = notch.rotate([0, 0, math.degrees(best_a)])
    return stone - socket - pocket - notch, math.degrees(best_a)

def _reach(section, a):
    """distance from the origin to the outline of `section` in direction a"""
    d = np.array([math.cos(a), math.sin(a)])
    best = 1e9
    for p in section.to_polygons():
        q = np.roll(p, -1, axis=0)
        for u, v in zip(p, q):
            m = np.array([d, u - v]).T
            if abs(np.linalg.det(m)) < 1e-9:
                continue
            t, s = np.linalg.solve(m, u)
            if t > 0 and 0 <= s <= 1:
                best = min(best, t)
    return best

def main():
    out = os.path.join(HERE, "stl")
    os.makedirs(out, exist_ok=True)
    shell, outer_t, foot_inner = crystal()
    stone, notch_a = base(outer_t, foot_inner)
    meshes = {}
    for name, m in (("base", stone), ("crystal", shell)):
        t = to_trimesh(m)
        assert t.is_watertight, name
        t.export(os.path.join(out, name + ".stl"))
        meshes[name] = t
        lo, hi = t.bounds
        print(f"{name:8s} {hi[0]-lo[0]:6.1f} x {hi[1]-lo[1]:6.1f} x {hi[2]-lo[2]:6.1f} mm  {t.volume / 1000:6.1f} cm3")
    asm = trimesh.util.concatenate([meshes["base"], meshes["crystal"].copy().apply_translation([0, 0, SOCKET_FLOOR])])
    asm.export(os.path.join(out, "assembled.stl"))
    tea_top = POCKET_FLOOR + TEA_H - SOCKET_FLOOR
    print(f"shallowest roof facet {min_slope(outer_t):.0f} deg, "
          f"tea-light clearance {clearance(foot_inner, 0, FOOT_H) - TEA_D / 2:.1f} mm at the foot, "
          f"notches at {notch_a:.0f} deg; overall height {asm.bounds[1][2]:.1f} mm")

if __name__ == "__main__":
    main()
