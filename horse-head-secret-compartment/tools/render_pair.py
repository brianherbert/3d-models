#!/usr/bin/env python3
"""Render a reference scan (transformed into the sculpt's head frame and
scale) next to the sculpt's head, from identical cameras.

    python3 tools/render_pair.py <ref_head.npz> <ref_mesh_in_ref_frame.stl> <my_head.stl> <out_prefix>
"""
import sys, os, subprocess, numpy as np, trimesh
from PIL import Image

ref = np.load(sys.argv[1])
refm = trimesh.load(sys.argv[2])
mine = trimesh.load(sys.argv[3])
pref = sys.argv[4]
tip = ref["tip_mine"]; Lt = np.linalg.norm(tip)
# reference vertices -> reference head frame (normalised) -> my head frame
poll, Rh, Lr = ref["poll"], ref["Rh"], float(ref["Lr"])
q = ((refm.vertices - poll) @ Rh) / Lr
a = np.arctan2(-tip[2], tip[1]); c, s = np.cos(a), np.sin(a)
Rm = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
qm = (q * Lt) @ Rm                                  # inverse of the rotation used in compare_ref
refm.vertices = qm
# keep only the head and upper neck
keep = np.all(refm.vertices[refm.faces][:, :, 1] > -40, axis=1)
refm = refm.submesh([np.where(keep)[0]], append=True)
rp = os.path.abspath(pref + "_ref.stl"); refm.export(rp)
mp = os.path.abspath(sys.argv[3])
center = "45,-14"   # look-at point (y, z) in the head frame
views = {"side": ("300,45,-14", "0,45,-14"), "front": ("0,300,-30", "0,45,-14"),
         "threeq": ("200,230,40", "0,45,-14"), "top": ("0,45,300", "0,45,-14"), "below": ("150,120,-250", "0,45,-14")}
for v, (eye, ctr) in views.items():
    tiles = []
    for tag, path, col in (("ref", rp, "LightGrey"), ("mine", mp, "Tan")):
        open("/tmp/claude-0/rp.scad", "w").write(f'color("{col}") import("{path}");')
        out = f"/tmp/claude-0/rp_{tag}.png"
        subprocess.run(["xvfb-run", "-a", "openscad", "-o", out, f"--camera={eye},{ctr}", "--projection=o",
                        "--imgsize=700,600", "--colorscheme=Tomorrow", "/tmp/claude-0/rp.scad"], capture_output=True)
        tiles.append(Image.open(out))
    W = Image.new("RGB", (1400, 600), "white"); W.paste(tiles[0], (0, 0)); W.paste(tiles[1], (700, 0))
    W.save(f"{pref}_{v}.png")
print("done")
