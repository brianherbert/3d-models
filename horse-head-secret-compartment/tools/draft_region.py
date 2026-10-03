#!/usr/bin/env python3
"""Mesh a world-space box of the sculpt at fine resolution for close-ups.
    python3 draft_region.py res name x0 x1 y0 y1 z0 z1"""
import sys, numpy as np, trimesh, subprocess
from skimage import measure
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import horse_sculpt as S
res = float(sys.argv[1]); name = sys.argv[2]
b = [float(v) for v in sys.argv[3:9]]
xs = np.arange(b[0] + 0.37 * res, b[1], res); ys = np.arange(b[2] + 0.37 * res, b[3], res); zs = np.arange(b[4] + 0.37 * res, b[5], res)
S.anchors()
out = np.empty((len(xs), len(ys), len(zs)), np.float32)
X, Y = np.meshgrid(xs, ys, indexing="ij")
for k0 in range(0, len(zs), 8):
    z = zs[k0:k0 + 8]
    P = np.c_[np.repeat(X[..., None], len(z), 2).ravel(), np.repeat(Y[..., None], len(z), 2).ravel(), np.broadcast_to(z, X.shape + (len(z),)).ravel()]
    out[:, :, k0:k0 + len(z)] = S.sculpt(P).reshape(len(xs), len(ys), len(z))
v, f, _, _ = measure.marching_cubes(out, 0.0, spacing=(res, res, res))
m = trimesh.Trimesh(v + [xs[0], ys[0], zs[0]], f)
m.export(f"stl/_{name}.stl")
subprocess.run(["python3", "tools/render.py", f"stl/_{name}.stl", f"images/_{name}"] + (sys.argv[9:] or ["side", "threeq", "front", "left"]), stderr=subprocess.DEVNULL)
print("done")
