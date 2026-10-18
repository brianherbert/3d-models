#!/usr/bin/env python3
"""
Turn a selfie into line art for the floor of the arch design's pocket, so
the person's face shows when the cup isn't there.

    python3 portrait.py photo.jpg        -> private/ (git-ignored)

The photo, the line art and the build made from it are someone's likeness,
so they go in private/ and never get committed. Writes:

    private/portrait.png            the line art, to check before printing
    private/stl/portrait.stl        the arch design with the pocket, no hearts
    private/stl/portrait_ink.stl    the line art (inlaid flush in the pocket floor) and the name
    private/images/                 renders
    private/emilys_cup_portrait.3mf the Bambu Studio project, two AMS filaments

How the line art is made: MediaPipe finds the face (478 landmarks, with the
irises) and splits the photo into hair, face, neck, clothes and background.
The lines are the borders between those regions (the outline of the hair,
the hairline, the jaw, the collar), plus the eyebrows, eyes, nose, smile and
a few freckles drawn from the landmarks. Everything is drawn at
LINE mm or wider, so every stroke prints with a 0.4 mm nozzle.

    pip install mediapipe opencv-python-headless (plus build.py's packages)

MediaPipe needs libEGL on Linux (apt install libegl1). The two models it
uses download into private/models/ the first time.
"""
import os, sys, urllib.request
import numpy as np
import cv2
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as B

PRIVATE = os.path.join(HERE, "private")
MODELS = {
    "face_landmarker.task": "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
                            "face_landmarker/float16/1/face_landmarker.task",
    "selfie_multiclass.tflite": "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
                                "selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite",
}

# ---------------------------------------------------------------- parameters
ART_R = B.POCKET_D / 2 - 2.5    # mm; the line art fills a circle this big in the pocket floor
LINE = 0.9                      # mm; the outlines
FINE = 0.8                      # mm; the smaller features (no thinner: 2 nozzle widths)
LID = 1.2                       # mm; the upper eyelids, a bit bolder
INLAY = 0.6                     # mm; how deep the lines go into the floor (3 layers)
FRAME = 0.9                     # mm; a ring round the line art
HEAD_ZOOM = 0.87                # the circle's radius as a fraction of the face's height
HEAD_UP = 0.12                  # how far above the face's middle the circle is centred
MIN_AREA = 40.0                 # mm2; smaller bits of a region (stray hair, the cat, a gap under the hair)
                                # take the class round them
FRECKLES = [(-0.21, -0.03), (-0.15, 0.03), (-0.11, -0.05), (-0.06, -0.10), (0.05, -0.08),
            (0.12, -0.04), (0.17, 0.02), (0.22, -0.05)]  # over the nose and cheeks, in face widths
                                                         # from the nose's middle (x right, y down)
STRANDS = [4.5, 10.0]           # mm out from the face: lines that follow the hair round it
STRAND_CLEAR = 3.0              # mm; strands stop this far short of the hair's outline
RES = 0.05                      # mm per pixel while drawing

# MediaPipe face mesh indices
BROW_R = ([70, 63, 105, 66, 107], [46, 53, 52, 65, 55])           # upper edge, lower edge
BROW_L = ([300, 293, 334, 296, 336], [276, 283, 282, 295, 285])
LID_R = [33, 246, 161, 160, 159, 158, 157, 173, 133]
LID_L = [263, 466, 388, 387, 386, 385, 384, 398, 362]
IRIS_R, IRIS_L = 468, 473                                          # centres; the next four are the rim
NOSE = [64, 98, 97, 2, 326, 327, 294]
LIP_BOT = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291]
TEETH = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308]         # the top of the teeth
TEETH_BOT = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308]
# segmentation classes
BG, HAIR, SKIN, FACE, CLOTHES = 0, 1, 2, 3, 4


def model(name):
    path = os.path.join(PRIVATE, "models", name)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print("downloading", name)
        urllib.request.urlretrieve(MODELS[name], path)
    return path


def detect(photo):
    """landmarks (478 x 2, image pixels) and the class of every pixel"""
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    img = mp.Image.create_from_file(photo)
    with vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=mpt.BaseOptions(model_asset_path=model("face_landmarker.task")), num_faces=1)) as fl:
        faces = fl.detect(img).face_landmarks
    if not faces:
        raise SystemExit("no face found in " + photo)
    pts = np.array([[p.x * img.width, p.y * img.height] for p in faces[0]])
    with vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=mpt.BaseOptions(model_asset_path=model("selfie_multiclass.tflite")),
            output_category_mask=True)) as seg:
        classes = seg.segment(img).category_mask.numpy_view().copy().squeeze()
    return pts, classes


