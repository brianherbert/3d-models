#!/usr/bin/env python3
"""Draft mesher + renderer for the sculpt.  python3 draft.py [res] [name]"""
import sys, time, numpy as np, trimesh, subprocess
from skimage import measure
import horse_sculpt as S
res = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
name = sys.argv[2] if len(sys.argv) > 2 else "draft"
xs = np.arange(-52 + 0.37 * res, 52, res)
ys = np.arange(-135 + 0.37 * res, 64, res)
zs = np.arange(-1 + 0.37 * res, 190, res)
t0 = time.time()
S.anchors()
out = np.empty((len(xs), len(ys), len(zs)), np.float32)
X, Y = np.meshgrid(xs, ys, indexing="ij")
for k0 in range(0, len(zs), 16):
    z = zs[k0:k0 + 16]
    P = np.c_[np.repeat(X[..., None], len(z), 2).ravel(), np.repeat(Y[..., None], len(z), 2).ravel(),
              np.broadcast_to(z, X.shape + (len(z),)).ravel()]
    out[:, :, k0:k0 + len(z)] = S.sculpt(P).reshape(len(xs), len(ys), len(z))
v, f, _, _ = measure.marching_cubes(out, 0.0, spacing=(res, res, res))
v += [xs[0], ys[0], zs[0]]
m = trimesh.Trimesh(v, f)
parts = [p for p in m.split(only_watertight=False) if abs(p.volume) > 20]
m = trimesh.util.concatenate(parts); m.fix_normals()
m.export(f"stl/_{name}.stl")
print(f"{time.time()-t0:.0f}s  watertight={m.is_watertight} bounds={np.round(m.bounds,1).tolist()}")
import subprocess
subprocess.run(["python3", "tools/render.py", f"stl/_{name}.stl", f"images/_{name}", "side", "threeq", "front", "left", "back", "high"], stderr=subprocess.DEVNULL)
print("rendered")
