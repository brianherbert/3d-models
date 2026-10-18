#!/usr/bin/env python3
"""
Emily's Cup: three designs for a little stand to park a 70 mm cup on, with
"Emily's Cup" on it.

    tab        a round coaster with a name tab out the front, in script
    arch       a wide round coaster with the name curving round the front of the rim
    nameplate  a coaster with a sloped nameplate in front, like a desk sign

Each one is a base with a pocket the cup drops into, and raised letters that
print in a second colour.

    python3 build.py         -> stl/<design>.stl and stl/<design>_text.stl

The script stops with an error if a letter has a stroke too thin to print or
the meshes come out broken.
"""
import os
import numpy as np
import manifold3d as mf
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

# ---------------------------------------------------------------- parameters
NAME = "Emily’s Cup"      # the curly apostrophe looks right in both fonts

CUP_D = 70.0                # mm; the bottom of the cup
CLEARANCE = 1.5             # mm each side, so it drops in without fuss
POCKET_D = CUP_D + 2 * CLEARANCE
POCKET_DEPTH = 3.0          # how far the cup sits down into the base
FLOOR = 2.4                 # under the pocket
BASE_H = POCKET_DEPTH + FLOOR
POCKET_CHAMFER = 1.0        # the pocket's top edge, to guide the cup in
EDGE = 0.8                  # rounding of the base's top edge
FOOT = 0.4                  # inset of the first layers (stops elephant's foot)
LETTER_H = 1.2              # how far the letters stand up (6 layers at 0.2 mm)
MIN_STROKE = 0.8            # mm; the thinnest letter stroke that prints well with a 0.4 mm nozzle

SCRIPT_FONT = os.path.join(FONTS, "Pacifico-Regular.ttf")
ROUND_FONT = os.path.join(FONTS, "Fredoka-SemiBold.ttf")

# tab: the round part and the name tab in front of it
TAB_RIM = 8.0               # mm of rim round the pocket
TAB_W = 102.0               # the tab's width
TAB_TEXT_W = 84.0           # the name's width on the tab (its height follows)
TAB_GAP = 1.5               # between the pocket's edge and the top of the name
TAB_MARGIN = 3.5            # between the bottom of the name and the tab's front edge

# arch: the name follows the rim on a circle
ARCH_D = 122.0
ARCH_TEXT_CAP = 11.0        # height of the capital E
ARCH_TEXT_R = 47.5          # radius of the middle of the letters

# nameplate: a ramp across the front
PLATE_W = 98.0
PLATE_RIM = 8.0
RAMP_LIP = BASE_H + 0.6     # the vertical front edge under the slope, just above the base
RAMP_RISE = 20.0            # height the slope climbs
RAMP_ANGLE = 45.0           # degrees from flat; at 45 the letters need no supports
RAMP_TOP = 4.0              # flat top behind the slope
RAMP_GAP = 7.0              # flat between the ramp and the pocket
PLATE_TEXT_W = 80.0

SEG = 192


# ---------------------------------------------------------------- helpers
def text_outline(text, font):
    """the text's outline as a CrossSection, baseline on y=0, starting at x=0, at font size 100"""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), text, size=100, prop=FontProperties(fname=font))
    polys = [np.asarray(p) for p in tp.to_polygons(closed_only=True) if len(p) > 2]
    # NonZero: the joined-up script letters overlap each other
    return mf.CrossSection(polys, mf.FillRule.NonZero)


def cap_height(font):
    x0, y0, x1, y1 = text_outline("E", font).bounds()
    return y1 - y0


def fit(cs, width=None, height=None):
    """scale to the given width and/or height (whichever is smaller) and centre on the origin"""
    x0, y0, x1, y1 = cs.bounds()
    k = min(width / (x1 - x0) if width else 1e9, height / (y1 - y0) if height else 1e9)
    return cs.translate((-(x0 + x1) / 2, -(y0 + y1) / 2)).scale((k, k))


def check_strokes(cs, what):
    """a stroke thinner than MIN_STROKE vanishes when shrunk by half of it and grown back"""
    r = MIN_STROKE / 2 - 0.01
    lost = cs.area() - cs.offset(-r, mf.JoinType.Round).offset(r, mf.JoinType.Round).area()
    assert lost < 0.02 * cs.area(), f"{what}: {lost:.1f} mm2 of the letters are thinner than {MIN_STROKE} mm"


def slab(outline, h, top_round=EDGE, foot=FOOT):
    """the outline extruded to height h, with the first layer inset and the top edge rounded
    off in 0.1 mm steps (a quarter circle)"""
    parts = [mf.Manifold.extrude(outline.offset(-foot, mf.JoinType.Round), 0.2 + 1e-3)]
    body_top = h - top_round
    parts.append(mf.Manifold.extrude(outline, body_top - 0.2).translate((0, 0, 0.2)))
    n = max(1, int(round(top_round / 0.1)))
    for i in range(n):
        z0 = body_top + i * top_round / n
        a = (i + 0.5) / n
        inset = top_round - np.sqrt(max(0.0, 1 - a * a)) * top_round
        parts.append(mf.Manifold.extrude(outline.offset(-inset, mf.JoinType.Round), top_round / n + 1e-3)
                     .translate((0, 0, z0)))
    return mf.Manifold.batch_boolean(parts, mf.OpType.Add)


