#!/usr/bin/env python3
"""
A small block for testing the magnet pockets before the long wheel print.

    python3 fit_test.py              -> stl/fit_test.stl

Six pockets in one upright face, made exactly like the wheel's (same
teardrop shape, same depth, same 0.1 mm sink), printed the same way up:

    left three:  4 x 2 mm magnets      right three: 6 x 2 mm magnets
    in each group, left to right: tight, the build's setting, loose
                 (pocket radius +0.06, +0.12, +0.18 mm over the magnet's)

The notch on the top left corner marks the left end.  Press a magnet into
each pocket.  The best fit goes in by hand, sits flush or just below, and
doesn't fall out when you turn the block over.  Set MAGNET_FIT in
build_wheel.py to that pocket's value.

Prints in about ten minutes.
"""
import os
import numpy as np, trimesh
import manifold3d as mf
from build_wheel import magnet_pocket, to_trimesh, MAGNET_SINK

HERE = os.path.dirname(os.path.abspath(__file__))
FITS = (0.06, 0.12, 0.18)
GROUPS = ((4.0, 2.0), (6.0, 2.0))      # magnet diameter, thickness
H, DEPTH, GAP = 14.0, 8.0, 3.0         # block height, thickness, wall between pockets
CZ = 6.0                               # pocket centre height

def build():
    xs, x = [], GAP + 1
    for d, h in GROUPS:
        for fit in FITS:
            r = d / 2 + fit
            xs.append((x + r, d, h, fit)); x += 2 * r + GAP
    L = x + 1
    block = mf.Manifold.cube([L, DEPTH, H])
    # the face at y = 0 stands in for a notch wall; pockets run into +y
    for cx, d, h, fit in xs:
        block = block - magnet_pocket(np.array([cx, 0.0, CZ]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), 0,
                                      d=d, h=h, fit=fit)
    notch = mf.Manifold.cube([4, DEPTH + 2, 4]).translate([-1, -1, H - 3])     # marks the left end
    block = block - notch
    path = os.path.join(HERE, "stl", "fit_test.stl")
    t = to_trimesh(block); t.export(path)
    assert trimesh.load(path).is_watertight
    print(f"wrote {path}: {L:.0f} x {DEPTH:.0f} x {H:.0f} mm, pockets {', '.join(f'{d:.0f}mm+{f:.2f}' for _, d, _, f in xs)}"
          f", magnet face {MAGNET_SINK} mm below the surface")

if __name__ == "__main__":
    build()
