#!/usr/bin/env python3
"""
Build the Bambu Studio project:

    samosa.3mf      the samosa, one plate, golden-brown PLA

    python3 make_3mf.py      (from this folder, after build_samosa.py and render.py)

Uses ../tools/bambu3mf.py.
"""
import os, sys
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from bambu3mf import Part, write_project, BED

PROCESS = "0.20mm Standard @BBL A1"
SAMOSA = {
    "brim_type": "no_brim",             # it stands on a wide flat triangle
    "enable_support": "0",              # nothing overhangs more than 40 degrees
    "wall_loops": "3",
    "sparse_infill_density": "15%",
    "seam_position": "random",          # scattered seam blobs disappear into the blistered pastry
}

def main():
    c = BED / 2
    mesh = trimesh.load(os.path.join(HERE, "stl", "samosa.stl"))
    out = write_project(os.path.join(HERE, "samosa.3mf"), [Part("samosa", mesh, c, c)],
                        PROCESS, SAMOSA, title="Samosa",
                        description="A life-size samosa. Print in golden-brown or tan PLA.",
                        thumbnail_png=os.path.join(HERE, "images", "samosa.png"),
                        filament_colour="#C98B3C")
    print("wrote", out)

if __name__ == "__main__":
    main()
