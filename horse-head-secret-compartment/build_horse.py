#!/usr/bin/env python3
"""
Horse head bust with a secret compartment: builds the print-in-place part.

The sculpt lives in horse_sculpt.py.  This file cuts the lower jaw out of
it, hinges it at the temporo-mandibular joint (TMJ) on a pin printed with the
body, hollows the compartment, adds a click detent so the mouth stays shut,
adds breakaway struts under the muzzle and chin, and meshes everything.

    python3 build_horse.py              # final, 0.3 mm grid
    python3 build_horse.py --res 0.6    # quick draft

Head frame (mm): origin at the poll, +y toward the lips (lips at y = L),
+z up off the face, +x the horse's left.  The hinge axis runs along x, so
in the world it is horizontal and the jaw opens by a rotation about x.
"""
import argparse, time, numpy as np, trimesh
from skimage import measure
from scipy.ndimage import map_coordinates
import horse_sculpt as S

L = S.L
# ----------------------------------------------------------------- mechanism parameters
TMJ = np.array([0.16 * L, -0.105 * L])     # hinge axis (head y, z)
R_ARC = 0.32 * L                           # jaw/jowl boundary: an arc about the hinge (front edge of the cheek)
OPEN_MAX = 20.0                            # designed opening, degrees
GAP = 0.45                                 # print-in-place clearance between jaw and body
WALL = 2.2                                 # compartment walls
PIN_R, PIN_GAP, PIN_HALF = 3.0, 0.40, 11.0  # hinge pin (part of the body)
KNUCKLE_R = 6.5                            # ring around the pin (part of the jaw)
ARM_HALF_X, ARM_HALF_H = 4.0, 4.0          # arm from the knuckle to the jaw
ARM_DIR = np.array([0.30, -0.035]) / np.hypot(0.30, -0.035)
# detent: a flexible tongue on each face of the arm with a nub that clicks into a dimple in the slot wall
TONGUE_T, SLIT, NUB_R, NUB_PROUD, DIMPLE_GAP = 1.6, 0.5, 1.4, 0.75, 0.25
NUB_RAD = 12.0                             # distance of the nub from the hinge
TONGUE_ROOT = 25.0                         # the tongue is free from NUB_RAD - 3 to its root here
# seam (mouth line): from the hinge under the cheek to the corner of the mouth, then between the lips
SEAM = np.array([[0.16, -0.105], [0.80, -0.085], [0.90, -0.052], [1.10, -0.042]]) * L
# struts
STRUT_GAP = 0.2                            # one layer of air between a strut and the part it holds up
PLINTH_H = S.PLINTH_H

def seam_z(y):
    return np.interp(y, SEAM[:, 0], SEAM[:, 1])

def rot_yz(Y, Z, deg, c=TMJ):
    """rotate head-frame (y, z) about the hinge; negative deg opens the jaw"""
    a = np.radians(deg); ca, sa = np.cos(a), np.sin(a)
    y, z = Y - c[0], Z - c[1]
    return c[0] + ca * y - sa * z, c[1] + sa * y + ca * z

# ----------------------------------------------------------------- regions (head frame), negative inside
def jaw_region(Ph):
    """the lower jaw: below the mouth line, in front of the cheek arc"""
    x, y, z = Ph[:, 0], Ph[:, 1], Ph[:, 2]
    r = np.hypot(y - TMJ[0], z - TMJ[1])
    return np.maximum.reduce([z - seam_z(y), R_ARC - r, 0.30 * L - y])

def arm_sdf(Ph):
    """central arm from the hinge out into the jaw, plus the knuckle ring"""
    x, y, z = Ph[:, 0], Ph[:, 1], Ph[:, 2]
    q = np.c_[y - TMJ[0], z - TMJ[1]]
    t = np.clip(q @ ARM_DIR, 0, R_ARC + 6.0)
    dl = np.linalg.norm(q - t[:, None] * ARM_DIR, axis=1) - ARM_HALF_H
    arm = np.maximum(dl, np.abs(x) - ARM_HALF_X)
    knuckle = np.maximum(np.hypot(q[:, 0], q[:, 1]) - KNUCKLE_R, np.abs(x) - ARM_HALF_X)
    return np.minimum(arm, knuckle)

def pin_sdf(Ph, grow=0.0):
    x, y, z = Ph[:, 0], Ph[:, 1], Ph[:, 2]
    return np.maximum(np.hypot(y - TMJ[0], z - TMJ[1]) - (PIN_R + grow), np.abs(x) - PIN_HALF)

