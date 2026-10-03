#!/usr/bin/env python3
"""
Horse head bust with a hinged lower jaw and a secret compartment.
One print-in-place part: no supports, no assembly.

The bust is sculpted as a signed distance field (smooth unions of
ellipsoids, cones and capsules) and meshed with marching cubes.  The
lower jaw is cut out of the same field as a separate body with a 0.45 mm
clearance, hinged on a diamond-section pin that prints captive inside
the jowls, and hollowed with a uniform 2.4 mm wall to form the
compartment.  A vaulted mouth cavity above the jaw keeps every printed
surface self-supporting.

Coordinates: X = horse's left, Y = forward (nose), Z = up.
Printed standing on the flat neck base (Z = 0).

Usage:  python3 sculpt_horse_head.py [--res 0.5] [--preview]
Writes stl/horse_head.stl (the one part to print) and preview meshes.
"""
import argparse, numpy as np, trimesh
from skimage import measure
import manifold3d as mf

# ----------------------------------------------------------------- helpers
def rot_x(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def rot_z(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def smin(a, b, k):
    """polynomial smooth union with blend radius k"""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)
def smax(a, b, k):
    return -smin(-a, -b, k)

class Field:
    def __init__(self, P): self.P = P
    def ellipsoid(self, c, r, R=np.eye(3)):
        q = ((self.P - np.asarray(c)) @ R) / np.asarray(r)
        return (np.linalg.norm(q, axis=1) - 1.0) * min(r)
    def capsule(self, a, b, r):
        a, b = np.asarray(a, float), np.asarray(b, float)
        ab = b - a; t = np.clip(((self.P - a) @ ab) / (ab @ ab), 0, 1)
        return np.linalg.norm(self.P - (a + t[:, None] * ab), axis=1) - r
    def cone(self, a, b, ra, rb):
        a, b = np.asarray(a, float), np.asarray(b, float)
        ab = b - a; L2 = ab @ ab; t = np.clip(((self.P - a) @ ab) / L2, 0, 1)
        return np.linalg.norm(self.P - (a + t[:, None] * ab), axis=1) - (ra + (rb - ra) * t)
    def rbox(self, c, half, rad, R=np.eye(3)):
        """rounded box: half-sizes `half` with corner radius `rad`"""
        q = np.abs((self.P - np.asarray(c)) @ R) - (np.asarray(half) - rad)
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0) - rad

# ----------------------------------------------------------------- head frame
# Origin at the POLL (between the ears); +Y runs down the face to the
# muzzle, +Z is up off the face, +X is the horse's left.  The frame is
# tilted nose-down by TILT degrees and placed at POLL in world space.
TILT = 45.0
POLL = np.array([0.0, -22.0, 136.0])
PLINTH_C = np.array([0.0, -6.0]); PLINTH_R = np.array([40.0, 56.0]); PLINTH_H = 8.0
L = 108.0                     # poll to upper lip

def head_to_world(p):
    return np.asarray(p, float) @ rot_x(-TILT).T + POLL
def world_to_head(P):
    return (P - POLL) @ rot_x(-TILT)

