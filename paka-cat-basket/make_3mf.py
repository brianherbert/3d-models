#!/usr/bin/env python3
"""
Build the Bambu Studio project: the basket on one A1 plate, one filament (no AMS).

    paka_basket.3mf

    python3 make_3mf.py      (from this folder, after build_basket.py and render.py)

Uses ../tools/bambu3mf.py.
"""
import os, sys
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from bambu3mf import Part, write_project, BED

PROCESS = "0.20mm Standard @BBL A1"
BASKET = {
    "brim_type": "no_brim",             # the solid base band and floor hold it down
    "enable_support": "0",              # the build script checks nothing overhangs more than 45 degrees
    "wall_loops": "3",                  # the 2 mm reeds print as solid walls
    "wall_generator": "arachne",        # varying-width walls follow the reeds where they cross
    "bottom_shell_layers": "6",         # the 1.2 mm floor prints solid
    "sparse_infill_density": "15%",     # only the rim, base band and plaque have infill
    "seam_position": "back",            # seams on the back wall, away from the plaque
    "reduce_crossing_wall": "1",        # fewer travel marks across the open weave
}


def main():
    c = BED / 2
    mesh = trimesh.load(os.path.join(HERE, "stl", "basket.stl"))
    out = write_project(os.path.join(HERE, "paka_basket.3mf"), [Part("paka_basket", mesh, c, c)],
                        PROCESS, BASKET, title="Paka's basket",
                        description="A woven countertop basket for cat supplies, with a paw print and Paka on the front. "
                                    "One piece, one colour, no supports.",
                        thumbnail_png=os.path.join(HERE, "images", "basket_empty.png"),
                        filament_colour="#C9A877")
    print("wrote", out)


if __name__ == "__main__":
    main()