def pocket(cx, cy, top):
    """the cup's pocket, cut down from z=top, with a chamfered top edge"""
    r = POCKET_D / 2
    cut = mf.Manifold.cylinder(POCKET_DEPTH + 1, r, r, SEG).translate((cx, cy, top - POCKET_DEPTH))
    cham = mf.Manifold.cylinder(POCKET_CHAMFER + 0.01, r, r + POCKET_CHAMFER + 0.01, SEG) \
        .translate((cx, cy, top - POCKET_CHAMFER))
    return cut + cham


def letters_on_top(cs, top):
    """raised letters standing on a flat top at z=top (they sink 0.2 mm in, so they're joined)"""
    return mf.Manifold.extrude(cs, LETTER_H + 0.2).translate((0, 0, top - 0.2))


def heart(size):
    """a heart about `size` wide, centred, point down"""
    r = size / 4
    lobes = mf.CrossSection.circle(r, 64).translate((-r * 0.95, 0)) + mf.CrossSection.circle(r, 64).translate((r * 0.95, 0))
    point = mf.CrossSection([np.array([(-1.92 * r, -0.4 * r), (0, -2.35 * r), (1.92 * r, -0.4 * r)])])
    h = (lobes + point + mf.CrossSection.square((1.9 * r, 1.0 * r), center=True).translate((0, -0.2 * r)))
    x0, y0, x1, y1 = h.bounds()
    return h.translate((-(x0 + x1) / 2, -(y0 + y1) / 2))


def bend(cs, radius, mid_r, step=0.4):
    """wrap a straight line of text, centred on the origin, round the bottom of a circle so it
    reads left to right from the front with the tops of the letters towards the centre.
    x becomes arc length at mid_r, y becomes radius (mid_r at y=0)."""
    polys = []
    for p in cs.to_polygons():
        p = np.asarray(p)
        dense = []
        for a, b in zip(p, np.roll(p, -1, axis=0)):          # add points so straight edges bend smoothly
            n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
            dense.extend(a + (b - a) * t for t in np.arange(n) / n)
        d = np.array(dense)
        theta = -np.pi / 2 + d[:, 0] / mid_r
        r = mid_r - d[:, 1]
        polys.append(np.column_stack([r * np.cos(theta), r * np.sin(theta)]))
    return mf.CrossSection(polys, mf.FillRule.NonZero)


def rounded_rect(w, d, r):
    return mf.CrossSection.square((w - 2 * r, d - 2 * r), center=True).offset(r, mf.JoinType.Round, circular_segments=96)


def to_trimesh(m):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts, process=False)
    assert t.is_watertight and t.is_winding_consistent and t.volume > 0, "broken mesh"
    return t


# ---------------------------------------------------------------- the three designs
def tab():
    """a round coaster with a rounded tab out the front carrying the name in script"""
    R = POCKET_D / 2 + TAB_RIM
    cy = 0.0                                            # pocket centre; the tab is in front of it
    name = fit(text_outline(NAME, SCRIPT_FONT), width=TAB_TEXT_W)
    x0, y0, x1, y1 = name.bounds()
    top = cy - POCKET_D / 2 - POCKET_CHAMFER - TAB_GAP  # the name's top, just clear of the pocket
    name = name.translate((0, top - y1))
    front = top - (y1 - y0) - TAB_MARGIN                # the tab's front edge
    back = cy - R * 0.45                                # the tab runs back into the round part
    tab_shape = rounded_rect(TAB_W, back - front, 12).translate((0, (front + back) / 2))
    outline = mf.CrossSection.circle(R, SEG).translate((0, cy)) + tab_shape
    outline = outline.offset(8, mf.JoinType.Round, circular_segments=96).offset(-8, mf.JoinType.Round, circular_segments=96)
    base = slab(outline, BASE_H) - pocket(0, cy, BASE_H)
    pocket_edge = mf.CrossSection.circle(POCKET_D / 2 + POCKET_CHAMFER + 1.2, SEG).translate((0, cy))
    assert (name ^ pocket_edge).area() < 1e-6, "the name runs into the pocket"
    assert (name - outline.offset(-EDGE - 1.0)).area() < 1e-6, "the name runs off the tab"
    check_strokes(name, "tab")
    return base, letters_on_top(name, BASE_H)


