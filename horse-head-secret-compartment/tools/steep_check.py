#!/usr/bin/env python3
"""Steep downward skin area of the plain sculpt in a world box (no mechanism).
    python3 tools/steep_check.py [res] [x0 x1 y0 y1 z0 z1]"""
import sys, os, numpy as np, trimesh
from skimage import measure
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import horse_sculpt as S
res = float(sys.argv[1]) if len(sys.argv) > 1 else 0.4
b = [float(v) for v in sys.argv[2:8]] if len(sys.argv) > 7 else [-30, 30, -35, 25, 85, 125]
xs = np.arange(b[0] + 0.37 * res, b[1], res); ys = np.arange(b[2] + 0.37 * res, b[3], res); zs = np.arange(b[4] + 0.37 * res, b[5], res)
S.anchors(); S.locks()
X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
F = S.sculpt(np.c_[X.ravel(), Y.ravel(), Z.ravel()]).reshape(X.shape)
v, f, _, _ = measure.marching_cubes(F, 0.0, spacing=(res,) * 3)
m = trimesh.Trimesh(v + [xs[0], ys[0], zs[0]], f)
c = m.triangles_center; n = m.face_normals; a = m.area_faces
inner = np.all((c > np.array(b[::2]) + 1) & (c < np.array(b[1::2]) - 1), axis=1)
over = np.degrees(np.arcsin(np.clip(-n[:, 2], 0, 1)))
for lim in (45, 50, 60, 70):
    print(f">{lim}: {a[inner & (over > lim)].sum():6.0f} mm2", end="  ")
print()
k = inner & (over > 50)
for lo, hi in ((-35, -10), (-10, 0), (0, 25)):
    s = k & (c[:, 1] >= lo) & (c[:, 1] < hi)
    print(f"  y {lo:4d}..{hi:3d}: {a[s].sum():5.0f} mm2" + (f"  z {c[s, 2].min():.0f}-{c[s, 2].max():.0f}" if s.any() else ""))
m.export("/tmp/claude-0/steep_region.stl")
