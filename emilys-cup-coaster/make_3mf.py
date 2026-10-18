#!/usr/bin/env python3
"""
Build the Bambu Studio projects, one per design, each on two AMS filaments
(the base on filament 1, the letters on filament 2):

    emilys_cup_tab.3mf          white with pink letters
    emilys_cup_arch.3mf         lilac with white letters
    emilys_cup_nameplate.3mf    mint with white letters

    python3 make_3mf.py      (from this folder, after build.py and render.py)

Uses ../tools/bambu3mf.py.
"""
import os, sys
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from bambu3mf import Part, write_project, BED

PROCESS = "0.20mm Standard @BBL A1"
SETTINGS = {
    "brim_type": "no_brim",             # it lies on a wide flat bottom
    "enable_support": "0",              # nothing overhangs more than 45 degrees
    "wall_loops": "3",
    "sparse_infill_density": "15%",
    "flush_into_infill": "1",           # purge between colours goes into the base's infill
}
DESIGNS = [
    ("tab", "round with a name tab", ["#F4F2EC", "#E0508C"], "white", "pink"),
    ("arch", "the name round the rim", ["#BDA8E2", "#F4F4F0"], "lilac", "white"),
    ("nameplate", "with a sloped nameplate", ["#8ECFC9", "#F4F4F0"], "mint", "white"),
]


def main():
    c = BED / 2
    load = lambda n: trimesh.load(os.path.join(HERE, "stl", n + ".stl"))
    for name, what, colours, base, ink in DESIGNS:
        part = Part(name, load(name), c, c, extra=[(name + "_text", load(name + "_text"), 2)])
        out = write_project(os.path.join(HERE, f"emilys_cup_{name}.3mf"), [part], PROCESS, SETTINGS,
                            title=f"Emily's Cup: {what}",
                            description=f"Load {base} PLA as filament 1 and {ink} as filament 2.",
                            thumbnail_png=os.path.join(HERE, "images", name + ".png"), filament_colour=colours)
        print("wrote", out)


if __name__ == "__main__":
    main()