def arch(hearts=True, floor_art=None, inlay=0.6):
    """a wide round coaster with the name curving round the front of the rim, a heart at each end.
    floor_art: a CrossSection (mm, centred) inlaid `inlay` deep and flush in the pocket floor,
    in the letters' colour (portrait.py puts a face there)"""
    R = ARCH_D / 2
    base = slab(mf.CrossSection.circle(R, SEG * 2), BASE_H) - pocket(0, 0, BASE_H)
    straight = text_outline(NAME, ROUND_FONT)
    k = ARCH_TEXT_CAP / cap_height(ROUND_FONT)
    x0, y0, x1, y1 = straight.bounds()
    # centre on the middle of the capitals' height, so the letters sit in the middle of the rim
    straight = straight.translate((-(x0 + x1) / 2, -cap_height(ROUND_FONT) / 2)).scale((k, k))
    check_strokes(straight, "arch")
    half = (x1 - x0) * k / 2
    name = bend(straight, R, ARCH_TEXT_R)
    for side in ((-1, 1) if hearts else ()):
        a = -np.pi / 2 + side * (half + 9.0) / ARCH_TEXT_R
        h = heart(9.0).rotate(np.degrees(a) + 90)
        name = name + h.translate((ARCH_TEXT_R * np.cos(a), ARCH_TEXT_R * np.sin(a)))
    rim = mf.CrossSection.circle(R - EDGE - 1.0, SEG * 2) - mf.CrossSection.circle(POCKET_D / 2 + POCKET_CHAMFER + 1.0, SEG * 2)
    assert (name - rim).area() < 1e-6, "the name doesn't fit on the rim"
    letters = letters_on_top(name, BASE_H)
    if floor_art is not None:
        assert (floor_art - mf.CrossSection.circle(POCKET_D / 2 - 0.5, SEG * 2)).area() < 1e-6, \
            "the floor art is bigger than the pocket"
        inlaid = mf.Manifold.extrude(floor_art, inlay).translate((0, 0, FLOOR - inlay))
        base = base - inlaid
        letters = letters + inlaid
    return base, letters


def nameplate():
    """a coaster with a 45-degree ramp across the front, like a desk nameplate, the name on its slope"""
    run = RAMP_RISE / np.tan(np.radians(RAMP_ANGLE))
    ramp_d = run + RAMP_TOP
    depth = ramp_d + RAMP_GAP + POCKET_D + 2 * PLATE_RIM - 2.0   # the rim at the back
    front = -depth / 2
    cy = front + ramp_d + RAMP_GAP + POCKET_D / 2
    outline = rounded_rect(PLATE_W, depth, 12)
    base = slab(outline, BASE_H) - pocket(0, cy, BASE_H)
    # the ramp's side profile (y, z), swept across and trimmed to the rounded footprint
    prof = [(front, 0), (front + ramp_d, 0), (front + ramp_d, RAMP_LIP + RAMP_RISE),
            (front + run, RAMP_LIP + RAMP_RISE), (front, RAMP_LIP)]
    sweep = mf.Manifold.extrude(mf.CrossSection([np.array(prof)]), PLATE_W + 2) \
        .rotate((90, 0, 90)).translate((-PLATE_W / 2 - 1, 0, 0))
    # check the profile landed where it should: y from front, z from 0
    b = sweep.bounding_box()
    assert abs(b[1] - front) < 1e-6 and abs(b[2]) < 1e-6, b
    footprint = slab(outline, RAMP_LIP + RAMP_RISE + 1, top_round=0.01)
    ramp = sweep ^ footprint
    base = base + ramp
    # the name on the slope: drawn flat, raised LETTER_H, then tipped up onto the slope
    name = fit(text_outline(NAME, SCRIPT_FONT), width=PLATE_TEXT_W, height=run * np.sqrt(2) * 0.6)
    check_strokes(name, "nameplate")
    slope_len = RAMP_RISE / np.sin(np.radians(RAMP_ANGLE))
    x0, y0, x1, y1 = name.bounds()
    assert y1 - y0 < slope_len - 4, "the name is too tall for the slope"
    letters = mf.Manifold.extrude(name, LETTER_H + 0.4).translate((0, 0, -0.4)) \
        .rotate((RAMP_ANGLE, 0, 0)).translate((0, front + run / 2, RAMP_LIP + RAMP_RISE / 2))
    return base, letters


DESIGNS = {"tab": tab, "arch": arch, "nameplate": nameplate}


def main():
    out = os.path.join(HERE, "stl")
    os.makedirs(out, exist_ok=True)
    for name, make in DESIGNS.items():
        base, letters = make()
        letters = letters - base                 # the letters' own volume only, so the two parts don't overlap
        b, t = to_trimesh(base), to_trimesh(letters)
        b.export(os.path.join(out, name + ".stl"))
        t.export(os.path.join(out, name + "_text.stl"))
        lo, hi = np.minimum(b.bounds[0], t.bounds[0]), np.maximum(b.bounds[1], t.bounds[1])
        size = hi - lo
        print(f"{name:10s} {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm   "
              f"base {b.volume / 1000:.1f} cm3, letters {t.volume / 1000:.2f} cm3")


if __name__ == "__main__":
    main()
