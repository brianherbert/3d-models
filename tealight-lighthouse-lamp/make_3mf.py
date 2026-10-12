#!/usr/bin/env python3
"""
Build the Bambu Studio projects, one per filament:

    lighthouse_white.3mf     tower and roof, side by side (opaque PLA)
    lighthouse_lantern.3mf   the lantern (translucent blue PLA)

    python3 make_3mf.py      (from this folder, after build_lighthouse.py and render.py)

Uses ../tools/bambu3mf.py.
"""
import os, sys
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from bambu3mf import Part, write_project, BED

PROCESS = "0.20mm Standard @BBL A1"
COMMON = {
    "brim_type": "no_brim",             # every part stands on a wide flat ring or disc
    "enable_support": "0",              # all overhangs are 45 degrees or short bridges
    "seam_position": "back",
}
OPAQUE = dict(COMMON, **{"wall_loops": "3", "sparse_infill_density": "10%"})
# four walls fill the whole 1.6 mm glass, so there is no infill pattern to
# show through when it is lit
LANTERN = dict(COMMON, **{"wall_loops": "4", "sparse_infill_density": "0%",
                          "top_shell_layers": "0", "bottom_shell_layers": "4"})

def load(name):
    return trimesh.load(os.path.join(HERE, "stl", name + ".stl"))

def main():
    thumb = os.path.join(HERE, "images", "lighthouse.png")
    c = BED / 2
    out = write_project(os.path.join(HERE, "lighthouse_white.3mf"),
                        [Part("tower", load("tower"), c - 40, c), Part("roof", load("roof"), c + 45, c)],
                        PROCESS, OPAQUE, title="Tea Light Lighthouse: tower and roof",
                        description="Tower and roof. Print in white (or any opaque colour).",
                        thumbnail_png=thumb, filament_colour="#F2F0E6")
    print("wrote", out)
    out = write_project(os.path.join(HERE, "lighthouse_lantern.3mf"),
                        [Part("lantern", load("lantern"), c, c)],
                        PROCESS, LANTERN, title="Tea Light Lighthouse: lantern",
                        description="The lantern room. Print in translucent blue PLA.",
                        thumbnail_png=os.path.join(HERE, "images", "lighthouse_lit.png"),
                        filament_colour="#4F8FE0")
    print("wrote", out)

if __name__ == "__main__":
    main()
