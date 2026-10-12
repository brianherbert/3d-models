#!/usr/bin/env python3
"""
Build box_cab_locomotive.3mf: a Bambu Studio project with every printed part
of the default build on one A1 plate, the print settings from the README
and the pause for the coupler magnets already set.  Also writes
box_cab_locomotive_roof.3mf with just the roof hatch, for reprinting it.

    python3 make_3mf.py        (from this folder, after exporting the STLs)

Uses ../tools/bambu3mf.py.
"""
import math, os, sys, subprocess, tempfile
import numpy as np, trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from bambu3mf import Part, write_project, BED

PROCESS = "0.20mm Standard @BBL A1"
LAYER, FIRST_LAYER = 0.2, 0.2
PROCESS_CHANGES = {
    "wall_loops": "3",
    "sparse_infill_density": "20%",
    "brim_type": "no_brim",          # only the body gets a brim (per-object below)
    "enable_support": "0",           # everything prints without supports
}
SOLID = {"sparse_infill_density": "100%"}          # wheels and axle: small, stiff, press-fit
BODY = {"brim_type": "outer_only", "brim_width": "5"}   # the body stands on the thin rim of its walls
# the roof prints the right way up: slicer supports from the plate under its
# deck (2 mm tall, they peel off), no brim to leave burrs on the locating rails
ROOF = {"enable_support": "1", "support_type": "normal(auto)", "support_on_build_plate_only": "1"}

def scad_value(name):
    """read a value the model echoes, so the pause follows the design"""
    with tempfile.TemporaryDirectory() as tmp:
        echo = os.path.join(tmp, "loco.echo")
        subprocess.run(["openscad", "-o", echo, os.path.join(HERE, "box_cab_locomotive.scad")], capture_output=True)
        out = open(echo).read()
    for line in out.splitlines():
        if name in line:
            return float(line.split(name)[1].split()[0])
    raise SystemExit(f"could not read {name} from the model")

def load(name):
    return trimesh.load(os.path.join(HERE, "stl", name + ".stl"))

def main():
    pocket_top = scad_value("add a pause at layer height")         # print height of the magnet pockets' top
    pause = FIRST_LAYER + math.ceil((pocket_top - FIRST_LAYER) / LAYER - 1e-9) * LAYER
    cx = BED / 2
    parts = [
        Part("body", load("body"), cx, 175, settings=BODY),
        Part("hatch", load("hatch"), cx, 131, settings=ROOF),
        Part("wheel_front_1", load("wheel"), cx - 49.5, 92, settings=SOLID),
        Part("wheel_front_2", load("wheel"), cx - 16.5, 92, settings=SOLID),
        Part("wheel_drive_1", load("wheel_drive_oring"), cx + 16.5, 92, settings=SOLID),
        Part("wheel_drive_2", load("wheel_drive_oring"), cx + 49.5, 92, settings=SOLID),
        Part("axle", load("axle"), cx, 66, settings=SOLID),
    ]
    out = write_project(os.path.join(HERE, "box_cab_locomotive.3mf"), parts, PROCESS, PROCESS_CHANGES,
                        pauses=[round(pause, 3)],
                        title="Battery Box-Cab Locomotive (Brio-compatible)",
                        description="Body, hatch, wheels and axle on one plate. Pauses for the coupler magnets.",
                        thumbnail_png=os.path.join(HERE, "images", "loco_iso.png"),
                        filament_colour="#2E6DB4")
    print(f"wrote {out}: magnet pause before the layer at {pause:.2f} mm (pocket top {pocket_top} mm)")
    # the roof on its own, for reprinting just the hatch
    out = write_project(os.path.join(HERE, "box_cab_locomotive_roof.3mf"),
                        [Part("hatch", load("hatch"), cx, BED / 2, settings=ROOF)], PROCESS, PROCESS_CHANGES,
                        title="Battery Box-Cab Locomotive: steam roof",
                        description="The roof (smoke stack, boiler and cab) on its own, to reprint it without the body.",
                        thumbnail_png=os.path.join(HERE, "images", "loco_iso.png"),
                        filament_colour="#2E6DB4")
    print(f"wrote {out}")

if __name__ == "__main__":
    main()