def nub_centres():
    p = TMJ + NUB_RAD * ARM_DIR
    return [np.array([s * (ARM_HALF_X + NUB_PROUD - NUB_R), p[0], p[1]]) for s in (1, -1)]

def nub_sdf(Ph, grow=0.0):
    d = np.full(len(Ph), 1e9)
    for c in nub_centres():
        d = np.minimum(d, np.linalg.norm(Ph - c, axis=1) - (NUB_R + grow))
    return d

def tongue_slit(Ph):
    """the slit that frees a tongue on each face of the arm: a thin gap
    parallel to the face, open at the knuckle end, closed at the root"""
    x, y, z = Ph[:, 0], Ph[:, 1], Ph[:, 2]
    q = np.c_[y - TMJ[0], z - TMJ[1]]
    t = q @ ARM_DIR
    n = np.abs(q[:, 0] * ARM_DIR[1] - q[:, 1] * ARM_DIR[0])
    along = np.maximum(NUB_RAD - 4.5 - t, t - TONGUE_ROOT)
    across = n - (ARM_HALF_H + 1.0)
    inner = ARM_HALF_X - TONGUE_T
    slit_x = np.abs(np.abs(x) - (inner - SLIT / 2)) - SLIT / 2
    # also cut the tongue's free end off the knuckle
    endcut = np.maximum.reduce([np.abs(t - (NUB_RAD - 4.5 + SLIT / 2)) - SLIT / 2, inner - SLIT - np.abs(x), across])
    return np.minimum(np.maximum.reduce([slit_x, along, across]), endcut)

# ----------------------------------------------------------------- compartment
CAV_N = np.array([0.0, 1.0, 1.0]) / np.sqrt(2)          # slanted back wall (prints without support)
def cavity_back(Ph, y0):
    return -((Ph[:, 1] - y0) * CAV_N[1] + (Ph[:, 2] + 0.10 * L) * CAV_N[2])

def jaw_cavity(Ph, dh):
    x, y, z = Ph[:, 0], Ph[:, 1], Ph[:, 2]
    return np.maximum.reduce([dh + WALL, cavity_back(Ph, 0.52 * L), y - 0.90 * L, z - seam_z(y) - 1.0])

def body_cavity(Ph, dh):
    x, y, z = Ph[:, 0], Ph[:, 1], Ph[:, 2]
    return np.maximum.reduce([dh + WALL, cavity_back(Ph, 0.52 * L), y - 0.84 * L, seam_z(y) - z - 1.0])

# ----------------------------------------------------------------- roof over the cheek arc
SKIN = 2.4
ROOF_FROM = 30.0                           # arc points within this angle of the bottom get a pitched roof
def arc_roof(P, Ph, dh):
    """Below the hinge the cheek arc is nearly horizontal, so the cheek's
    underside would print as a flat ceiling over the jaw.  Hollow the cheek
    there up to a 45-degree pitched roof, leaving only its skin."""
    c = S.h2w([0, TMJ[0], TMJ[1]])
    yr, zr = P[:, 1] - c[1], P[:, 2] - c[2]
    r = np.hypot(yr, zr)
    a = np.radians(ROOF_FROM)
    roof = -R_ARC * np.cos(a) + (R_ARC * np.sin(a) - np.abs(yr))      # 45-degree lines from the arc points at +-ROOF_FROM
    return np.maximum.reduce([zr - roof, r - (R_ARC - 0.1), 8.0 - r, dh + SKIN, Ph[:, 2] - seam_z(Ph[:, 1]), np.abs(yr) - R_ARC * np.sin(a)])

# ----------------------------------------------------------------- the two parts (world points)
def jaw_closed(P, dh=None):
    """jaw solid at rest, before hollowing/detents (used for the sweep)"""
    Ph = S.w2h(P)
    if dh is None: dh = S.head_field(Ph)
    j = np.maximum(dh, jaw_region(Ph))
    return np.minimum(j, np.maximum(arm_sdf(Ph), dh + 1.0)), Ph, dh

def jaw_fn(P):
    j, Ph, dh = jaw_closed(P)
    j = np.maximum(j, -jaw_cavity(Ph, dh))
    j = np.maximum(j, -pin_sdf(Ph, PIN_GAP))                  # hole for the pin
    j = np.maximum(j, -tongue_slit(Ph))
    j = np.minimum(j, nub_sdf(Ph))
    return j

