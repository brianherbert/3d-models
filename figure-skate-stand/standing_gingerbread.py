#!/usr/bin/env python3
"""
A standing gingerbread man who holds up the back of a figure skate.

The skate's blade sits in the round stand (the puck) at its middle. The boot
is heavy at the back, so the skate wants to tip backwards. He stands behind
the skate, facing the audience, and holds the back tip of the blade in his
hands, in a slot at the right height, so it can't tip.

He's a thick gingerbread cookie standing on a small base. His near arm
reaches down to his hands beside him, the other arm crosses his tummy to
join it, and his hands sit on a little pedestal that carries the weight
down to the base (it also means he prints without supports). Eyes, smile and
buttons are raised a little, so they show as shadows on white.

Coordinates: the blade runs along X, the skate's toe towards +X, so he stands
at the -X end. The audience is at -Y. Z is up.

    python3 standing_gingerbread.py     -> stl/standing_gingerbread.stl
"""
import os, sys
import numpy as np, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build import SHORT_H, GROOVE_DEPTH, GROOVE_LEAD, to_trimesh
from gingerbread import GB_GROOVE_W, circle, capsule

# ---------------------------------------------------------------- where the blade is
# Height of the slot's floor above the table: the bottom of the blade near its
# back tip, with the skate standing in the 1 in puck. The puck's groove floor
# is SHORT_H - GROOVE_DEPTH = 15.4 mm, and the blade's curve (rocker) lifts
# its back end about 4 mm more. Measure the real skate and change this.
HOLD_Z = SHORT_H - GROOVE_DEPTH + 4.0       # 19.4 mm
SLOT_W = GB_GROOVE_W                         # 8.2 mm, for the bedazzled blade

# ---------------------------------------------------------------- the figure (front view, mm; x across, z up, feet at z=0)
THICK = 18.0                # the cookie's thickness, front to back
EDGE = 0.8                  # chamfer round the front and back faces
HEAD_R, HEAD_Z = 10.0, 53.0
BODY = (-11.5, 14.0, 11.5, 44.0)            # x0, z0, x1, z1, before rounding
LEG_R, LEG_X, LEG_TOP = 5.5, 5.5, 16.0      # legs side by side, a small notch between the feet
FILLET = 1.5

# his hands, and a little gift box under them, beside him on the skate's side (+X)
CUP_X = (11.0, 25.0)        # the hands, from his side out towards the skate
CUP_FLOOR = 2.5             # under the slot
BOX_X = (15.5, 25.0)        # the gift box under his hands, down to the base: it carries the weight
NEAR_SHOULDER, NEAR_ARM_R = (9.0, 40.0), 3.8
SLOT_X0 = 14.5              # the slot runs from here out through the +X end of the hands

# raised details on the front
ARM_RELIEF, ARM_R = 1.6, 2.8                # both arms, raised on the front, reaching to his hands
FAR_SHOULDER = (-9.0, 40.0)
DETAIL = 0.8                                # eyes, smile, buttons, mittens

# ---------------------------------------------------------------- base
BASE_T = 3.0
BASE_PAD = 4.0              # how far the base reaches past him and the pedestal
BASE_CHAMFER = 1.0

STEP = 0.1

FLOOR = HOLD_Z - BASE_T                     # slot floor, above his feet
CUP_Z = (FLOOR - CUP_FLOOR, FLOOR + GROOVE_DEPTH)

def rect(x0, z0, x1, z1, r=0.0):
    s = mf.CrossSection.square([x1 - x0, z1 - z0]).translate([x0, z0])
    return s.offset(-r, mf.JoinType.Round).offset(r, mf.JoinType.Round) if r else s

