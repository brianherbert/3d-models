#!/usr/bin/env python3
"""
A round stand that holds a figure skate upright on a table.

A plain disc with a straight groove across the whole top for the blade to
slot into. Four versions: 4 in or 3 in across, each 2 in or 1 in tall.

    python3 build.py            -> stl/stand.stl, stand_short.stl,
                                       stand_3in.stl, stand_3in_short.stl
"""
import os
import numpy as np, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
IN = 25.4

# ---------------------------------------------------------------- disc
DISC_D = 4 * IN             # 101.6 mm
SMALL_D = 3 * IN            # 76.2 mm, the 3 in version
DISC_H = 2 * IN             # 50.8 mm
SHORT_H = 1 * IN            # 25.4 mm, the short version
VARIANTS = {                # name: (diameter, height)
    "stand": (DISC_D, DISC_H),
    "stand_short": (DISC_D, SHORT_H),
    "stand_3in": (SMALL_D, DISC_H),
    "stand_3in_short": (SMALL_D, SHORT_H),
}
TOP_CHAMFER = 1.5           # softens the top edge
FOOT_CHAMFER = 0.6          # bottom edge, so the first layer's squish doesn't leave a lip

# ---------------------------------------------------------------- groove
GROOVE_W = 4.1              # figure skate blades are about 3.8-4 mm thick
GROOVE_DEPTH = 10.0
GROOVE_LEAD = 0.8           # 45 degree lead-in along both top edges, to guide the blade in

SEGMENTS = 256

def to_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)

def disc(dia, h):
    r = dia / 2
    foot = mf.Manifold.cylinder(FOOT_CHAMFER, r - FOOT_CHAMFER, r, SEGMENTS)
    body = mf.Manifold.cylinder(h - FOOT_CHAMFER - TOP_CHAMFER, r, r, SEGMENTS).translate([0, 0, FOOT_CHAMFER])
    top = mf.Manifold.cylinder(TOP_CHAMFER, r, r - TOP_CHAMFER, SEGMENTS).translate([0, 0, h - TOP_CHAMFER])
    return foot + body + top

def groove(dia, h):
    """Runs along X, right across the disc and out both sides."""
    L = dia + 10
    slot = mf.Manifold.cube([L, GROOVE_W, GROOVE_DEPTH + 1], center=False).translate([-L / 2, -GROOVE_W / 2, h - GROOVE_DEPTH])
    # the lead-in: a V-shaped prism along the top of the slot
    w, d = GROOVE_W / 2 + GROOVE_LEAD, GROOVE_LEAD
    pts = []
    for x in (-L / 2, L / 2):
        for (y, z) in ((-GROOVE_W / 2, -0.01), (GROOVE_W / 2, -0.01), (w + 1, d + 1), (-w - 1, d + 1)):
            pts.append([x, y, h - GROOVE_LEAD + z])
    lead = mf.Manifold.hull_points(pts)
    return slot + lead

def build(dia, h):
    return disc(dia, h) - groove(dia, h)

def main():
    for name, (dia, h) in VARIANTS.items():
        check_and_write(name, dia, h)

def check_and_write(name, dia, h):
    m = build(dia, h)
    t = to_trimesh(m)
    assert t.is_watertight and t.is_winding_consistent, "mesh is broken"
    lo, hi = t.bounds
    assert np.allclose(hi[:2] - lo[:2], dia, atol=0.05) and abs(hi[2] - h) < 1e-3, t.bounds

    # check the groove: probe its width at mid-depth and its floor
    z = h - GROOVE_DEPTH / 2
    s = m.slice(z)
    pts = np.vstack([np.asarray(p) for p in s.to_polygons()])
    assert len(s.to_polygons()) == 2, "groove should split the slice in two"
    ys = pts[np.abs(pts[:, 1]) < 10, 1]     # the groove walls' vertices
    gap = ys[ys > 0].min() - ys[ys < 0].max()
    assert abs(gap - GROOVE_W) < 1e-3, gap
    assert len(m.slice(h - GROOVE_DEPTH - 0.01).to_polygons()) == 1, "groove floor"

    os.makedirs(os.path.join(HERE, "stl"), exist_ok=True)
    out = os.path.join(HERE, "stl", name + ".stl")
    t.export(out)
    print(f"wrote {out}: {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, "
          f"groove {gap:.2f} mm wide x {GROOVE_DEPTH:.1f} mm deep, volume {t.volume/1000:.0f} cm3")

if __name__ == "__main__":
    main()
