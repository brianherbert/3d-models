#!/usr/bin/env python3
"""Overlay the sculpt's head silhouettes on a reference scan's, both in a
head frame (poll at the origin, +y toward the front of the upper lip,
length normalised to 1).  Used only as a proportion reference.

    python3 tools/compare_ref.py <reference_head_frame.npz> <my_head.stl> out.png
"""
import sys, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ref = np.load(sys.argv[1])
rq = ref["q"]                                   # reference vertices, head frame, units of L
mine = trimesh.load(sys.argv[2])
L = float(ref["L_mine"]); tip = ref["tip_mine"]  # my poll->tip vector (mm)
# rotate my head so poll->tip lies on +y, then normalise
a = np.arctan2(-tip[2], tip[1])
c, s = np.cos(a), np.sin(a)
Rm = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
mq = (mine.vertices @ Rm.T) / np.linalg.norm(tip)

def sil(ax, P, i, j, color, label, dots=False):
    if dots:
        ax.scatter(P[:, i], P[:, j], s=0.3, c=color, alpha=0.35, label=label)
    else:
        # outline: extreme points per bin along the horizontal axis
        b = np.round(P[:, i] / 0.01).astype(int)
        u = np.unique(b)
        hi = [P[b == k, j].max() for k in u]; lo = [P[b == k, j].min() for k in u]
        ax.plot(u * 0.01, hi, color=color, lw=1.6, label=label); ax.plot(u * 0.01, lo, color=color, lw=1.6)

fig, axs = plt.subplots(1, 3, figsize=(18, 6))
win = (rq[:, 1] > -0.25) & (rq[:, 1] < 1.1) & (rq[:, 2] > -0.75) & (rq[:, 2] < 0.45)
for ax, (i, j, t) in zip(axs, [(1, 2, "side (y right, z up)"), (1, 0, "top (y right, x up)"), (0, 2, "front (x right, z up)")]):
    sil(ax, rq[win], i, j, "grey", "reference scan", dots=True)
    sil(ax, mq, i, j, "red", "sculpt")
    ax.set_aspect("equal"); ax.set_title(t); ax.grid(alpha=0.3)
axs[0].legend(loc="lower left")
plt.tight_layout(); plt.savefig(sys.argv[3], dpi=80)
print("wrote", sys.argv[3])