def outline():
    """His silhouette from the front, hands and pedestal included."""
    s = rect(*BODY, r=6.0) + circle(0, HEAD_Z, HEAD_R)
    for sx in (-1, 1):
        s += capsule((sx * LEG_X, LEG_TOP), (sx * LEG_X, LEG_R), LEG_R)
    # a small 45 degree notch between the feet (prints without support)
    s -= mf.CrossSection([[(-4.0, -0.01), (4.0, -0.01), (0.0, 4.0)]])
    # near arm down to the hands, the hands, the pedestal
    hand_top_left = (CUP_X[0] + 3.0, CUP_Z[1] - 2.0)
    s += capsule(NEAR_SHOULDER, hand_top_left, NEAR_ARM_R)
    s += rect(CUP_X[0], CUP_Z[0], CUP_X[1], CUP_Z[1], r=2.5)
    s += rect(BOX_X[0], 0.0, BOX_X[1], CUP_Z[0] + 3.0, r=1.0)
    s = s.offset(FILLET, mf.JoinType.Round).offset(-FILLET, mf.JoinType.Round)
    return s.simplify(0.01)

def stacked(shape, z0, z1, ch0, ch1):
    """shape extruded from z0 to z1, with 45 degree chamfers of ch0 at the bottom and ch1 at the top."""
    ext = mf.Manifold.extrude
    inset = lambda d: shape.offset(-d, mf.JoinType.Round).simplify(0.01) if d > 0 else shape
    parts = [ext(shape, z1 - z0 - ch0 - ch1).translate([0, 0, z0 + ch0])]
    for i in range(round(ch0 / STEP)):
        parts.append(ext(inset(ch0 - i * STEP), STEP).translate([0, 0, z0 + i * STEP]))
    for i in range(round(ch1 / STEP)):
        parts.append(ext(inset((i + 1) * STEP), STEP).translate([0, 0, z1 - ch1 + i * STEP]))
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add)

def stand_up(m):
    """2D outline coordinates (x, y) -> (x, z); the extrusion axis -> -Y, so +z becomes the front."""
    return m.rotate([90, 0, 0])

def relief(pieces, depth, chamfer):
    """Raised from the front face by `depth`. With chamfer, each piece (they must be convex) gets
    sides sloping at 45 degrees, so its underside prints without support."""
    z0, z1 = THICK / 2 - 0.3, THICK / 2 + depth
    out = []
    for p in pieces:
        if chamfer:
            lo = np.vstack(p.to_polygons())
            hi = np.vstack(p.offset(-depth, mf.JoinType.Round).to_polygons())
            pts = [[x, y, z0] for x, y in lo] + [[x, y, z1] for x, y in hi]
            out.append(mf.Manifold.hull_points(pts))
        else:
            out.append(mf.Manifold.extrude(p, z1 - z0).translate([0, 0, z0]))
    return stand_up(mf.Manifold.batch_boolean(out, mf.OpType.Add))

def details():
    hand = (CUP_X[0] + 3.0, (CUP_Z[0] + CUP_Z[1]) / 2 + 1.0)
    near_hand = (CUP_X[0] + 9.5, hand[1] + 0.5)
    arms = relief([capsule(FAR_SHOULDER, hand, ARM_R), capsule((NEAR_SHOULDER[0] - 1.0, NEAR_SHOULDER[1]), near_hand, ARM_R)],
                  ARM_RELIEF, True)
    mittens = [circle(hand[0] + 1.0, hand[1] - 1.0, 3.8), circle(*near_hand, 3.8)]
    eyes = [circle(-3.6, HEAD_Z + 2.0, 1.5), circle(3.6, HEAD_Z + 2.0, 1.5)]
    smile = (circle(0, HEAD_Z + 1.5, 5.2) - circle(0, HEAD_Z + 1.5, 4.0)) ^ rect(-4.2, HEAD_Z - 6, 4.2, HEAD_Z - 1.5)
    buttons = [circle(0, 39.5, 1.6), circle(0, 25.0, 1.6)]
    # a ribbon round the gift box: one band up the front, one across
    bx = (BOX_X[0] + BOX_X[1]) / 2
    ribbon = [rect(bx - 1.2, 0.0, bx + 1.2, CUP_Z[0] - 0.5), rect(BOX_X[0], 5.2, BOX_X[1], 7.6)]
    return (arms + relief(mittens, ARM_RELIEF + 0.4, True) + relief(eyes + buttons, DETAIL, True)
            + relief([smile], DETAIL, False) + relief(ribbon, DETAIL, True))

def lid_line():
    """A fine groove across the front where his hands sit on the box's lid."""
    x0, x1 = CUP_X[0] + 3.0, BOX_X[1] + 1
    return (mf.Manifold.cube([x1 - x0, 1.0, 0.6]).translate([x0, -THICK / 2 - 0.5, CUP_Z[0] - 0.3]))

