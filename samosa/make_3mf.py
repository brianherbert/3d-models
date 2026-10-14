#!/usr/bin/env python3
"""
Build the Bambu Studio projects, one plate and one filament each (no AMS):

    samosa.3mf              the samosa, golden-brown PLA
    samosa_dip_cup.3mf      the dipping cup, white PLA
    samosa_dip_sauce.3mf    the sauce, red PLA

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
    "seam_position": "aligned",         # one tidy seam line on the smooth pastry
}

CUP = {
    "brim_type": "no_brim",
    "enable_support": "0",              # the lip's underside is the steepest part, under 40 degrees
    "wall_loops": "4",                  # the 2.2 mm wall prints solid
    "sparse_infill_density": "15%",
    "seam_position": "aligned",
}
SAUCE = {
    "brim_type": "no_brim",
    "enable_support": "0",
    "wall_loops": "3",
    "sparse_infill_density": "15%",
    "seam_position": "aligned",
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
    for name, title, settings, colour, what in (
            ("dip_cup", "dipping cup", CUP, "#F2F0E6", "The dipping cup. Print in white PLA."),
            ("dip_sauce", "sauce", SAUCE, "#B8241C", "The sauce. Print in red PLA and drop it into the cup.")):
        mesh = trimesh.load(os.path.join(HERE, "stl", name + ".stl"))
        out = write_project(os.path.join(HERE, "samosa_" + name + ".3mf"), [Part(name, mesh, c, c)],
                            PROCESS, settings, title="Samosa: " + title,
                            description=what, thumbnail_png=os.path.join(HERE, "images", "dip.png"),
                            filament_colour=colour)
        print("wrote", out)

if __name__ == "__main__":
    main()