def swept_jaw(P, n=12):
    """union of the jaw (without nubs) over the opening range"""
    Ph = S.w2h(P)
    best = np.full(len(P), 1e9)
    # only points near the head's lower half can be reached
    near = (Ph[:, 1] > -0.05 * L) & (Ph[:, 2] < 0.05 * L) & (np.abs(Ph[:, 0]) < 0.35 * L)
    Q = Ph[near]
    out = np.full(len(Q), 1e9)
    for th in np.linspace(0, OPEN_MAX, n):
        y, z = rot_yz(Q[:, 1], Q[:, 2], th)                    # undo an opening of th
        Qr = np.c_[Q[:, 0], y, z]
        dh = S.head_field(Qr)
        jr = np.maximum(dh, jaw_region(Qr))
        jr = np.minimum(jr, np.maximum(arm_sdf(Qr), dh + 1.0))
        out = np.minimum(out, jr)
    best[near] = out
    return best

STRUTS = []          # filled by build(): (x, y, z_top, which) for the lowest points of body and jaw
def strut_sdf(P):
    d = np.full(len(P), 1e9)
    for sx, sy, ztop, _ in STRUTS:
        x, y, z = P[:, 0] - sx, P[:, 1] - sy, P[:, 2]
        h = np.clip((z - PLINTH_H) / max(ztop - PLINTH_H, 1), 0, 1)
        arm = 6.0 - 2.0 * h                                     # cross-shaped blade, narrowing upward
        blade = np.minimum(np.maximum(np.abs(x) - arm, np.abs(y) - 0.6), np.maximum(np.abs(x) - 0.6, np.abs(y) - arm))
        pad = np.hypot(x, y) - np.clip(4.0 - (ztop - z), 0, 4.0)  # a 45-degree cone widening to the contact
        s = np.maximum(np.minimum(blade, pad), np.maximum(PLINTH_H - 0.5 - z, z - ztop - 3.0))
        notch = np.maximum(np.abs(z - (PLINTH_H + 1.2)) - 0.6, 0.35 - np.minimum(np.abs(x), np.abs(y)))
        d = np.minimum(d, np.maximum(s, -notch))
    return d

def body_fn(P):
    d = S.sculpt(P)
    Ph = S.w2h(P)
    dh = S.head_field(Ph)
    sw = swept_jaw(P)
    b = np.maximum(d, GAP - sw)                                 # clear the jaw's whole path
    b = np.maximum(b, -body_cavity(Ph, dh))
    b = np.maximum(b, -arc_roof(P, Ph, dh))
    # dimple for the nub at the closed position
    b = np.maximum(b, -nub_sdf(Ph, DIMPLE_GAP))
    b = np.minimum(b, pin_sdf(Ph))                              # the pin bridges the arm slot
    if STRUTS:
        j, _, _ = jaw_closed(P, dh)
        b = np.minimum(b, np.maximum(strut_sdf(P), np.maximum(STRUT_GAP - j, STRUT_GAP - d)))
    return b

# ----------------------------------------------------------------- narrow-band evaluation and meshing
def grid(res):
    xs = np.arange(-46 + 0.37 * res, 46, res)
    ys = np.arange(-104 + 0.37 * res, 62, res)
    zs = np.arange(-1 + 0.37 * res, 170, res)
    return xs, ys, zs

def _eval(fn, xs, ys, zs, slab=12):
    out = np.empty((len(xs), len(ys), len(zs)), np.float32)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    for k0 in range(0, len(zs), slab):
        z = zs[k0:k0 + slab]
        P = np.c_[np.repeat(X[..., None], len(z), 2).ravel(), np.repeat(Y[..., None], len(z), 2).ravel(),
                  np.broadcast_to(z, X.shape + (len(z),)).ravel()]
        out[:, :, k0:k0 + len(z)] = fn(P).reshape(len(xs), len(ys), len(z))
    return out

def narrowband(fn, xs, ys, zs, factor=4, band=None):
    """evaluate fn exactly near its zero set and interpolate elsewhere"""
    res = xs[1] - xs[0]
    cx, cy, cz = xs[::factor], ys[::factor], zs[::factor]
    C = _eval(fn, cx, cy, cz)
    band = band if band is not None else 1.8 * factor * res
    fx = np.arange(len(xs)) / factor; fy = np.arange(len(ys)) / factor
    out = np.empty((len(xs), len(ys), len(zs)), np.float32)
    FX, FY = np.meshgrid(fx, fy, indexing="ij")
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    n_exact = 0
    for k in range(len(zs)):
        fz = np.full(FX.shape, k / factor)
        approx = map_coordinates(C, [FX.ravel(), FY.ravel(), fz.ravel()], order=1, mode="nearest").reshape(FX.shape)
        m = np.abs(approx) < band
        if m.any():
            P = np.c_[X[m], Y[m], np.full(m.sum(), zs[k])]
            approx[m] = fn(P)
            n_exact += m.sum()
        out[:, :, k] = approx
    print(f"   exact evaluations: {n_exact / 1e6:.1f} M of {out.size / 1e6:.0f} M")
    return out

