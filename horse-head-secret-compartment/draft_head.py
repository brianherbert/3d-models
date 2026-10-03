#!/usr/bin/env python3
"""Mesh the head alone in the head frame (nose along +y, top +z) and render
side / front / three-quarter views.  python3 draft_head.py [res] [name]"""
import sys, time, os, numpy as np, trimesh, subprocess
from skimage import measure
import horse_sculpt as S
res = float(sys.argv[1]) if len(sys.argv) > 1 else 0.8
name = sys.argv[2] if len(sys.argv) > 2 else "head"
L = S.L
xs = np.arange(-0.32 * L + 0.37 * res, 0.32 * L, res)
ys = np.arange(-0.15 * L + 0.37 * res, 1.06 * L, res)
zs = np.arange(-0.45 * L + 0.37 * res, 0.38 * L, res)
S.anchors()
def field(Ph):
    return S.head_field(Ph)
out = np.empty((len(xs), len(ys), len(zs)), np.float32)
X, Y = np.meshgrid(xs, ys, indexing="ij")
for k0 in range(0, len(zs), 16):
    z = zs[k0:k0 + 16]
    P = np.c_[np.repeat(X[..., None], len(z), 2).ravel(), np.repeat(Y[..., None], len(z), 2).ravel(),
              np.broadcast_to(z, X.shape + (len(z),)).ravel()]
    out[:, :, k0:k0 + len(z)] = field(P).reshape(len(xs), len(ys), len(z))
v, f, _, _ = measure.marching_cubes(out, 0.0, spacing=(res, res, res))
v += [xs[0], ys[0], zs[0]]
m = trimesh.Trimesh(v, f)
m = trimesh.util.concatenate([p for p in m.split(only_watertight=False) if abs(p.volume) > 20])
m.export(f"stl/_{name}.stl")
open("/tmp/claude-0/dh.scad", "w").write(f'color("Tan") import("{os.path.abspath(f"stl/_{name}.stl")}");')
for vname, cam in [("side", "90,0,90"), ("front", "90,0,180"), ("threeq", "75,0,125"), ("top", "0,0,90"), ("below", "130,0,110")]:
    subprocess.run(["xvfb-run", "-a", "openscad", "-o", f"images/_{name}_{vname}.png", f"--camera=0,0,0,{cam},350",
                    "--viewall", "--autocenter", "--imgsize=900,700", "--colorscheme=Tomorrow", "/tmp/claude-0/dh.scad"], capture_output=True)
print("done", np.round(m.bounds, 1).tolist())
