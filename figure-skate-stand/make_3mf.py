#!/usr/bin/env python3
"""
Build the Bambu Studio projects, set up for a display-quality finish:

    figure_skate_stand.3mf          the stand, 2 in tall (white PLA), groove up
    figure_skate_stand_short.3mf    the short stand, 1 in tall
    figure_skate_stand_3in.3mf          the same two, 3 in across
    figure_skate_stand_3in_short.3mf

    python3 make_3mf.py      (from this folder, after build.py and render.py)

Uses ../tools/bambu3mf.py.
"""
import os, sys
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from bambu3mf import Part, write_project, BED

# Fine layers so the sides show almost no layer lines.
PROCESS = "0.12mm Fine @BBL A1"
STAND = {
    "brim_type": "no_brim",             # wide and flat
    "enable_support": "0",              # the groove is open at the top: nothing overhangs
    # The seam goes at the back of the plate. The part is turned so the groove
    # runs front to back, which puts the seam right under one end of the
    # blade, and the scarf joint blends it in.
    "seam_position": "back",
    "seam_slope_type": "external",      # "Scarf joint seam: Contour"
    # White PLA lets light through: thick walls and top so the infill
    # pattern can't show.
    "wall_loops": "4",
    "top_shell_thickness": "1.2",
    "top_shell_layers": "10",
    "sparse_infill_density": "15%",
    "sparse_infill_pattern": "gyroid",
    # Slow, gentle outer wall for an even surface.
    "outer_wall_speed": ["80"],
    "outer_wall_acceleration": ["2000"],
    # Iron the top face (only the very top, not the groove floor).
    "ironing_type": "topmost",
}

def main():
    c = BED / 2
    for stl, out_name, title, height, thumb in (
            ("stand", "figure_skate_stand", "Figure skate stand", "2 in", "stand_blade"),
            ("stand_short", "figure_skate_stand_short", "Figure skate stand (short)", "1 in", "stand_short"),
            ("stand_3in", "figure_skate_stand_3in", "Figure skate stand (3 in)", "3 in across and 2 in", "stand_3in"),
            ("stand_3in_short", "figure_skate_stand_3in_short", "Figure skate stand (3 in, short)",
             "3 in across and 1 in", "stand_3in_short")):
        stand = trimesh.load(os.path.join(HERE, "stl", stl + ".stl"))
        # rot_z=90 turns the groove (along X in the STL) to run front to back
        out = write_project(os.path.join(HERE, out_name + ".3mf"), [Part(stl, stand, c, c, rot_z=90)],
                            PROCESS, STAND, title=title,
                            description=f"A round stand for one figure skate, {height} tall. Print in white PLA, groove up. "
                                        "Set up for a display finish: fine layers, seam hidden under the blade, ironed top.",
                            thumbnail_png=os.path.join(HERE, "images", thumb + ".png"),
                            filament_colour="#F2F0E6")
        print("wrote", out)

if __name__ == "__main__":
    main()