def slot():
    x0, x1 = SLOT_X0, CUP_X[1] + 20
    box = mf.Manifold.cube([x1 - x0, SLOT_W, GROOVE_DEPTH + 10]).translate([x0, -SLOT_W / 2, FLOOR])
    w = SLOT_W / 2 + GROOVE_LEAD
    top = CUP_Z[1]
    pts = []
    for x in (x0, x1):
        for (y, z) in ((-SLOT_W / 2, -0.01), (SLOT_W / 2, -0.01), (w + 1, GROOVE_LEAD + 1), (-w - 1, GROOVE_LEAD + 1)):
            pts.append([x, y, top - GROOVE_LEAD + z])
    return box + mf.Manifold.hull_points(pts)

def base(s):
    lo = s.bounds()
    plate = rect(lo[0] - BASE_PAD, -THICK / 2 - BASE_PAD, lo[2] + BASE_PAD, THICK / 2 + BASE_PAD, r=8.0)
    return stacked(plate, 0.0, BASE_T, 0.4, BASE_CHAMFER)

def build():
    s = outline()
    body = stand_up(stacked(s, -THICK / 2, THICK / 2, EDGE, EDGE)) - lid_line() + details()
    body = body.translate([0, 0, BASE_T - 0.01])
    m = base(s) + body
    return m - slot().translate([0, 0, BASE_T])

def overhangs(shape, limit_deg=45.0):
    """Edges of the silhouette that face down more steeply than limit_deg past vertical (bridges
    included), not counting the feet and the box on the base. The extrusion is along Y, so the
    silhouette is what decides the overhangs; the 45 degree chamfers and reliefs are printable."""
    total, where = 0.0, []
    for p in shape.to_polygons():
        p = np.asarray(p); q = np.roll(p, -1, axis=0)
        d = q - p; L = np.hypot(d[:, 0], d[:, 1])
        ny = -d[:, 0] / np.maximum(L, 1e-9)          # outward normal's z part (anticlockwise outline)
        bad = (ny < -np.sin(np.radians(limit_deg)) - 1e-3) & (np.minimum(p[:, 1], q[:, 1]) > 0.05)
        total += L[bad].sum(); where += [tuple(np.round((p[k] + q[k]) / 2, 1)) for k in np.nonzero(bad)[0]]
    return total, where

def main():
    m = build()
    t = to_trimesh(m)
    assert t.is_watertight and t.is_winding_consistent, "mesh is broken"
    lo, hi = t.bounds
    # the slot: SLOT_W wide, floor at HOLD_Z, GROOVE_DEPTH deep below the top of the hands
    sl = m.slice(HOLD_Z + GROOVE_DEPTH / 2)
    pts = np.vstack([np.asarray(p) for p in sl.to_polygons()])
    near = pts[(pts[:, 0] > SLOT_X0 + 1) & (pts[:, 0] < CUP_X[1] - 1)]
    gap = near[near[:, 1] > 0, 1].min() - near[near[:, 1] < 0, 1].max()
    assert abs(gap - SLOT_W) < 1e-3, gap
    probe = lambda z: (m ^ mf.Manifold.cube([0.2, 0.2, 0.2], True).translate([(SLOT_X0 + CUP_X[1]) / 2, 0, z])).volume()
    assert probe(HOLD_Z - 0.2) > 0.007 and probe(HOLD_Z + 0.2) == 0, "slot floor isn't at HOLD_Z"
    length, where = overhangs(outline())
    zs = sorted({round(w[1]) for w in where})
    os.makedirs(os.path.join(HERE, "stl"), exist_ok=True)
    out = os.path.join(HERE, "stl", "standing_gingerbread.stl")
    t.export(out)
    print(f"wrote {out}: {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, slot {gap:.2f} mm wide, "
          f"floor {HOLD_Z:.1f} mm up, {GROOVE_DEPTH:.0f} mm deep; silhouette edges past 45 deg: {length:.1f} mm"
          + (f" (at heights above his feet {zs})" if zs else ""))

if __name__ == "__main__":
    main()
