#!/usr/bin/env python3
"""
Build the Bambu Studio projects, one plate per filament:

    crystal_base.3mf    the base (white PLA)
    crystal_top.3mf     the crystal (translucent blue PLA)

    python3 make_3mf.py      (from this folder, after build_crystal.py and render.py)

Uses ../tools/bambu3mf.py.
"""
import os, sys
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from bambu3mf import Part, write_project, BED

PROCESS = "0.20mm Standard @BBL A1"
BASE = {
    "brim_type": "no_brim",             # wide and flat
    "enable_support": "0",
    "wall_loops": "3",
    "sparse_infill_density": "15%",
    "seam_position": "aligned",
}
# The crystal is modelled as a 0.9 mm shell: exactly two lines of wall.
# Arachne keeps it two lines where the sloped roof is a little wider.
# 'aligned' tucks the seam into one of the crystal's vertical corners.
CRYSTAL = {
    "brim_type": "outer_only",          # tall and narrow on a thin foot: the brim keeps it down
    "brim_width": "5",                  # (the foot hides in the socket, so the brim edge never shows)
    "enable_support": "0",              # every roof facet is 50 degrees or steeper
    "wall_loops": "2",
    "sparse_infill_density": "0%",
    "wall_generator": "arachne",
    "seam_position": "aligned",
}

def load(name):
    return trimesh.load(os.path.join(HERE, "stl", name + ".stl"))

def main():
    c = BED / 2
    out = write_project(os.path.join(HERE, "crystal_base.3mf"), [Part("base", load("base"), c, c)],
                        PROCESS, BASE, title="Tea Light Crystal: base",
                        description="The base. Print in white PLA.",
                        thumbnail_png=os.path.join(HERE, "images", "crystal_open.png"),
                        filament_colour="#F2F0E6")
    print("wrote", out)
    out = write_project(os.path.join(HERE, "crystal_top.3mf"), [Part("crystal", load("crystal"), c, c)],
                        PROCESS, CRYSTAL, title="Tea Light Crystal: crystal",
                        description="The crystal. Print in translucent blue PLA.",
                        thumbnail_png=os.path.join(HERE, "images", "crystal_lit.png"),
                        filament_colour="#4F8FE0")
    print("wrote", out)

if __name__ == "__main__":
    main()
