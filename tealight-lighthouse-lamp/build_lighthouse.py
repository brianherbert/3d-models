#!/usr/bin/env python3
"""
A small lighthouse lamp for one LED tea light (Bambu Lab LED Flame Tea Light,
37.2 mm across, 36.6 mm tall including the flame).

Three parts, all printed upright with no supports:

    tower     opaque.  Plinth, tapered tower, gallery deck with railing, and
              a pocket on top that the tea light drops into
    lantern   translucent blue.  The glass room around the flame
    roof      opaque.  Cone roof with a ventilator ball; plugs into the lantern

    python3 build_lighthouse.py            -> stl/tower.stl, lantern.stl, roof.stl, assembled.stl

To switch the tea light on or off (its switch is underneath) lift the roof and
lantern off and pull the tea light out by its body.
"""
import math, os
import numpy as np, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = 160

# ---------------------------------------------------------------- tea light
TEA_D, TEA_H = 37.2, 36.6
POCKET_R = TEA_D / 2 + 0.5          # 0.5 mm all round: drops in and lifts out freely
POCKET_DEPTH = 9.0                  # holds it upright; the top 27 mm stands clear to grab

# ---------------------------------------------------------------- tower
PLINTH_R, PLINTH_H = 36.0, 4.0
TOWER_R0, TOWER_R1 = 33.0, 24.0     # radius at the bottom and at the top of the taper
TOWER_H = 72.0                      # top of the taper
DECK_R = 30.0                       # gallery; the corbel flares out to it at 45 degrees
DECK_T = 2.0
WALL = 2.4                          # the tower is hollow and open underneath
RING_R, RING_H = 21.0, 2.0          # locating ring the lantern sits over
RAIL_H, POSTS, POST_W, RAIL_T = 6.0, 16, 1.6, 1.2

# ---------------------------------------------------------------- lantern and roof
FIT = 0.4                           # radial clearance on each spigot
LANT_RO = 23.0
LANT_RI = RING_R + FIT              # 1.6 mm wall: thin enough to glow evenly
LANT_H = 42.0
BAND_R, BAND_H = 23.8, 4.0          # thicker band top and bottom
MULLIONS, MULL_W, MULL_D = 8, 1.6, 0.8
SPIGOT_H = 3.0
EAVE_R = 26.0

CORBEL_TOP = TOWER_H + (DECK_R - TOWER_R1)
DECK_TOP = CORBEL_TOP + DECK_T
RING_TOP = DECK_TOP + RING_H
POCKET_FLOOR = RING_TOP - POCKET_DEPTH

def revolve(profile):
    """profile: (r, z) points, counter-clockwise, r >= 0"""
    return mf.Manifold.revolve(mf.CrossSection([profile]), SEG)

def cyl(r, z0, z1, seg=SEG):
    return mf.Manifold.cylinder(z1 - z0, r, r, seg).translate([0, 0, z0])

def box(sx, sy, sz, centre):
    return mf.Manifold.cube([sx, sy, sz], True).translate(list(centre))

def tower_radius(z):
    return TOWER_R0 + (TOWER_R1 - TOWER_R0) * (z - PLINTH_H) / (TOWER_H - PLINTH_H)

def arch_recess(width, height, depth, z0, angle):
    """An arched window or door sunk into the tapered wall, facing `angle`
    (degrees, 0 = -Y, the front).  Tilted with the wall so it is equally
    deep top to bottom."""
    r = width / 2
    shape = mf.CrossSection.square([width, height - r]).translate([-r, 0]) + \
        mf.CrossSection.circle(r, 48).translate([0, height - r])
    # extruded along +Z, then stood up so the opening faces -Y
    m = shape.extrude(depth + 4).translate([0, 0, -depth]).rotate([90, 0, 0])
    slope = math.degrees(math.atan((TOWER_R0 - TOWER_R1) / (TOWER_H - PLINTH_H)))
    m = m.rotate([-slope, 0, 0])                                # lean back with the wall
    rz = tower_radius(z0)
    m = m.translate([0, -rz, z0])
    return m.rotate([0, 0, angle])

