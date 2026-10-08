#!/usr/bin/env python3
"""
A Swiss-cheese wedge with a QR code on top: a physical way to hand over a
digital gift card (or any link).

    python3 build_wedge.py "https://example.com/your-link"  [out_dir]

The URL is a command-line argument on purpose.  If it is a gift card, the QR
code *is* the money, so the real build goes to a folder outside the repo
(or to private/, which git ignores).  Run with no URL to build the sample in
stl/, which points at a harmless placeholder.

Output, in out_dir:
    cheese_body.stl   the wedge (print in cheese yellow)
    cheese_qr.stl     the QR modules, 0.8 mm tall, sitting on the top face
    cheese_wedge.stl  both as one mesh, for a filament swap at a layer
    cheese_wedge.3mf  Bambu Studio project, two filaments, settings chosen

The wedge lies on its flat bottom.  Everything above the top face is QR, so
the colour change is a clean layer change: AMS prints it automatically, and
without AMS you add a filament-change pause at that layer.
"""
import os, sys
import numpy as np, qrcode, trimesh
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- parameters (mm) -------------------------------------------------------
SAMPLE_URL = "https://www.olympiaprovisions.com/"
ECC = qrcode.constants.ERROR_CORRECT_M     # ~15% damage tolerance
QR_SIZE = 61.5        # QR code width; a 41-module code (a ~90-character URL) gets 1.5 mm modules,
                      # shorter URLs get bigger ones, so the wedge is the same size whatever the link
QR_HEIGHT = 0.8       # how far the dark modules stand above the cheese
QUIET = 2             # light border around the code, in modules (spec says 4; 2 scans fine on a matte part)

ANGLE = 64            # wedge angle, degrees
HEIGHT = 28           # wedge thickness
SEED = 7              # change for a different hole pattern
THANKS = "ありがとう"   # debossed on the left side; "" to omit
THANKS_FONT = ["/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
               "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
               "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
               "C:/Windows/Fonts/msgothic.ttc"]
TEXT_H = 11           # cap height of the deboss
TEXT_DEPTH = 0.7

def qr_matrix(url):
    q = qrcode.QRCode(error_correction=ECC, border=0)
    q.add_data(url); q.make(fit=True)
    return np.array(q.get_matrix(), bool)

def to_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)

def wedge_geometry(module, n_modules):
    """Wedge apex at the origin, pointing -x; the rind arc is at the back (+x).
    Returns (radius, square centre x, square side) so the QR square plus quiet
    zone fits on the top face with a margin."""
    side = (n_modules + 2 * QUIET) * module
    half = side / 2 + 2.0                                    # 2 mm margin to the edges
    t = np.tan(np.radians(ANGLE / 2))
    x_front = half / t
    x_back = x_front + side + 0.0
    radius = np.ceil(np.hypot(x_back + 2.0, half) + 2.0)
    return radius, (x_front + x_back) / 2, side

def sector(radius, n=96):
    a = np.radians(np.linspace(-ANGLE / 2, ANGLE / 2, n))
    pts = [(0.0, 0.0)] + [(radius * np.cos(t), radius * np.sin(t)) for t in a]
    return mf.CrossSection([pts])

def teardrop(r):
    """A sphere with a 45-degree roof, so a hole cut into a wall needs no support."""
    s = mf.Manifold.sphere(r, 48)
    tip = mf.Manifold.sphere(0.01, 8).translate([0, 0, r * np.sqrt(2)])
    return mf.Manifold.batch_hull([s, tip])

def text_solid(text, height, depth):
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    font = next((f for f in THANKS_FONT if os.path.exists(f)), None)
    if font is None:
        print("  no Japanese font found; skipping the deboss"); return None
    tp = TextPath((0, 0), text, size=10, prop=FontProperties(fname=font))
    polys = [p for p in tp.to_polygons(closed_only=True) if len(p) >= 3]
    cs = mf.CrossSection([[tuple(v) for v in p[:-1]] for p in polys], mf.FillRule.EvenOdd)
    (x0, y0), (x1, y1) = cs.bounds()[:2], cs.bounds()[2:]
    s = height / (y1 - y0)
    cs = cs.translate([-(x0 + x1) / 2, -(y0 + y1) / 2]).scale([s, s]).offset(0.2, mf.JoinType.Round)   # thicker strokes
    return cs.extrude(depth), (x1 - x0) * s