# ----------------------------------------------------------------- the sculpt
def horse_sdf(P):
    """Signed distance of the whole bust (negative inside)."""
    F = Field(P)
    Fh = Field(world_to_head(P))

    skull   = Fh.ellipsoid([0, 0.26*L, -8], [21, 0.30*L, 22])
    face    = Fh.cone([0, 0.30*L, 0], [0, 0.92*L, -8], 17.5, 12.5)
    face_fl = Fh.ellipsoid([0, 0.60*L, -4], [15.5, 0.34*L, 16])
    jowlL   = Fh.ellipsoid([ 15, 0.22*L, -24], [11, 0.21*L, 21])
    jowlR   = Fh.ellipsoid([-15, 0.22*L, -24], [11, 0.21*L, 21])
    jaw     = Fh.cone([0, 0.22*L, -36], [0, 0.88*L, -26], 15, 10)
    muzzle  = Fh.ellipsoid([0, 0.92*L, -14], [13.5, 13, 13])
    lipU    = Fh.ellipsoid([0, 0.99*L, -16], [11, 7, 7.5])
    chin    = Fh.ellipsoid([0, 0.97*L, -27], [10, 10, 7])
    throat  = Fh.ellipsoid([0, 0.04*L, -36], [15, 16, 12])

    d = skull
    d = smin(d, face, 9)
    d = smin(d, face_fl, 9)
    d = smin(d, jowlL, 8); d = smin(d, jowlR, 8)
    d = smin(d, jaw, 8)
    d = smin(d, muzzle, 7)
    d = smin(d, lipU, 5)
    d = smin(d, chin, 6)
    d = smin(d, throat, 12)

    # ears: tapered cones at the poll, leaning back and out, scooped in front
    for sx in (1, -1):
        base = np.array([sx * 9.5, 2, 6]); tip = np.array([sx * 15, -8, 34])
        ear = Fh.cone(base, tip, 6.5, 1.8)
        scoop = Fh.ellipsoid(base + (tip - base) * 0.55 + np.array([0, 4.5, 0]), [3.2, 4.5, 9])
        d = smin(d, smax(ear, -scoop, 1.5), 4)
    # eyes: socket hollow with an eyeball, high where skull meets face
    for sx in (1, -1):
        socket = Fh.ellipsoid([sx * 19.5, 0.36*L, 2.5], [7.5, 9, 6.5])
        eye    = Fh.ellipsoid([sx * 20.0, 0.36*L, 0.5], [5.4, 6.8, 5.4])
        d = smax(d, -socket, 3.0)
        d = smin(d, eye, 4.5)          # blended into the socket floor so it prints
    # nostrils
    for sx in (1, -1):
        nostril = Fh.ellipsoid([sx * 8, 0.99*L, -9], [3.0, 4.5, 5.5], rot_z(sx * 30))
        d = smax(d, -nostril, 2)
    # mouth line groove
    d = smax(d, -Fh.ellipsoid([0, 1.0*L, -21], [12, 7, 0.9]), 1.0)

    # neck: an elliptical column leaning back, narrower at the throat than the
    # jowls, deeper (front-back) than it is wide
    sq = np.array([1.35, 1.0, 1.0])
    Fsq = Field(P * sq)
    neck = Fsq.cone(np.array([0, -26, -5]) * sq, np.array([0, -20, 100]) * sq, 32, 23)
    crest = F.capsule([0, -56, 10], [0, -40, 130], 9)
    d = smin(d, neck, 14)
    d = smin(d, crest, 8)
    # base plinth: a chamfered ellipse that also carries the chin strut
    e = np.linalg.norm((P[:, :2] - PLINTH_C) / PLINTH_R, axis=1)
    plinth = np.maximum((e - 1.0) * min(PLINTH_R), np.abs(P[:, 2] - PLINTH_H/2) - PLINTH_H/2)
    plinth = np.maximum(plinth, (e - 1.0) * min(PLINTH_R) + (P[:, 2] - PLINTH_H) + 2.5)   # 45-degree top edge
    d = np.minimum(d, plinth)
    return np.maximum(d, -P[:, 2])          # flat base at z = 0

# ----------------------------------------------------------------- jaw definition
GAP     = 0.45            # print-in-place clearance
PIN_GAP = 0.45            # hinge pin clearance, measured normal to the diamond's faces
WALL    = 2.4             # compartment wall
Z0      = -21.0           # mouth line (head frame z)
HY, HZ  = 20.0, -29.0     # hinge axis (head frame y, z); runs along x
RJ      = 26.0            # radius of the jaw's rounded heel around the hinge (reaches the underside skin)
OPEN_MAX  = 35.0
STRUT = None              # (x, y, z_top) of the chin strut; set by build() from the jaw's lowest point          # degrees the jaw is designed to open; the body is carved for this sweep
XJ      = 17.0            # half-width of the jaw block between the jowls
XP      = 21.0            # half-length of the hinge pin
PIN_R   = 3.0             # pin half-diagonal (diamond section)

