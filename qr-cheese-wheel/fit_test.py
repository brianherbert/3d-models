#!/usr/bin/env python3
"""
A small block that rehearses the embedded magnets before the long wheel print.

    python3 fit_test.py              -> stl/fit_test.stl, stl/pauses.json entry

Six upright slots made exactly like the wheel's: same 0.6 mm skin on the front
face, same headroom, tops on a layer line, and the same pause before the
layer that closes them.

    left three:  4 x 2 mm magnets      right three: 6 x 2 mm magnets
    in each group, left to right: snug, the build's setting, loose
                 (slot 0.15, 0.25 or 0.35 mm thicker than the magnet)

When it pauses, drop a magnet into each slot on edge, face toward the front
(the side away from the notch on top).  The right slot takes the magnet
without forcing and holds it upright, and the nozzle doesn't pull it out
when printing resumes.  Afterwards, a magnet held to the front face should
find each one.  Set EMBED_SIDE in build_wheel.py to the best slot's value.

The notch on the back top edge marks the left end.  About ten minutes.
"""
import json, os
import numpy as np, trimesh
import manifold3d as mf
from build_wheel import magnet_slot, layer_top, to_trimesh, EMBED_SKIN, EMBED_TOP

HERE = os.path.dirname(os.path.abspath(__file__))
SIDES = (0.15, 0.25, 0.35)
GROUPS = ((4.0, 2.0), (6.0, 2.0))      # magnet diameter, thickness
DEPTH, GAP, FLOOR = 8.0, 3.0, 1.0      # block thickness, wall between slots, floor under the tallest slot

def build():
    z_top = layer_top(FLOOR + max(d for d, _ in GROUPS) + EMBED_TOP)   # every slot's top, on one layer line
    H = layer_top(z_top + 2.0)
    slots, pause, x = [], set(), GAP
    for d, h in GROUPS:
        for side in SIDES:
            cx = x + (d + 0.4) / 2
            # centre height chosen so magnet_slot puts this slot's top at z_top
            c = np.array([cx, 0.0, z_top - (d + EMBED_TOP) / 2])
            s, p = magnet_slot(c, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), 0, 0, d=d, h=h, side=side)
            slots.append(s); pause.add(p)
            x += d + 0.4 + GAP
    L = x
    block = mf.Manifold.cube([L, DEPTH, H])
    for s in slots:
        block = block - s
    block = block - mf.Manifold.cube([3, 3, 3]).translate([-1, DEPTH - 2, H - 2])   # left-end marker
    out = os.path.join(HERE, "stl")
    path = os.path.join(out, "fit_test.stl")
    t = to_trimesh(block); t.export(path)
    assert trimesh.load(path).is_watertight
    assert len(pause) == 1
    pj = os.path.join(out, "pauses.json")
    pauses = json.load(open(pj)) if os.path.exists(pj) else {}
    pauses["fit_test"] = sorted(pause)
    json.dump(pauses, open(pj, "w"))
    print(f"wrote {path}: {L:.0f} x {DEPTH:.0f} x {H:.1f} mm, {EMBED_SKIN} mm skin, pause before z = {min(pause):.2f} mm")

if __name__ == "__main__":
    build()
