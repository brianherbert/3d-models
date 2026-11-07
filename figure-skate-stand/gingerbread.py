#!/usr/bin/env python3
"""
A gingerbread man that holds up the back of a figure skate, to go with the
round stands.

The figure is 1.5 in across (arm tip to arm tip), half the 3 in stand, and
lies flat like a cookie. The groove runs down his middle from the top of his
head to his crotch, where it comes out between his legs. It is twice as wide
as the round stands' groove, for a blade bedazzled on both sides, and the
same depth.

Two heights, to match the round stands: 2 in and 1 in.

    python3 gingerbread.py      -> stl/gingerbread.stl, stl/gingerbread_short.stl
"""
import os
import numpy as np, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
import sys; sys.path.insert(0, HERE)
from build import IN, DISC_H, SHORT_H, GROOVE_W, GROOVE_DEPTH, GROOVE_LEAD, to_trimesh

# ---------------------------------------------------------------- figure (plan view, mm; he faces up the page)
WIDTH = 1.5 * IN            # 38.1 mm, arm tip to arm tip
HEAD_R, HEAD_Y = 8.5, 37.0
TORSO = (-11.0, 12.0, 11.0, 30.0)       # x0, y0, x1, y1 of the body, before rounding
ARM_R = 4.5                 # half the arm's thickness
SHOULDER, HAND_Y = (6.0, 28.0), 23.0     # arms run from the shoulder down to the hand
LEG_R = 5.0
HIP, FOOT = (9.0, 18.0), (13.5, 3.0)     # the legs start inside the body
CROTCH_R = 5.5              # the round top of the gap between the legs
FILLET = 1.5                # rounds the armpits, neck and hips, like a cookie cutter

HEIGHTS = {"gingerbread": DISC_H, "gingerbread_short": SHORT_H}

# ---------------------------------------------------------------- groove
GB_GROOVE_W = 2 * GROOVE_W  # 8.2 mm: the blade is bedazzled on both sides
TOP_CHAMFER = 1.0
FOOT_CHAMFER = 0.4
STEP = 0.1                  # the chamfers are built as 0.1 mm steps, finer than the layers

def circle(x, y, r):
    return mf.CrossSection.circle(r, 96).translate([x, y])

def capsule(a, b, r):
    return mf.CrossSection.batch_hull([circle(*a, r), circle(*b, r)])

def outline():
    hand_x = WIDTH / 2 - ARM_R
    x0, y0, x1, y1 = TORSO
    body = mf.CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0]).offset(-4, mf.JoinType.Round).offset(4, mf.JoinType.Round)
    s = body + circle(0, HEAD_Y, HEAD_R)
    for sx in (-1, 1):
        s += capsule((sx * SHOULDER[0], SHOULDER[1]), (sx * hand_x, HAND_Y), ARM_R)
        s += capsule((sx * HIP[0], HIP[1]), (sx * FOOT[0], FOOT[1]), LEG_R)
    # The gap between the legs: a round arch that meets the inside edge of
    # each leg tangentially, so the edge runs smoothly from foot to foot.
    d = np.subtract(FOOT, HIP); d = d / np.hypot(*d)        # down the right leg
    n = np.array([d[1], -d[0]])                              # across it, towards the middle
    p = np.add(HIP, LEG_R * n)                               # a point on its inside edge
    cy = p[1] + (CROTCH_R + n[0] * p[0]) / n[1]              # arch centre: CROTCH_R from both edges
    t = np.array([0, cy]) - CROTCH_R * n                     # where the arch meets the right leg
    assert t[0] > GB_GROOVE_W / 2 + 1, "the legs are too close for the groove to come out between them"
    far = t + 40 * d
    gap = mf.CrossSection([[(-t[0], t[1]), (-far[0], far[1]), (far[0], far[1]), (t[0], t[1])]])   # anticlockwise
    s = s - (gap + circle(0, cy, CROTCH_R))
    s = s.offset(FILLET, mf.JoinType.Round).offset(-FILLET, mf.JoinType.Round)   # fillet the inside corners
    lo = s.bounds()
    return s.translate([0, -lo[1]])          # feet on y=0

