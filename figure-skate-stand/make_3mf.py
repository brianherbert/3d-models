#!/usr/bin/env python3
"""
Build the Bambu Studio project:

    figure_skate_stand.3mf    the stand (white PLA), groove up

    python3 make_3mf.py      (from this folder, after build.py and render.py)

Uses ../tools/bambu3mf.py.
"""
import os, sys
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from bambu3mf import Part, write_project, BED

PROCESS = "0.20mm Standard @BBL A1"
STAND = {
    "brim_type": "no_brim",             # wide and flat
    "enable_support": "0",              # the groove is open at the top: nothing overhangs
    "wall_loops": "3",
    "sparse_infill_density": "15%",
}

def main():
    c = BED / 2
    stand = trimesh.load(os.path.join(HERE, "stl", "stand.stl"))
    out = write_project(os.path.join(HERE, "figure_skate_stand.3mf"), [Part("stand", stand, c, c)],
                        PROCESS, STAND, title="Figure skate stand",
                        description="A round stand for one figure skate. Print in white PLA, groove up.",
                        thumbnail_png=os.path.join(HERE, "images", "stand_blade.png"),
                        filament_colour="#F2F0E6")
    print("wrote", out)

if __name__ == "__main__":
    main()