def mesh_of(F, xs, ys, zs, min_vol=5.0):
    res = xs[1] - xs[0]
    v, f, _, _ = measure.marching_cubes(F, 0.0, spacing=(res, res, res))
    m = trimesh.Trimesh(v + [xs[0], ys[0], zs[0]], f, process=True)
    parts = [p for p in m.split(only_watertight=False) if abs(p.volume) > min_vol]
    print("   shells:", sorted([round(p.volume, 0) for p in parts], key=abs, reverse=True)[:8])
    m = trimesh.util.concatenate(parts)
    m.fix_normals()
    return m

def simplify(m, tol=0.02):
    import manifold3d as mf
    X = mf.Manifold(mf.Mesh(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.uint32)))
    Y = X.simplify(tol).to_mesh()
    out = trimesh.Trimesh(np.asarray(Y.vert_properties)[:, :3], np.asarray(Y.tri_verts))
    return out if out.is_watertight else m

def lowest_point(F, xs, ys, zs, keep):
    """lowest solid sample (world) among those where keep(P) holds"""
    idx = np.argwhere(F < 0)
    P = np.c_[xs[idx[:, 0]], ys[idx[:, 1]], zs[idx[:, 2]]]
    P = P[keep(P)]
    zmin = P[:, 2].min()
    low = P[P[:, 2] < zmin + 1.0]
    return np.array([low[:, 0].mean(), low[:, 1].mean(), zmin])

def build(res):
    t0 = time.time()
    S.anchors(); S.locks(); S._loft_grid()
    xs, ys, zs = grid(res)
    print(f"grid {len(xs)}x{len(ys)}x{len(zs)} at {res} mm")
    J = narrowband(jaw_fn, xs, ys, zs)
    jaw = mesh_of(J, xs, ys, zs)
    print(f"jaw: watertight={jaw.is_watertight}  {jaw.volume / 1000:.1f} cm3  ({time.time() - t0:.0f} s)")
    # struts under the lowest points of the jaw and of the muzzle
    global STRUTS
    pj = lowest_point(J, xs, ys, zs, lambda P: np.ones(len(P), bool))
    B0 = narrowband(lambda P: np.maximum(S.sculpt(P), GAP - jaw_closed(P)[0]), xs[::2], ys[::2], zs[::2], factor=3)
    pb = lowest_point(B0, xs[::2], ys[::2], zs[::2],
                      lambda P: (S.w2h(P)[:, 1] > 0.7 * L) & (P[:, 2] > PLINTH_H + 10) & (S.head_field(S.w2h(P)) < 0.5))
    STRUTS = [(pj[0], pj[1], pj[2] - STRUT_GAP, "jaw"), (pb[0], pb[1], pb[2] - STRUT_GAP, "muzzle")]
    print("struts:", [tuple(np.round(s[:3], 1)) for s in STRUTS])
    np.save("stl/.struts.npy", np.array([s[:3] for s in STRUTS], float))
    Bf = narrowband(body_fn, xs, ys, zs)
    body = mesh_of(Bf, xs, ys, zs)
    print(f"body: watertight={body.is_watertight}  {body.volume / 1000:.1f} cm3  ({time.time() - t0:.0f} s)")
    # merge coplanar-ish triangles (0.02 mm tolerance, far below print resolution)
    # so the STLs stay small enough to share
    body, jaw = simplify(body), simplify(jaw)
    print(f"simplified: body {len(body.faces)} faces watertight={body.is_watertight}, jaw {len(jaw.faces)} faces watertight={jaw.is_watertight}")
    body.export("stl/preview_body.stl"); jaw.export("stl/preview_jaw.stl")
    both = trimesh.util.concatenate([body, jaw])
    both.export("stl/horse_head.stl")
    np.savez_compressed("/tmp/claude-0/horse_fields.npz", J=J, B=Bf, xs=xs, ys=ys, zs=zs)
    print(f"wrote stl/horse_head.stl  bounds {np.round(both.bounds, 1).tolist()}  ({time.time() - t0:.0f} s)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=float, default=0.3)
    build(ap.parse_args().res)
