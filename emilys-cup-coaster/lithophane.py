#!/usr/bin/env python3
"""
A lithophane of a photo for the arch design: a white disc whose thickness
follows the photo (thin where it's light, thick where it's dark), so the
picture shows when light shines through it. The base has a window right
through the pocket floor; the disc drops in over it, flat side up, and the
cup stands on it. Lift the coaster up to a lamp or a window, or stand it on a
phone's torch, and the face lights up.

    python3 lithophane.py photo.jpg      -> private/ (git-ignored)

Like portrait.py, the photo and everything made from it are someone's
likeness, so it all goes in private/ and never gets committed. Writes:

    private/lithophane_preview.png              what it looks like lit from behind (an estimate)
    private/stl/litho_base.stl, litho_text.stl  the base and its letters
    private/stl/litho_disc.stl                  the lithophane disc, as it prints (flat side down)
    private/images/                             renders
    private/emilys_cup_litho_base.3mf           lilac and white on the AMS
    private/emilys_cup_litho_disc.3mf           white, 0.16 mm layers, 100% infill

The face is framed the same way as portrait.py's (HEAD_ZOOM, HEAD_UP), and
the background is faded to white so she stands out against a bright glow.
Needs the same packages as portrait.py.
"""
import os, sys
import numpy as np
import cv2
import manifold3d as mf
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as B
import portrait as P

PRIVATE = P.PRIVATE

# ---------------------------------------------------------------- parameters
T_MIN, T_MAX = 0.8, 3.0         # mm; the disc's thickness where the photo is white and black
LEDGE = 1.4                     # mm; the ledge under the disc
WINDOW_R = 32.0                 # mm; the hole through the floor, under the picture
FIT = 0.2                       # mm; gap round the disc in the pocket
DISC_R = B.POCKET_D / 2 - FIT
PICTURE_R = WINDOW_R - 0.8      # the picture stops a little inside the window: a dark ring frames it
STEP = 0.2                      # mm between heights (half a nozzle width)
GAMMA = 1.35                    # above 1 lightens the midtones, below 1 darkens them
BACKGROUND = 0.97               # how light the faded background is (1 = as thin as the disc goes)
FEATHER = 1.2                   # mm; how softly the background fades in
COLOURS = ["#BDA8E2", "#F4F4F0"]        # lilac base, white letters (and print the disc in white too)

HEIGHT = LEDGE + T_MAX + B.POCKET_DEPTH  # the base: ledge, disc, then the cup's 3 mm


def picture(photo):
    """the photo's lightness (0 black .. 1 white) on a STEP grid over the disc, centred, y up"""
    pts, classes = P.detect(photo)
    gray = cv2.cvtColor(cv2.imread(photo), cv2.COLOR_BGR2GRAY)
    face_h = np.linalg.norm(pts[152] - pts[10])
    centre = (pts[152] + pts[10]) / 2 - [0, P.HEAD_UP * face_h]
    px_per_mm = P.HEAD_ZOOM * face_h / PICTURE_R
    n = int(np.ceil(2 * DISC_R / STEP)) + 1
    k = 1 / (px_per_mm * STEP)
    to_grid = np.array([[k, 0, (n - 1) / 2 - k * centre[0]], [0, k, (n - 1) / 2 - k * centre[1]]])
    img = cv2.warpAffine(gray, to_grid, (n, n), flags=cv2.INTER_AREA, borderValue=255)
    person = cv2.warpAffine(((classes != P.BG) & (classes != 5)).astype(np.float32), to_grid, (n, n),
                            flags=cv2.INTER_LINEAR, borderValue=0)
    # local contrast, so the face doesn't go flat
    img = cv2.createCLAHE(clipLimit=1.3, tileGridSize=(4, 4)).apply(img).astype(np.float32) / 255
    img = img ** (1 / GAMMA)
    person = cv2.GaussianBlur(person, (0, 0), FEATHER / STEP)
    light = person * img + (1 - person) * BACKGROUND
    light = cv2.GaussianBlur(light, (0, 0), 0.18 / STEP)   # soften skin texture and noise
    return np.flipud(light)                     # image rows run down; y runs up


def disc(light):
    """the disc as it sits in the base: flat top at z=T_MAX, the picture carved into its underside"""
    n = light.shape[0]
    xs = (np.arange(n) - (n - 1) / 2) * STEP
    X, Y = np.meshgrid(xs, xs)
    R = np.hypot(X, Y)
    t = T_MIN + (1 - np.clip(light, 0, 1)) * (T_MAX - T_MIN)
    t[R > PICTURE_R] = T_MAX
    bottom = T_MAX - t
    # a closed block: the heightfield underneath, a flat grid on top, and walls round the sides
    idx = np.arange(n * n).reshape(n, n)
    vb = np.column_stack([X.ravel(), Y.ravel(), bottom.ravel()])
    vt = np.column_stack([X.ravel(), Y.ravel(), np.full(n * n, T_MAX + 0.5)])
    a, b, c, d = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
    under = np.vstack([np.column_stack([a, c, b]), np.column_stack([a, d, c])])
    over = np.vstack([np.column_stack([a, b, c]), np.column_stack([a, c, d])]) + n * n
    ring = np.concatenate([idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]])
    p, q = ring, np.roll(ring, -1)
    walls = np.vstack([np.column_stack([p, q, q + n * n]), np.column_stack([p, q + n * n, p + n * n])])
    mesh = mf.Mesh(vert_properties=np.vstack([vb, vt]).astype(np.float32),
                   tri_verts=np.vstack([under, over, walls]).astype(np.uint32))
    block = mf.Manifold(mesh)
    assert block.status() == mf.Error.NoError, block.status()
    cyl = mf.Manifold.cylinder(T_MAX, DISC_R, DISC_R, B.SEG * 2)
    return block ^ cyl