def tower():
    taper = revolve([(0, 0), (PLINTH_R, 0), (PLINTH_R, PLINTH_H - 1.5),
                     (TOWER_R0 + 0.5, PLINTH_H), (TOWER_R0, PLINTH_H),
                     (TOWER_R1, TOWER_H), (DECK_R, CORBEL_TOP), (DECK_R, DECK_TOP), (0, DECK_TOP)])
    body = taper + cyl(RING_R, DECK_TOP - 0.01, RING_TOP)
    # hollow inside, closing at 45 degrees well below the pocket floor
    floor = POCKET_FLOOR - 2.0
    zc = PLINTH_H
    rc = None
    # find the height where the inner wall meets a 45-degree cone up to `floor`
    for i in range(2000):
        z = PLINTH_H + i * 0.05
        ri = tower_radius(z) - WALL
        if z + ri >= floor:
            zc, rc = z, ri
            break
    cavity = revolve([(0, -1), (PLINTH_R - WALL - 1.5, -1), (PLINTH_R - WALL - 1.5, 0.01),
                      (TOWER_R0 - WALL, PLINTH_H), (rc, zc), (0, zc + rc)])
    body = body - cavity
    body = body - cyl(POCKET_R, POCKET_FLOOR, RING_TOP + 1)
    # railing: posts and a top rail
    rp = DECK_R - POST_W / 2 - 0.2
    for k in range(POSTS):
        a = 360 * k / POSTS
        body = body + box(POST_W, POST_W, RAIL_H, (0, 0, 0)).translate([rp, 0, DECK_TOP + RAIL_H / 2 - 0.01]).rotate([0, 0, a])
    rail = cyl(DECK_R - 0.2, DECK_TOP + RAIL_H - RAIL_T, DECK_TOP + RAIL_H) - \
        cyl(DECK_R - 0.2 - 2 * RAIL_T, DECK_TOP + RAIL_H - RAIL_T - 1, DECK_TOP + RAIL_H + 1)
    body = body + rail
    # door at the front, windows climbing round the tower
    body = body - arch_recess(11, 17, 1.6, PLINTH_H, 0)
    for z, a in ((24, 120), (40, 240), (54, 0)):
        body = body - arch_recess(6, 10, 1.4, z, a)
    return body

def lantern():
    prof = [(LANT_RI, 0), (BAND_R, 0), (BAND_R, BAND_H), (LANT_RO, BAND_H + 0.8),
            (LANT_RO, LANT_H - BAND_H), (BAND_R, LANT_H - BAND_H + 0.8),   # 45-degree step out to the top band
            (BAND_R, LANT_H), (LANT_RI, LANT_H)]
    m = revolve(prof)
    for k in range(MULLIONS):
        a = 360 * k / MULLIONS + 360 / MULLIONS / 2
        h = LANT_H - 2 * BAND_H
        m = m + box(MULL_D + 0.4, MULL_W, h, (LANT_RO + MULL_D / 2 - 0.2, 0, BAND_H + h / 2)).rotate([0, 0, a])
    return m

def roof():
    sp = RING_R                                   # spigot slides into the lantern bore
    ball_z, ball_r = 26.0, 5.0                    # ventilator ball on top
    t45 = ball_r * math.sqrt(0.5)
    neck = t45 - (ball_z - t45 - 21.0)            # meets the ball's 45-degree tangent
    prof = [(0, -SPIGOT_H), (sp, -SPIGOT_H), (sp, 0), (LANT_RO, 0),
            (EAVE_R, EAVE_R - LANT_RO), (EAVE_R, EAVE_R - LANT_RO + 2.0),
            (6.0, 19.0), (neck, 19.0), (neck, 21.0)]
    top = math.degrees(math.acos(1.2 / ball_r))   # where the finial leaves the ball
    for k in range(13):
        a = math.radians(-45 + (top + 45) * k / 12)
        prof.append((ball_r * math.cos(a), ball_z + ball_r * math.sin(a)))
    prof += [(1.2, 34.0), (0, 34.0)]
    return revolve(prof).translate([0, 0, SPIGOT_H])

def to_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)

def main():
    out = os.path.join(HERE, "stl")
    os.makedirs(out, exist_ok=True)
    parts = {"tower": tower(), "lantern": lantern(), "roof": roof()}
    meshes = {}
    for name, m in parts.items():
        t = to_trimesh(m)
        assert t.is_watertight and m.genus() >= 0, name
        t.export(os.path.join(out, name + ".stl"))
        meshes[name] = t
        lo, hi = t.bounds
        print(f"{name:8s} {hi[0]-lo[0]:6.1f} x {hi[1]-lo[1]:6.1f} x {hi[2]-lo[2]:6.1f} mm  "
              f"{t.volume / 1000:6.1f} cm3  genus {m.genus()}")
    # assembled, for the renders
    lant_z = DECK_TOP
    roof_z = DECK_TOP + LANT_H - SPIGOT_H
    asm = trimesh.util.concatenate([meshes["tower"],
                                    meshes["lantern"].copy().apply_translation([0, 0, lant_z]),
                                    meshes["roof"].copy().apply_translation([0, 0, roof_z])])
    asm.export(os.path.join(out, "assembled.stl"))
    print(f"lantern sits at z = {lant_z:.1f}, roof at z = {roof_z:.1f}, overall height {asm.bounds[1][2]:.1f} mm")
    print(f"tea light: pocket floor z = {POCKET_FLOOR:.1f}, top of flame z = {POCKET_FLOOR + TEA_H:.1f}, "
          f"underside of roof spigot z = {roof_z:.1f}")

if __name__ == "__main__":
    main()
