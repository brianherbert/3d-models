#!/usr/bin/env python3
"""Section images straight from the saved body/jaw fields.  python3 tools/fieldsec.py out.png x1 x2 ..."""
import sys, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
F = np.load("/tmp/claude-0/horse_fields.npz")
xs, ys, zs = F["xs"], F["ys"], F["zs"]
X = [float(v) for v in sys.argv[2:]]
fig, axs = plt.subplots(1, len(X), figsize=(7 * len(X), 8)); axs = np.atleast_1d(axs)
for ax, x in zip(axs, X):
    i = np.argmin(np.abs(xs - x))
    img = np.ones((len(zs), len(ys), 3))
    img[F["B"][i].T < 0] = (0.85, 0.72, 0.52); img[F["J"][i].T < 0] = (0.35, 0.55, 0.80)
    ax.imshow(img, origin="lower", extent=[ys[0], ys[-1], zs[0], zs[-1]])
    ax.set_xlim(-25, 55); ax.set_ylim(50, 150); ax.set_title(f"x = {xs[i]:.1f}"); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig(sys.argv[1], dpi=70)
