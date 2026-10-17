#!/usr/bin/env python3
"""
Build the Bambu Studio projects, one plate each.  All but the card use one
filament, so they need no AMS:

    basket.3mf          the basket and its handle, brown PLA
    apple.3mf           two apples, red PLA
    cookie.3mf          the cookie, tan PLA
    snack_bag.3mf       the bag of snacks, any bright colour
    card.3mf            the thank-you card, white with the characters in black (AMS)

    python3 make_3mf.py      (from this folder, after build_basket.py and render.py)

Uses ../tools/bambu3mf.py.
"""
import os, sys
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from bambu3mf import Part, write_project, BED

PROCESS = "0.20mm Standard @BBL A1"
COMMON = {
    "brim_type": "no_brim",
    "enable_support": "0",              # the build script checks nothing overhangs more than 45 degrees
    "wall_loops": "3",
    "sparse_infill_density": "15%",
    "seam_position": "aligned",
}
BASKET = dict(COMMON, wall_loops="4")   # the 2.2 mm wall prints solid


def load(name):
    return trimesh.load(os.path.join(HERE, "stl", name + ".stl"))


def main():
    c = BED / 2
    img = lambda n: os.path.join(HERE, "images", n + ".png")
    projects = [
        ("basket", "Snack basket: basket and handle", BASKET, "#7A4A26",
         "The basket and its handle. Print in brown PLA, then push the handle's pegs into the sockets.",
         [Part("basket", load("basket"), c - 25, c), Part("handle", load("handle"), c + 55, c, rot_z=90)],
         "basket_empty"),
        ("apple", "Snack basket: apples", COMMON, "#C12E1F", "Two apples. Print in red PLA.",
         [Part("apple", load("apple"), c - 20, c), Part("apple_2", load("apple"), c + 20, c)], "treats"),
        ("cookie", "Snack basket: cookie", COMMON, "#D9A460", "The cookie. Print in tan PLA.",
         [Part("cookie", load("cookie"), c, c)], "treats"),
        ("snack_bag", "Snack basket: bag of snacks", COMMON, "#EE731F",
         "The bag of snacks. Print in any bright PLA, lying on its flat back.",
         [Part("snack_bag", load("snack_bag"), c, c)], "treats"),
    ]
    # the card: one object with two parts, the white body on filament 1 and the
    # black characters on filament 2.  The characters are only in the top two
    # layers, so the AMS changes colour on those layers and no others.
    projects.append(
        ("card", "Snack basket: thank-you card", COMMON, ["#F4F4F0", "#1A1A1A"],
         "The thank-you card. Load white PLA as filament 1 and black PLA as filament 2.",
         [Part("card", load("card"), c, c, extra=[("card_ink", load("card_ink"), 2)])], "card"))
    for name, title, settings, colour, what, parts, thumb in projects:
        out = write_project(os.path.join(HERE, name + ".3mf"), parts, PROCESS, settings, title=title,
                            description=what, thumbnail_png=img(thumb), filament_colour=colour)
        print("wrote", out)


if __name__ == "__main__":
    main()