def lower_jaw_parts(Ph):
    """the sculpt's own lower-jaw solids (jaw bar, chin, muzzle), slightly
    dilated so the blended skin around them goes with the jaw"""
    Fh = Field(Ph)
    jaw    = Fh.cone([0, 0.22*L, -36], [0, 0.88*L, -26], 15, 10)
    muzzle = Fh.ellipsoid([0, 0.92*L, -14], [13.5, 13, 13])
    chin   = Fh.ellipsoid([0, 0.97*L, -27], [10, 10, 7])
    return smin(smin(jaw, muzzle, 7), chin, 6) - 3.0

def jaw_sdf(d_head, Ph):
    """jaw region: inside the head, below the mouth line, between the jowls,
    and either within the lower-jaw solids or within the rounded heel
    around the hinge.  Defined by the sculpt's shapes, not a box, so the
    neck is never part of it."""
    x, y, z = Ph[:, 0], Ph[:, 1], Ph[:, 2]
    heel = np.hypot(y - HY, z - HZ) - RJ
    region = np.maximum.reduce([z - Z0, np.abs(x) - XJ, (HY - RJ) - y,
                                np.minimum(heel, lower_jaw_parts(Ph))])
    return np.maximum(d_head, region)

def pin_sdf(Ph, r, half_len=XP):
    """diamond-section bar along x through the hinge axis"""
    u = Ph[:, 1] - HY; v = Ph[:, 2] - HZ
    return np.maximum((np.abs(u) + np.abs(v) - r) / np.sqrt(2), np.abs(Ph[:, 0]) - half_len)

def mouth_cavity_sdf(Ph):
    """vaulted chamber above the jaw inside the body so the roof of the
    mouth is high and self-supporting instead of a flat face over the gap"""
    return Field(Ph).rbox([0, 0.60*L, Z0 + 8], [XJ - WALL, 0.26*L, 9], 5)

# ----------------------------------------------------------------- meshing
def grid(res):
    # start the grid a fraction of a cell off round numbers so no sample plane
    # lands exactly on the z = 0 base or the plinth top (exact zeros in the
    # field make marching cubes produce degenerate faces)
    xs = np.arange(-50 + 0.37 * res, 50 + res, res)
    ys = np.arange(-75 + 0.37 * res, 110 + res, res)
    zs = np.arange(-2 + 0.37 * res, 180 + res, res)
    return xs, ys, zs

def evaluate(fn, xs, ys, zs, slab=24):
    """evaluate fn(P) over the grid in z-slabs to bound memory"""
    out = np.empty((len(xs), len(ys), len(zs)), np.float32)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    for k0 in range(0, len(zs), slab):
        z = zs[k0:k0 + slab]
        Z = np.broadcast_to(z, (len(xs), len(ys), len(z)))
        P = np.c_[np.broadcast_to(X[..., None], Z.shape).ravel(),
                  np.broadcast_to(Y[..., None], Z.shape).ravel(), Z.ravel()].astype(np.float64)
        out[:, :, k0:k0 + len(z)] = fn(P).reshape(len(xs), len(ys), len(z))
    return out

def mesh_of(field, xs, ys, zs, res, level=0.0):
    v, f, _, _ = measure.marching_cubes(field, level=level, spacing=(res, res, res))
    v += np.array([xs[0], ys[0], zs[0]])
    m = trimesh.Trimesh(v, f, process=True)
    # keep the largest body (marching cubes leaves slivers along the blends)
    parts = m.split(only_watertight=False)
    m = max(parts, key=lambda p: p.volume)
    m.fix_normals()
    return m

def M(mesh):
    return mf.Manifold(mf.Mesh(np.asarray(mesh.vertices, np.float32), np.asarray(mesh.faces, np.uint32)))
def T(man):
    m = man.to_mesh(); return trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts))