def holes(radius, sq_cx, side, text_box):
    """Swiss-cheese holes: dents on the two flat sides and the rind, a few
    craters on the top near the point, none touching the QR square or the text."""
    rng = np.random.default_rng(SEED)
    half_a = np.radians(ANGLE / 2)
    placed, cut = [], []
    sq = (sq_cx - side / 2 - 3, sq_cx + side / 2 + 3, -side / 2 - 3, side / 2 + 3)

    def free(p, r):
        return all(np.linalg.norm(p - q) > r + rq + 2.5 for q, rq in placed)

    def add(p, r):
        placed.append((p, r)); cut.append(teardrop(r).translate(p.tolist()))

    # side faces: the plane through the apex at angle +/-half_a
    for sgn in (1, -1):
        along = np.array([np.cos(half_a), np.sin(half_a) * sgn, 0])
        out = np.array([-np.sin(half_a), np.cos(half_a), 0]) * np.array([1, sgn, 1])
        n_ok = 0
        for _ in range(400):
            if n_ok >= 6: break
            r = rng.uniform(3.0, 7.0)
            d = rng.uniform(18, radius - 12)
            z = rng.uniform(r + 1.5, HEIGHT - r * 1.5 - 1.5)
            if text_box and sgn == text_box[0] and text_box[1] - r - 3 < d < text_box[2] + r + 3 and z > HEIGHT / 2 - TEXT_H / 2 - r - 3:
                continue
            # centre sits slightly outside the face so the dent is a shallow bowl, or inside for a deep one
            depth = rng.uniform(-0.45, 0.35) * r
            p = along * d - out * depth
            p[2] = z
            if free(p, r): add(p, r); n_ok += 1
    # rind (the back arc)
    n_ok = 0
    for _ in range(400):
        if n_ok >= 5: break
        r = rng.uniform(3.0, 6.5)
        t = rng.uniform(-half_a + 0.08, half_a - 0.08)
        z = rng.uniform(r + 1.5, HEIGHT - r * 1.5 - 1.5)
        rr = radius + rng.uniform(-0.35, 0.45) * r
        p = np.array([rr * np.cos(t), rr * np.sin(t), z])
        if free(p, r): add(p, r); n_ok += 1
    # top craters, only toward the point where there is no QR
    n_ok = 0
    for _ in range(400):
        if n_ok >= 3: break
        r = rng.uniform(2.5, 4.5)
        x = rng.uniform(14, sq[0] - r)
        y = rng.uniform(-1, 1) * (x * np.tan(half_a) - r - 2)
        p = np.array([x, y, HEIGHT + rng.uniform(-0.2, 0.3) * r])
        if abs(y) + r + 1.5 < x * np.tan(half_a) and free(p, r):
            placed.append((p, r)); cut.append(mf.Manifold.sphere(r, 48).translate(p.tolist())); n_ok += 1
    return cut

def build(url, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    M = qr_matrix(url)
    n = M.shape[0]
    MODULE = QR_SIZE / n
    if MODULE < 1.2:
        sys.exit(f"URL needs a {n}x{n} code, which would have {MODULE:.2f} mm modules; too fine to print and scan. Shorten the URL or raise QR_SIZE.")
    radius, sq_cx, side = wedge_geometry(MODULE, n)
    print(f"QR {n}x{n} modules at {MODULE:.2f} mm = {n * MODULE:.1f} mm; wedge radius {radius:.0f} mm, "
          f"angle {ANGLE} deg, height {HEIGHT} mm")

    body = sector(radius).extrude(HEIGHT)

    text_box = None
    if THANKS:
        res = text_solid(THANKS, TEXT_H, TEXT_DEPTH + 1.0)
        if res:
            txt, width = res
            # stand the letters up on the +y side face.  Seen from outside that face they
            # read toward the point, so text x -> toward the apex, text y -> up, text z -> out of the face
            a = np.radians(ANGLE / 2)
            c, s_ = np.cos(a), np.sin(a)
            d = radius * 0.5
            right, up, out = (-c, -s_, 0), (0, 0, 1), (-s_, c, 0)
            origin = np.array([d * c, d * s_, HEIGHT / 2]) - np.array(out) * TEXT_DEPTH
            txt = txt.transform([[right[0], up[0], out[0], origin[0]],
                                 [right[1], up[1], out[1], origin[1]],
                                 [right[2], up[2], out[2], origin[2]]])
            body = body - txt
            text_box = (1, d - width / 2, d + width / 2)

    for h in holes(radius, sq_cx, side, text_box):
        body = body - h

    # QR modules: merged into rectangles per row run, then unioned
    x0 = sq_cx - n * MODULE / 2
    y0 = -n * MODULE / 2
    rects = []
    for i in range(n):              # row i runs along -y ... keep the code readable from the back (+x) edge
        j = 0
        while j < n:
            if M[i, j]:
                k = j
                while k < n and M[i, k]: k += 1
                # module (i, j): x along columns, y along rows (top row at +y)
                xa, xb = x0 + j * MODULE, x0 + k * MODULE
                yb = -y0 - i * MODULE
                rects.append([(xa, yb - MODULE), (xb, yb - MODULE), (xb, yb), (xa, yb)])
                j = k
            else:
                j += 1
    # grow by 0.02 mm so modules that touch only at a corner overlap, which keeps the STL manifold
    qr2d = mf.CrossSection(rects, mf.FillRule.NonZero).offset(0.02, mf.JoinType.Miter)
    qr = qr2d.extrude(QR_HEIGHT).translate([0, 0, HEIGHT])   # sits on the top face: every layer is one colour

    # lay the point toward -x, centre the footprint on the origin
    b = to_trimesh(body); q = to_trimesh(qr)
    lo, hi = b.bounds
    shift = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    b.apply_translation(shift); q.apply_translation(shift)
    both = to_trimesh(mf.Manifold(mf.Mesh(np.asarray(b.vertices, np.float32), np.asarray(b.faces, np.uint32)))
                      + mf.Manifold(mf.Mesh(np.asarray(q.vertices, np.float32), np.asarray(q.faces, np.uint32))))
    for name, m in (("cheese_body", b), ("cheese_qr", q), ("cheese_wedge", both)):
        path = os.path.join(out_dir, name + ".stl")
        m.export(path)
        assert trimesh.load(path).is_watertight, name + " is not watertight once written as STL"
    print(f"wrote {out_dir}: body {b.volume / 1000:.0f} cm3, footprint {hi[0] - lo[0]:.0f} x {hi[1] - lo[1]:.0f} mm, "
          f"colour change at z = {HEIGHT:.2f} mm")
    return b, q

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else SAMPLE_URL
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "stl" if url == SAMPLE_URL else "private")
    build(url, out)