def draw(pts, classes):
    """the line art as a black-and-white image, RES mm per pixel, the circle filling it"""
    face_h = np.linalg.norm(pts[152] - pts[10])
    centre = (pts[152] + pts[10]) / 2 - [0, HEAD_UP * face_h]
    px_per_mm = HEAD_ZOOM * face_h / ART_R
    n = int(round(2 * ART_R / RES))
    k = 1 / (px_per_mm * RES)                                # photo pixels -> drawing pixels
    to_art = np.array([[k, 0, n / 2 - k * centre[0]], [0, k, n / 2 - k * centre[1]]])
    P = pts @ to_art[:, :2].T + to_art[:, 2]
    lab = cv2.warpAffine(classes, to_art, (n, n), flags=cv2.INTER_NEAREST, borderValue=BG)
    w = lambda mm: max(1, int(round(mm / RES)))

    # tidy the regions: smooth each one, drop crumbs, and give every pixel its smoothed class
    lab[lab == 5] = BG
    crumbs = np.zeros((n, n), np.uint8)
    for c in range(5):
        cnt, cc, stats, _ = cv2.connectedComponentsWithStats((lab == c).astype(np.uint8))
        for i in range(1, cnt):
            if stats[i, cv2.CC_STAT_AREA] * RES * RES < MIN_AREA:
                crumbs[cc == i] = 1
    # each crumb pixel takes the class of the nearest pixel that isn't a crumb
    _, nearest = cv2.distanceTransformWithLabels(crumbs, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    keep = crumbs == 0
    lut = np.zeros(nearest.max() + 1, np.uint8)
    lut[nearest[keep]] = lab[keep]
    lab = lut[nearest]
    score = np.zeros((5, n, n), np.float32)
    for c in range(5):
        score[c] = cv2.GaussianBlur((lab == c).astype(np.float32), (0, 0), 0.8 / RES)
    lab = score.argmax(0).astype(np.uint8)

    art = np.zeros((n, n), np.uint8)
    # borders between regions, LINE wide
    edge = np.zeros_like(art)
    edge[:-1, :] |= (lab[:-1, :] != lab[1:, :]).astype(np.uint8)
    edge[:, :-1] |= (lab[:, :-1] != lab[:, 1:]).astype(np.uint8)
    art |= cv2.dilate(edge, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (w(LINE), w(LINE))))

    poly = lambda ids: np.round(P[ids]).astype(np.int32)
    line = lambda ids, mm: cv2.polylines(art, [poly(ids)], False, 1, w(mm), cv2.LINE_AA)
    # eyebrows: filled between their upper and lower edges, at least FINE thick
    for up, lo in (BROW_R, BROW_L):
        cv2.fillPoly(art, [np.vstack([poly(up), poly(lo)[::-1]])], 1)
        line(up, FINE)
    # strands of hair: lines that follow the face's outline through the hair, a set distance out
    face = np.isin(lab, (FACE, SKIN)).astype(np.uint8)
    d_face = cv2.distanceTransform(1 - face, cv2.DIST_L2, 5) * RES
    d_edge = cv2.distanceTransform((lab == HAIR).astype(np.uint8), cv2.DIST_L2, 5) * RES
    for d in STRANDS:
        band = (np.abs(d_face - d) < w(LINE) * RES / 2) & (d_edge > STRAND_CLEAR)
        art |= band.astype(np.uint8)
    # eyes, smiling: a bold upper lid with the iris hanging under it
    for lid, iris in ((LID_R, IRIS_R), (LID_L, IRIS_L)):
        line(lid, LID)
        r = np.mean([np.linalg.norm(P[iris + i] - P[iris]) for i in range(1, 5)])
        disc = np.zeros_like(art)
        cv2.circle(disc, tuple(np.round(P[iris]).astype(int)), int(round(r * 0.9)), 1, -1, cv2.LINE_AA)
        below = np.zeros_like(art)                       # everything under the lid's curve
        drop = poly([lid[-1], lid[0]]) + [0, int(3 * r)]
        cv2.fillPoly(below, [np.vstack([poly(lid), drop])], 1)
        art |= disc & below
    line(NOSE, FINE)
    # the smile: the open mouth's outline and the lower lip under it
    cv2.polylines(art, [np.vstack([poly(TEETH), poly(TEETH_BOT)[::-1]])], True, 1, w(FINE), cv2.LINE_AA)
    line(LIP_BOT, FINE)
    # freckles
    face_w = np.linalg.norm(P[454] - P[234])
    bridge = P[195]
    for fx, fy in FRECKLES:
        c = bridge + np.array([fx, fy]) * face_w
        cv2.circle(art, tuple(np.round(c).astype(int)), w(FINE) // 2, 1, -1, cv2.LINE_AA)

    # keep it inside the circle, with a frame round it
    yy, xx = np.mgrid[:n, :n]
    rr = np.hypot(xx - n / 2, yy - n / 2) * RES
    art[rr > ART_R - FRAME] = 0
    art[(rr <= ART_R) & (rr > ART_R - FRAME)] = 1
    return art


def vectorise(art):
    """the drawing's black areas as a CrossSection in mm, centred on the origin, y up"""
    # smooth the pixel steps and the wobble of the region borders off the edges first
    art = (cv2.GaussianBlur(art.astype(np.float32), (0, 0), 0.12 / RES) > 0.5).astype(np.uint8)
    contours, tree = cv2.findContours(art, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    n = art.shape[0]
    shape = lambda c: mf.CrossSection([np.column_stack([(c[:, 0] - n / 2) * RES, (n / 2 - c[:, 1]) * RES])],
                                      mf.FillRule.NonZero)
    # each outline minus its holes, then all of them unioned, so outlines that touch merge cleanly
    pieces = []
    for i, c in enumerate(contours):
        if tree[0][i][3] != -1:                        # a hole; taken care of with its outline
            continue
        piece = shape(cv2.approxPolyDP(c, 1.0, True).reshape(-1, 2).astype(float))
        j = tree[0][i][2]
        while j != -1:
            piece = piece - shape(cv2.approxPolyDP(contours[j], 1.0, True).reshape(-1, 2).astype(float))
            j = tree[0][j][0]
        pieces.append(piece)
    cs = mf.CrossSection.batch_boolean(pieces, mf.OpType.Add)
    # anything that came out thinner than a printable stroke (corners where lines meet) is
    # thickened rather than lost
    r = B.MIN_STROKE / 2 - 0.01
    thin = cs - cs.offset(-r, mf.JoinType.Round).offset(r, mf.JoinType.Round)
    # Clipper leaves pairs of points a few nanometres apart; once the STL rounds them to 32-bit
    # floats they'd fuse and leave edges shared by four faces, so drop them
    return (cs + thin.offset(0.15, mf.JoinType.Round)).simplify(0.005)


COLOURS = ["#BDA8E2", "#4B2E83"]       # lilac base, dark purple lines and name


def render(base, ink):
    """private/images/: the line art from above, three-quarter, and with the cup in"""
    import render as R
    out = os.path.join(PRIVATE, "images")
    os.makedirs(out, exist_ok=True)
    rgb = lambda h: tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    stl = lambda n: os.path.join(PRIVATE, "stl", n + ".stl")
    parts = lambda: [R.actor(stl("portrait"), rgb(COLOURS[0])), R.actor(stl("portrait_ink"), rgb(COLOURS[1]), (0, 0, 0.02), 0.4)]  # lifted a
    # hair so the renderer can tell the flush lines from the floor
    R.shot(parts(), os.path.join(out, "portrait_top.png"), (0, 0, 3), 0, 89.9, 1.3, size=(1100, 1100))
    R.shot(parts(), os.path.join(out, "portrait.png"), (0, 0, 3), 0, 48, 1.25)
    R.shot(parts() + [R.actor(R.cup(), R.CUP, (0, 0, B.FLOOR), 0.6, 0.55)], os.path.join(out, "portrait_cup.png"),
           (0, 0, 30), 15, 22, 1.15, size=(1000, 1100))


def project():
    sys.path.insert(0, os.path.join(HERE, "..", "tools"))
    import trimesh
    from bambu3mf import Part, write_project, BED
    from make_3mf import PROCESS, SETTINGS
    load = lambda n: trimesh.load(os.path.join(PRIVATE, "stl", n + ".stl"))
    c = BED / 2
    part = Part("portrait", load("portrait"), c, c, extra=[("portrait_ink", load("portrait_ink"), 2)])
    out = write_project(os.path.join(PRIVATE, "emilys_cup_portrait.3mf"), [part], PROCESS, SETTINGS,
                        title="Emily's Cup: portrait",
                        description="Load lilac PLA as filament 1 and dark purple as filament 2.",
                        thumbnail_png=os.path.join(PRIVATE, "images", "portrait.png"), filament_colour=COLOURS)
    print("wrote", out)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    photo = sys.argv[1]
    os.makedirs(os.path.join(PRIVATE, "stl"), exist_ok=True)
    pts, classes = detect(photo)
    art = draw(pts, classes)
    cv2.imwrite(os.path.join(PRIVATE, "portrait.png"), 255 - art * 255)
    lines = vectorise(art)
    base, ink = B.arch(hearts=False, floor_art=lines, inlay=INLAY)
    ink = ink - base
    b, t = B.to_trimesh(base), B.to_trimesh(ink)
    b.export(os.path.join(PRIVATE, "stl", "portrait.stl"))
    t.export(os.path.join(PRIVATE, "stl", "portrait_ink.stl"))
    import trimesh
    for n in ("portrait", "portrait_ink"):                  # still sound after the STL's 32-bit rounding
        assert trimesh.load(os.path.join(PRIVATE, "stl", n + ".stl")).is_watertight, n + ".stl is broken"
    render(b, t)
    project()
    print(f"portrait   {b.extents[0]:.1f} x {b.extents[1]:.1f} x {max(b.bounds[1][2], t.bounds[1][2]):.1f} mm   "
          f"base {b.volume / 1000:.1f} cm3, ink {t.volume / 1000:.2f} cm3")


if __name__ == "__main__":
    main()