def build(res, preview=False):
    xs, ys, zs = grid(res)
    print(f"grid {len(xs)}x{len(ys)}x{len(zs)} at {res} mm")
    d = evaluate(horse_sdf, xs, ys, zs)
    head = mesh_of(d, xs, ys, zs, res)
    print("head:", "watertight" if head.is_watertight else "NOT watertight", np.round(head.bounds, 1))
    head.export("stl/preview_head_solid.stl")
    if preview: return

    # --- fields derived from the head field
    def body_fn(P):
        Ph = world_to_head(P); dh = horse_sdf(P)
        j = jaw_sdf(dh, Ph)
        # body = head minus (jaw + clearance) minus the mouth vault minus the pin socket
        # clearance for the whole swept path of the jaw from closed to OPEN_MAX
        axis_pt = head_to_world([0, HY, HZ])
        sweep = j
        for th in np.linspace(0, OPEN_MAX, 8)[1:]:
            Pr = (P - axis_pt) @ rot_x(th).T + axis_pt      # un-rotate the sample points
            sweep = np.minimum(sweep, jaw_sdf(horse_sdf(Pr), world_to_head(Pr)))
        b = np.maximum(dh, GAP - sweep)
        b = np.maximum(b, -mouth_cavity_sdf(Ph))
        # breakaway strut from the plinth up to 0.25 mm under the chin: a thin
        # cross-shaped blade with a notch at its foot so it snaps off cleanly
        if STRUT is not None:
            sx, sy, ztop = STRUT
            blade = np.minimum(np.maximum(np.abs(P[:, 0] - sx) - 6.0, np.abs(P[:, 1] - sy) - 0.5),
                               np.maximum(np.abs(P[:, 0] - sx) - 0.5, np.abs(P[:, 1] - sy) - 5.0))
            blade = np.maximum(blade, np.maximum(PLINTH_H - 0.5 - P[:, 2], P[:, 2] - ztop))
            notch = np.maximum(np.abs(P[:, 2] - (PLINTH_H + 1.0)) - 0.6, 0.3 - np.minimum(np.abs(P[:, 0] - sx), np.abs(P[:, 1] - sy)))
            blade = np.maximum(blade, -notch)
            b = np.minimum(b, np.maximum(blade, j - 0.2))    # never closer than 0.2 mm (one layer) to the jaw
        return b
        b = np.maximum(b, -(pin_sdf(Ph, PIN_R + PIN_GAP * np.sqrt(2), XP + 0.6)))
        return b
    def jaw_fn(P):
        Ph = world_to_head(P); dh = horse_sdf(P)
        j = jaw_sdf(dh, Ph)
        # compartment: the head eroded by WALL, limited to the front of the jaw,
        # open at the top (mouth line)
        x, y, z = Ph[:, 0], Ph[:, 1], Ph[:, 2]
        cav_box = np.maximum.reduce([(HY + RJ + 2.0) - y, y - (0.90*L - WALL), np.abs(x) - (XJ - WALL)])
        cav = np.maximum(dh + WALL, cav_box)
        j = np.maximum(j, -cav)
        j = np.minimum(j, np.maximum(pin_sdf(Ph, PIN_R), dh + 1.5))   # pin, kept inside the jowls
        return j
    global STRUT
    j = evaluate(jaw_fn, xs, ys, zs);  jaw  = mesh_of(j, xs, ys, zs, res)
    v = jaw.vertices; low = v[v[:, 2] < jaw.bounds[0][2] + 0.8]
    STRUT = (0.0, float(low[:, 1].mean()), float(jaw.bounds[0][2]) - 0.2)
    print("chin strut at", np.round(STRUT, 1))
    b = evaluate(body_fn, xs, ys, zs); body = mesh_of(b, xs, ys, zs, res)
    print("body:", "watertight" if body.is_watertight else "NOT watertight",
          "| jaw:", "watertight" if jaw.is_watertight else "NOT watertight",
          "| jaw volume", round(jaw.volume / 1000, 1), "cm3")
    body.export("stl/preview_body.stl"); jaw.export("stl/preview_jaw.stl")
    trimesh.util.concatenate([body, jaw]).export("stl/horse_head.stl")
    print("wrote stl/horse_head.stl")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=float, default=0.5)
    ap.add_argument("--preview", action="store_true", help="solid head only")
    a = ap.parse_args()
    build(a.res, a.preview)
