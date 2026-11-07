#!/usr/bin/env python3
"""
Build the Bambu Studio projects, set up for a display-quality finish:

    figure_skate_stand.3mf          the stand, 2 in tall (white PLA), groove up
    figure_skate_stand_short.3mf    the short stand, 1 in tall
    figure_skate_stand_3in.3mf          the same two, 3 in across
    figure_skate_stand_3in_short.3mf
    gingerbread_skate_stand.3mf         the gingerbread man, 2 in tall
    gingerbread_skate_stand_short.3mf   and 1 in tall
    standing_gingerbread.3mf            the standing gingerbread man who holds the back of the blade

    python3 make_3mf.py      (from this folder, after build.py, gingerbread.py,
                              standing_gingerbread.py and render.py)

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

ROUND = "A round stand for one figure skate, {} tall."
GINGER = "A gingerbread man that holds up the back of a figure skate, {} tall."

def main():
    c = BED / 2
    # rot_z turns the groove to run front to back: the round stands' groove
    # is along X in the STL, the gingerbread man's along Y already (head at
    # the back, so the seam goes up through his head, under the blade).
    for stl, out_name, title, what, thumb, rot in (
            ("stand", "figure_skate_stand", "Figure skate stand", ROUND.format("2 in"), "stand_blade", 90),
            ("stand_short", "figure_skate_stand_short", "Figure skate stand (short)", ROUND.format("1 in"), "stand_short", 90),
            ("stand_3in", "figure_skate_stand_3in", "Figure skate stand (3 in)",
             ROUND.format("3 in across and 2 in"), "stand_3in", 90),
            ("stand_3in_short", "figure_skate_stand_3in_short", "Figure skate stand (3 in, short)",
             ROUND.format("3 in across and 1 in"), "stand_3in_short", 90),
            ("gingerbread", "gingerbread_skate_stand", "Gingerbread skate stand",
             GINGER.format("2 in"), "gingerbread_blade", 0),
            ("gingerbread_short", "gingerbread_skate_stand_short", "Gingerbread skate stand (short)",
             GINGER.format("1 in"), "gingerbread_short", 0),
            # his back faces +Y (the back of the plate), so the seam goes down his back
            ("standing_gingerbread", "standing_gingerbread", "Standing gingerbread man",
             "A gingerbread man who stands behind a figure skate and holds the back tip of its blade "
             "(the skate's middle sits in the 1 in round stand).", "standing", 0)):
        stand = trimesh.load(os.path.join(HERE, "stl", stl + ".stl"))
        out = write_project(os.path.join(HERE, out_name + ".3mf"), [Part(stl, stand, c, c, rot_z=rot)],
                            PROCESS, STAND, title=title,
                            description=what + " Print in white PLA, groove up. "
                                        "Set up for a display finish: fine layers, seam hidden under the blade, ironed top.",
                            thumbnail_png=os.path.join(HERE, "images", thumb + ".png"),
                            filament_colour="#F2F0E6")
        print("wrote", out)

if __name__ == "__main__":
    main()