def stack(shape, h):
    """Extrude with a 45 degree chamfer at the top and bottom edges."""
    ext = mf.Manifold.extrude
    shape = shape.simplify(0.01)
    inset = lambda k: shape.offset(-k * STEP, mf.JoinType.Round).simplify(0.01)   # no near-duplicate points
    parts = []
    n_foot, n_top = round(FOOT_CHAMFER / STEP), round(TOP_CHAMFER / STEP)
    for i in range(n_foot):
        parts.append(ext(inset(n_foot - i), STEP).translate([0, 0, i * STEP]))
    parts.append(ext(shape, h - FOOT_CHAMFER - TOP_CHAMFER).translate([0, 0, FOOT_CHAMFER]))
    for i in range(n_top):
        parts.append(ext(inset(i + 1), STEP)
                     .translate([0, 0, h - TOP_CHAMFER + i * STEP]))
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add)

def groove(h, length):
    """Down the middle, along Y, out past the head and on through the gap between the legs."""
    L = length + 20
    slot = mf.Manifold.cube([GB_GROOVE_W, L, GROOVE_DEPTH + 1]).translate([-GB_GROOVE_W / 2, -10, h - GROOVE_DEPTH])
    w = GB_GROOVE_W / 2 + GROOVE_LEAD
    pts = []
    for y in (-10, L - 10):
        for (x, z) in ((-GB_GROOVE_W / 2, -0.01), (GB_GROOVE_W / 2, -0.01), (w + 1, GROOVE_LEAD + 1), (-w - 1, GROOVE_LEAD + 1)):
            pts.append([x, y, h - GROOVE_LEAD + z])
    return slot + mf.Manifold.hull_points(pts)

def build(h):
    s = outline()
    length = s.bounds()[3]
    return stack(s, h) - groove(h, length)

def main():
    s = outline()
    b = s.bounds()
    print(f"outline {b[2]-b[0]:.1f} x {b[3]-b[1]:.1f} mm")
    for name, h in HEIGHTS.items():
        m = build(h)
        t = to_trimesh(m)
        assert t.is_watertight and t.is_winding_consistent, "mesh is broken"
        lo, hi = t.bounds
        assert abs((hi[0] - lo[0]) - WIDTH) < 0.05 and abs(hi[2] - h) < 1e-3, t.bounds
        # the groove: splits the top in two, is GB_GROOVE_W wide, and has a floor
        sl = m.slice(h - GROOVE_DEPTH / 2)
        polys = sl.to_polygons()
        assert len(polys) == 2, f"groove should split the top in two, got {len(polys)} pieces"
        xs = np.vstack([np.asarray(p) for p in polys])[:, 0]
        gap = xs[xs > 0].min() - xs[xs < 0].max()
        assert abs(gap - GB_GROOVE_W) < 1e-3, gap
        assert len(m.slice(h - GROOVE_DEPTH - 0.01).to_polygons()) == 1, "groove floor"
        # thinnest wall beside the groove (each half at mid-depth, eroded until it splits or vanishes)
        half = mf.CrossSection([polys[0]])
        thin = next(2 * d for d in np.arange(0.1, 10, 0.05)
                    if len(half.offset(-d, mf.JoinType.Round).to_polygons()) != 1)
        os.makedirs(os.path.join(HERE, "stl"), exist_ok=True)
        out = os.path.join(HERE, "stl", name + ".stl")
        t.export(out)
        print(f"wrote {out}: {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, groove {gap:.2f} mm wide "
              f"x {GROOVE_DEPTH:.1f} mm deep, thinnest part beside the groove about {thin:.1f} mm, volume {t.volume/1000:.0f} cm3")

if __name__ == "__main__":
    main()