def preview(light, path):
    """roughly what it looks like lit from behind: light falls off with thickness through white PLA"""
    t = T_MIN + (1 - np.clip(light, 0, 1)) * (T_MAX - T_MIN)
    n = light.shape[0]
    xs = (np.arange(n) - (n - 1) / 2) * STEP
    R = np.hypot(*np.meshgrid(xs, xs))
    t[R > PICTURE_R] = T_MAX
    glow = np.exp(-1.6 * (t - T_MIN))                     # white PLA: about 1.6 per mm
    glow[R > WINDOW_R] = 0.03                              # the base's rim, unlit
    warm = np.dstack([glow * 0.80, glow * 0.93, glow * 1.0])   # BGR: a warm lamp
    img = (np.flipud(warm) * 255).clip(0, 255).astype(np.uint8)
    cv2.imwrite(path, cv2.resize(img, (900, 900), interpolation=cv2.INTER_AREA))


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    os.makedirs(os.path.join(PRIVATE, "stl"), exist_ok=True)
    light = picture(sys.argv[1])
    preview(light, os.path.join(PRIVATE, "lithophane_preview.png"))
    base, letters = B.arch(hearts=False, height=HEIGHT, pocket_depth=T_MAX + B.POCKET_DEPTH, window_r=WINDOW_R)
    letters = letters - base
    d = disc(light)
    # print it flat side down: turn it over (the picture then reads the right way from the top
    # once it's flipped back into the base)
    printed = d.rotate((180, 0, 0)).translate((0, 0, T_MAX))
    out = {"litho_base": base, "litho_text": letters, "litho_disc": printed}
    for name, m in out.items():
        t = B.to_trimesh(m)
        t.export(os.path.join(PRIVATE, "stl", name + ".stl"))
        assert trimesh.load(os.path.join(PRIVATE, "stl", name + ".stl")).is_watertight, name
    print(f"base 122 x 122 x {HEIGHT + B.LETTER_H:.1f} mm, window {2 * WINDOW_R:.0f} mm; "
          f"disc {2 * DISC_R:.1f} x {T_MAX:.1f} mm, {T_MIN}-{T_MAX} mm thick in the picture")
    render(d)
    project()


def render(d):
    import render as R
    out = os.path.join(PRIVATE, "images")
    os.makedirs(out, exist_ok=True)
    rgb = lambda h: tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    stl = lambda n: os.path.join(PRIVATE, "stl", n + ".stl")
    seated = os.path.join(PRIVATE, "stl", "_seated.stl")
    B.to_trimesh(d.translate((0, 0, LEDGE))).export(seated)          # in place, for the renders only
    base = lambda: [R.actor(stl("litho_base"), rgb(COLOURS[0])), R.actor(stl("litho_text"), rgb(COLOURS[1]), spec=0.4)]
    white = (0.97, 0.97, 0.95)
    R.shot(base() + [R.actor(seated, white)], os.path.join(out, "litho.png"), (0, 0, 3), 0, 48, 1.25)
    R.shot([R.actor(stl("litho_disc"), white, spec=0.1)], os.path.join(out, "litho_disc.png"),
           (0, 0, 1), 0, 89.9, 1.05, size=(1000, 1000))
    R.shot(base(), os.path.join(out, "litho_base_only.png"), (0, 0, 3), 0, 48, 1.25)
    # from underneath: the window and the picture's relief (mirrored from this side)
    R.shot(base() + [R.actor(seated, white, spec=0.1)], os.path.join(out, "litho_under.png"), (0, 0, 3), 0, -70, 1.25)
    os.remove(seated)


def project():
    sys.path.insert(0, os.path.join(HERE, "..", "tools"))
    from bambu3mf import Part, write_project, BED
    from make_3mf import PROCESS, SETTINGS
    load = lambda n: trimesh.load(os.path.join(PRIVATE, "stl", n + ".stl"))
    c = BED / 2
    out = write_project(os.path.join(PRIVATE, "emilys_cup_litho_base.3mf"),
                        [Part("litho_base", load("litho_base"), c, c, extra=[("litho_text", load("litho_text"), 2)])],
                        PROCESS, SETTINGS, title="Emily's Cup: lithophane base",
                        description="Load lilac PLA as filament 1 and white as filament 2.",
                        thumbnail_png=os.path.join(PRIVATE, "images", "litho_base_only.png"), filament_colour=COLOURS)
    print("wrote", out)
    disc_settings = {
        "brim_type": "no_brim",
        "enable_support": "0",              # it prints flat side down; the picture is a gentle relief on top
        "sparse_infill_density": "100%",    # solid, so the light only sees the thickness
        "wall_loops": "2",
        "ironing_type": "no ironing",
    }
    out = write_project(os.path.join(PRIVATE, "emilys_cup_litho_disc.3mf"),
                        [Part("litho_disc", load("litho_disc"), c, c)],
                        "0.16mm High Quality @BBL A1", disc_settings, title="Emily's Cup: lithophane",
                        description="The lithophane. Print in white PLA, flat side down. "
                                    "Turn it over and drop it into the base.",
                        thumbnail_png=os.path.join(PRIVATE, "images", "litho_disc.png"), filament_colour="#F4F4F0")
    print("wrote", out)


if __name__ == "__main__":
    main()
