#!/usr/bin/env python3
"""Visible (outer-skin) steep overhang area per part of the built model."""
import sys, os, warnings; warnings.filterwarnings("ignore")
import numpy as np, trimesh
from scipy.cluster.hierarchy import fcluster, linkage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import horse_sculpt as S
S.anchors(); S.locks()
for nm in ("body", "jaw"):
    m = trimesh.load(f"stl/preview_{nm}.stl"); n = m.face_normals; c = m.triangles_center; a = m.area_faces
    over = np.degrees(np.arcsin(np.clip(-n[:, 2], 0, 1)))
    k = (over > 50) & (c[:, 2] > 10)
    sk = np.abs(S.sculpt(c[k])) < 0.35
    p, w, o = c[k][sk], a[k][sk], over[k][sk]
    # faces resting on a pillar pad are supported
    import build_horse as B
    st = np.load("stl/.struts.npy")
    onpad = np.min([np.hypot(p[:, 0] - s[0], p[:, 1] - s[1]) for s in st], axis=0) < B.PAD_R - 0.5
    print(f"  ({w[onpad].sum():.0f} mm2 of it sits on the pillar pads and is excluded)")
    p, w, o = p[~onpad], w[~onpad], o[~onpad]
    print(f"{nm}: >50 {w.sum():.0f}  >60 {w[o > 60].sum():.0f}  >70 {w[o > 70].sum():.0f} mm2")
    if len(p) > 1:
        lab = fcluster(linkage(p, "single"), 2.0, "distance")
        for l in sorted(np.unique(lab), key=lambda l: -w[lab == l].sum())[:6]:
            s = lab == l
            if w[s].sum() < 5: break
            print(f"   {w[s].sum():5.0f} mm2 (>60: {w[s & (o > 60)].sum():4.0f})  at {np.round(p[s].mean(0), 1)}")
