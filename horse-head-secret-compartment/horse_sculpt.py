#!/usr/bin/env python3
"""
Horse head bust - the sculpt (shape only).

An original parametric sculpt.  Its proportions (dorsal line, jaw line,
widths at seven heights along the head, landmark positions) were
calibrated against the Cyberware horse scan (Georgia Tech large-models
archive, via alecjacobson/common-3d-test-models), measured by ray casting
in a head frame.  No reference geometry is used in the model itself.

Head frame (mm): origin at the poll, +y from the poll toward the front of
the lips (the lips are at y = L), +z up off the face, +x the horse's left.
World: +z up, +y forward, plinth on z = 0.
"""
import numpy as np
from scipy.interpolate import PchipInterpolator

# ----------------------------------------------------------------- placement
L    = 96.0                       # poll to lips (mm)
TILT = 62.0                       # head axis, degrees below horizontal
POLL = np.array([0.0, 0.0, 150.0])
_c, _s = np.cos(np.radians(-TILT)), np.sin(np.radians(-TILT))
R = np.array([[1, 0, 0], [0, _c, -_s], [0, _s, _c]])   # columns = head axes in world

def h2w(p):  return np.asarray(p, float) @ R.T + POLL
def w2h(P):  return (np.asarray(P, float) - POLL) @ R
def H(yf, zf, xf=0.0):  return np.array([xf * L, yf * L, zf * L])

# ----------------------------------------------------------------- SDF helpers
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)
def smax(a, b, k):
    return -smin(-a, -b, k)

def ellipsoid(P, c, r, Rm=None):
    q = P - np.asarray(c, float)
    if Rm is not None: q = q @ Rm
    r = np.asarray(r, float)
    k0 = np.linalg.norm(q / r, axis=1)
    k1 = np.linalg.norm(q / (r * r), axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)

def capsule(P, a, b, ra, rb=None):
    a = np.asarray(a, float); b = np.asarray(b, float); rb = ra if rb is None else rb
    ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1) - (ra + (rb - ra) * t)

def chain(P, pts, radii):
    d = np.full(len(P), 1e9)
    for i in range(len(pts) - 1):
        d = np.minimum(d, capsule(P, pts[i], pts[i + 1], radii[i], radii[i + 1]))
    return d

def rotx(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def implicit_sdf(F, P, h=0.15):
    f0 = F(P)
    g = np.zeros_like(P)
    for i in range(3):
        e = np.zeros(3); e[i] = h
        g[:, i] = (F(P + e) - F(P - e)) / (2 * h)
    return f0 / np.maximum(np.linalg.norm(g, axis=1), 1e-6)

# ----------------------------------------------------------------- loft profiles (fractions of L)
def prof(pts):
    y, v = np.array(pts, float).T
    return PchipInterpolator(y * L, v * L, extrapolate=True)

# top (dorsal) line, measured: poll, flat forehead, straight nasal line
# rising slightly relative to the poll-lips axis, rolling over the nose
ZT = prof([(-0.08, -0.05), (0.00, 0.000), (0.05, 0.030), (0.10, 0.042), (0.20, 0.050),
           (0.30, 0.054), (0.40, 0.064), (0.50, 0.073), (0.60, 0.082), (0.70, 0.091),
           (0.80, 0.100), (0.86, 0.105), (0.91, 0.102), (0.95, 0.086), (0.985, 0.055)])
# bottom line: throat, round jowl, rising jaw line, chin, lower lip
ZB = prof([(-0.08, -0.13), (0.00, -0.22), (0.06, -0.28), (0.12, -0.33), (0.19, -0.365),
           (0.27, -0.378), (0.35, -0.372), (0.43, -0.352), (0.50, -0.328), (0.57, -0.300),
           (0.64, -0.270), (0.70, -0.240), (0.76, -0.208), (0.82, -0.182), (0.87, -0.168),
           (0.92, -0.150), (0.96, -0.120), (0.985, -0.080)])
# half-widths at seven section heights u (-1 = bottom, +1 = top), measured
U_NODES = np.array([-0.8, -0.5, -0.2, 0.1, 0.4, 0.7, 0.9])
W_ROWS = np.array([
    # y      u=-.8   -.5    -.2    .1     .4     .7     .9
    [-0.08, 0.110, 0.125, 0.130, 0.128, 0.120, 0.105, 0.080],
    [ 0.00, 0.175, 0.190, 0.195, 0.190, 0.180, 0.160, 0.120],
    [ 0.10, 0.190, 0.200, 0.195, 0.185, 0.182, 0.185, 0.150],
    [ 0.20, 0.190, 0.200, 0.200, 0.198, 0.200, 0.205, 0.165],
    [ 0.30, 0.170, 0.205, 0.215, 0.222, 0.222, 0.222, 0.195],
    [ 0.40, 0.125, 0.195, 0.225, 0.228, 0.215, 0.192, 0.150],
    [ 0.50, 0.105, 0.172, 0.208, 0.208, 0.182, 0.140, 0.092],
    [ 0.60, 0.090, 0.150, 0.165, 0.155, 0.138, 0.100, 0.063],
    [ 0.70, 0.084, 0.128, 0.135, 0.125, 0.114, 0.088, 0.057],
    [ 0.80, 0.070, 0.114, 0.121, 0.119, 0.114, 0.098, 0.064],
    [ 0.88, 0.062, 0.100, 0.116, 0.115, 0.095, 0.080, 0.062],
    [ 0.94, 0.052, 0.078, 0.098, 0.098, 0.082, 0.064, 0.040],
    [ 0.985, 0.035, 0.050, 0.060, 0.060, 0.052, 0.040, 0.025]])
Y0, Y1 = -0.08 * L, 0.985 * L
_W_FUN = [PchipInterpolator(W_ROWS[:, 0] * L, W_ROWS[:, k + 1] * L, extrapolate=True) for k in range(7)]
N_X, N_U = 2.8, 3.0                        # cross-section superellipse exponents
_ROUND = (1 - np.abs(U_NODES) ** N_U) ** (1 / N_X)

def _width(yc, u):
    """half-width at height u: Catmull-Rom through the seven nodes (values
    pre-divided by the superellipse rounding so the measured widths hold)"""
    vals = np.stack([_W_FUN[k](yc) / _ROUND[k] for k in range(7)], 1)
    nodes = np.concatenate([[-1.1], U_NODES, [1.1]])
    vals = np.concatenate([vals[:, :1], vals, vals[:, -1:]], 1)
    uc = np.clip(u, nodes[0], nodes[-1] - 1e-6)
    k = np.clip(np.searchsorted(nodes, uc) - 1, 0, len(nodes) - 2)
    i0, i1 = np.clip(k - 1, 0, len(nodes) - 1), k
    i2, i3 = k + 1, np.clip(k + 2, 0, len(nodes) - 1)
    r = np.arange(len(u))
    p0, p1, p2, p3 = vals[r, i0], vals[r, i1], vals[r, i2], vals[r, i3]
    t = (uc - nodes[i1]) / (nodes[i2] - nodes[i1])
    t2, t3 = t * t, t * t * t
    return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)

def loft_F(Ph):
    x, y, z = Ph[:, 0], Ph[:, 1], Ph[:, 2]
    yc = np.clip(y, Y0, Y1)
    zt, zb = ZT(yc), ZB(yc)
    zc, hz = 0.5 * (zt + zb), 0.5 * (zt - zb)
    u = (z - zc) / hz
    w = np.maximum(_width(yc, u), 0.5)
    A = (np.abs(x) / w) ** N_X + np.abs(u) ** N_U
    A = A + (np.maximum(y - Y1, 0) / (0.030 * L)) ** 2 + (np.maximum(Y0 - y, 0) / (0.08 * L)) ** 2
    return A ** (1.0 / N_U) - 1.0        # degree-1 so F/|grad F| stays a fair distance far away

_LOFT_GRID = None
_LG_LO = np.array([-0.32, -0.30, -0.50]) * L
_LG_HI = np.array([0.32, 1.10, 0.25]) * L
_LG_H = 0.4
def _loft_grid():
    """Euclidean distance to the loft on a grid (distance transform), used
    away from the surface where the implicit estimate is unreliable"""
    global _LOFT_GRID
    if _LOFT_GRID is None:
        from scipy.ndimage import distance_transform_edt
        axes = [np.arange(lo, hi + _LG_H, _LG_H) for lo, hi in zip(_LG_LO, _LG_HI)]
        G = np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, 3)
        inside = (loft_F(G) < 0).reshape([len(a) for a in axes])
        from scipy.ndimage import gaussian_filter
        g = (distance_transform_edt(~inside) - distance_transform_edt(inside)) * _LG_H
        _LOFT_GRID = gaussian_filter(g, 1.5).astype(np.float32)
    return _LOFT_GRID

def loft_sdf(Ph):
    from scipy.ndimage import map_coordinates
    near = implicit_sdf(loft_F, Ph)
    G = _loft_grid()
    idx = ((Ph - _LG_LO) / _LG_H).T
    far = map_coordinates(G, idx, order=1, mode="nearest")
    # outside the grid: distance to the grid box plus the boundary value
    box = np.linalg.norm(np.maximum(np.maximum(_LG_LO - Ph, Ph - _LG_HI), 0), axis=1)
    far = far + box
    w = np.clip((np.abs(near) - 2.0) / 1.5, 0, 1)
    w = w * w * (3 - 2 * w)
    return near * (1 - w) + far * w

# ----------------------------------------------------------------- surface probes
def surf_x(y, z, field):
    lo, hi = 0.0, 0.45 * L
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if field(np.array([[mid, y, z]]))[0] < 0: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)

def surf_along(p0, dirn, field, smax_=0.4 * L):
    """first surface point from p0 (inside) along dirn"""
    dirn = np.asarray(dirn, float) / np.linalg.norm(dirn)
    lo, hi = 0.0, smax_
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if field(np.array([np.asarray(p0) + mid * dirn]))[0] < 0: lo = mid
        else: hi = mid
    return np.asarray(p0) + 0.5 * (lo + hi) * dirn

# ----------------------------------------------------------------- muzzle and lips
def muzzle_sdf(Ph, d):
    upper = ellipsoid(Ph, H(0.955, 0.020), np.array([0.092, 0.050, 0.060]) * L)
    lower = ellipsoid(Ph, H(0.950, -0.058), np.array([0.070, 0.044, 0.034]) * L)
    chin  = ellipsoid(Ph, H(0.885, -0.128), np.array([0.064, 0.058, 0.040]) * L, rotx(-20))
    d = smin(d, upper, 0.035 * L)
    d = smin(d, lower, 0.022 * L)
    d = smin(d, chin, 0.028 * L)
    d = smax(d, -ellipsoid(Ph, H(0.925, -0.098), np.array([0.058, 0.014, 0.010]) * L, rotx(-25)), 0.010 * L)
    return d

def base_head(Ph):
    return muzzle_sdf(Ph, loft_sdf(Ph))

class _A: pass
_AN = None
def anchors():
    """surface positions of features, computed once on the base head"""
    global _AN
    if _AN is not None: return _AN
    a = _A()
    a.eye_y, a.eye_z = 0.335 * L, -0.030 * L
    a.eye_x = surf_x(a.eye_y, a.eye_z, base_head)
    a.crest = [(0.30, -0.080), (0.37, -0.088), (0.45, -0.097), (0.53, -0.104), (0.60, -0.108)]
    a.crest_x = [surf_x(y * L, z * L, base_head) for y, z in a.crest]
    a.jowl_c = (0.300 * L, -0.200 * L)
    a.jowl_x = surf_x(a.jowl_c[0], a.jowl_c[1], base_head)
    nn = np.array([0.78, 0.30, 0.55]); nn /= np.linalg.norm(nn)
    a.nostril = surf_along(H(0.895, 0.000, 0.0), nn, base_head)
    a.nostril_n = nn
    _AN = a
    return a

# ----------------------------------------------------------------- head details
def eye_detail(Ph, d, s):
    a = anchors()
    ex, ey, ez = s * a.eye_x, a.eye_y, a.eye_z
    Re = rotx(-10)
    # recess in front of and below the eye (the face narrows below the orbit)
    d = smax(d, -ellipsoid(Ph, [s * (a.eye_x + 0.020 * L), ey + 0.070 * L, ez - 0.035 * L], np.array([0.030, 0.060, 0.035]) * L), 0.030 * L)
    # hollow above and behind the eye (temporal fossa)
    d = smax(d, -ellipsoid(Ph, [s * (a.eye_x + 0.012 * L), ey - 0.085 * L, ez + 0.060 * L], np.array([0.032, 0.045, 0.030]) * L), 0.028 * L)
    # brow: the bony orbit arch over and behind the eye
    d = smin(d, ellipsoid(Ph, [s * (a.eye_x - 0.016 * L), ey - 0.010 * L, ez + 0.036 * L], np.array([0.030, 0.062, 0.024]) * L, rotx(-6)), 0.024 * L)
    # almond eyeball standing a little proud of the face
    c = np.array([ex - s * 0.012 * L, ey, ez])
    rE = np.array([0.026, 0.043, 0.024]) * L
    d = smin(d, ellipsoid(Ph, c, rE, Re), 0.003 * L)
    q = (Ph - c) @ Re                               # eye frame: y along the eye, z up
    # upper lid: a shell over the top of the eyeball, ending in a crisp margin
    # slightly above centre and lifting toward the back corner
    lid = ellipsoid(Ph, c, rE + 0.55, Re)
    d = smin(d, np.maximum(lid, 0.15 * rE[2] - q[:, 2] - 0.12 * q[:, 1]), 0.002 * L)
    # lower lid: a thinner shell under the bottom quarter
    lidl = ellipsoid(Ph, c, rE + 0.22, Re)
    d = smin(d, np.maximum(lidl, q[:, 2] + 0.55 * rE[2]), 0.002 * L)
    # fold above the upper lid
    fold = ellipsoid(Ph, c + Re @ np.array([0, -0.004 * L, 0.012 * L]), rE + np.array([0.9, 1.6, 1.2]), Re)
    crease = np.abs(fold) - 0.35
    d = smax(d, -np.maximum(crease, 0.42 * rE[2] - q[:, 2]), 0.25)
    return d

def nostril_detail(Ph, d, s):
    a = anchors()
    c = a.nostril.copy(); c[0] *= s
    n = a.nostril_n.copy(); n[0] *= s
    ax = np.array([s * -0.35, 0.10, 1.0]); ax -= n * (ax @ n); ax /= np.linalg.norm(ax)
    bx = s * np.cross(n, ax)                              # lateral (mirrored for both sides)
    Rn = np.stack([bx, ax, n], 1)
    # gentle swelling of the muzzle around the nostril
    d = smin(d, ellipsoid(Ph, c - n * 0.010 * L, np.array([0.044, 0.078, 0.018]) * L, Rn), 0.026 * L)
    q = (Ph - c) @ Rn
    # comma-shaped opening: round at the bottom, its tail curling up and out;
    # its walls flare outward so the edge rolls instead of leaving a flap
    path = np.array([[0.004, -0.034], [0.000, -0.010], [0.006, 0.014], [0.018, 0.032], [0.030, 0.036]]) * L
    rad = np.array([0.016, 0.015, 0.011, 0.006, 0.003]) * L
    dist = np.full(len(Ph), 1e9)
    for i in range(len(path) - 1):
        p0, p1 = path[i], path[i + 1]; seg = p1 - p0
        t = np.clip(((q[:, :2] - p0) @ seg) / (seg @ seg), 0, 1)
        dd = np.linalg.norm(q[:, :2] - (p0 + t[:, None] * seg), axis=1) - (rad[i] + (rad[i + 1] - rad[i]) * t)
        dist = np.minimum(dist, dd)
    depth = 0.028 * L * np.clip(1 - (q[:, 1] - 0.010 * L) / (0.040 * L), 0.15, 1)   # shallower toward the tail
    hole = np.maximum(dist - 0.5 * np.maximum(q[:, 2] + 0.006 * L, 0), -q[:, 2] - depth)
    d = smax(d, -hole, 0.010 * L)
    return d

def head_details(Ph, d):
    a = anchors()
    for s in (1, -1):
        d = eye_detail(Ph, d, s)
        pts = [[s * (x - 0.006 * L), y * L, z * L] for (y, z), x in zip(a.crest, a.crest_x)]
        jy, jz = a.jowl_c
        # cheek: a broad flat plate whose back and bottom border is a clean edge
        plate = ellipsoid(Ph, [s * (a.jowl_x - 0.045 * L), jy, jz + 0.020 * L], np.array([0.050, 0.170, 0.150]) * L)
        d = smin(d, plate, 0.060 * L)
        dy, dz = Ph[:, 1] - jy, Ph[:, 2] - jz
        rr = np.hypot(dy, dz)
        phi = np.arctan2(dz, dy)
        active = np.cos(phi - np.radians(178)) - np.cos(np.radians(48))      # back and underneath only
        edge = np.abs(rr - 0.170 * L) - 0.008 * L
        side = np.abs(Ph[:, 0]) - (a.jowl_x - 0.004 * L)
        groove = np.maximum.reduce([edge, -side, -active * 0.05 * L])
        d = smax(d, -groove, 0.014 * L)
        d = nostril_detail(Ph, d, s)
    for s in (1, -1):
        d = smax(d, -capsule(Ph, H(0.80, -0.085, s * 0.125), H(0.87, -0.068, s * 0.118), 0.008 * L, 0.004 * L), 0.012 * L)
    return d

# ----------------------------------------------------------------- ears (head frame)
EAR_LEN = 0.24 * L
EAR_WALL = 1.3
def ear_frame(s):
    base = H(0.040, 0.020, s * 0.100)
    dv = np.array([s * 0.30, -0.35, 1.0]); dv /= np.linalg.norm(dv)          # up the ear
    o = np.array([s * 0.55, 1.0, 0.10]); o -= dv * (o @ dv); o /= np.linalg.norm(o)   # the way the ear opens
    e = np.cross(dv, o)
    return base, dv, o, e

def _ear_ab(tt):
    """half-width a (across the opening) and half-depth b along the ear: a
    narrow base, widest about 40 % up, then a pointed tip"""
    a = 0.062 * L * (1 - tt) ** 0.85 * (0.62 + 2.2 * tt) + 0.12
    b = 0.70 * a
    return a, b

def ear_sdf(Ph, s, inner=False):
    base, dv, o, e = ear_frame(s)
    q = Ph - base
    tl = q @ dv
    tt = np.clip(tl / EAR_LEN, 0, 1)
    # tips turn slightly toward each other and forward
    q = q - np.outer(tt ** 2, -s * np.array([1.0, 0, 0]) * 0.05 * L + o * 0.020 * L)
    a, b = _ear_ab(tt)
    w = q @ e; f = q @ o
    if inner:
        ai, bi = np.maximum(a - EAR_WALL, 0.05), np.maximum(b - EAR_WALL, 0.05)
        shift = 0.5 * b + EAR_WALL                  # inner front pokes 0.5 b past the outer: the cup is open
        r = np.sqrt((w / ai) ** 2 + ((f - shift) / bi) ** 2)
        return np.maximum.reduce([(r - 1.0) * np.minimum(ai, bi), 0.14 * EAR_LEN - tl, tl - 0.88 * EAR_LEN])
    r = np.sqrt((w / a) ** 2 + (f / b) ** 2)
    return np.maximum.reduce([(r - 1.0) * np.minimum(a, b), -tl - 3.0, tl - EAR_LEN])

def ears(Ph, d):
    for s in (1, -1):
        d = smin(d, np.maximum(ear_sdf(Ph, s), -ear_sdf(Ph, s, True)), 0.030 * L)
    return d

def forelock(Ph, d):
    """tuft from between the ears down the forehead"""
    x, y = Ph[:, 0], Ph[:, 1]
    yn = (y - 0.02 * L) / (0.24 * L)
    width = 0.085 * L * (1 - 0.55 * np.clip(yn, 0, 1))
    ragged = 0.07 * np.sin(x / 1.6) + 0.05 * np.sin(x / 0.7 + 2.0)
    cover = np.clip((1.0 + ragged - yn) / 0.10, 0, 1) * np.clip((yn + 0.10) / 0.10, 0, 1)
    cover *= np.clip((width - np.abs(x)) / 1.5, 0, 1) * (Ph[:, 2] > 0.0)
    flow = x * (1 + 0.15 * np.clip(yn, 0, 1)) + 0.5 * np.sin(y / 5.0)
    groove = 0.45 * np.abs(np.sin(flow / 1.15)) + 0.2 * np.abs(np.sin(flow / 0.5))
    return np.minimum(d, d - np.maximum(1.8 * cover - groove * cover, 0))

# ----------------------------------------------------------------- neck (world): elliptical cone chain along an arched spine
#                 y,     z (relative to the poll),  half-depth,  width/depth
NECK = np.array([[ -6.0,  -8.0, 15.0, 0.80],
                 [-22.0, -15.0, 17.5, 0.80],
                 [-39.0, -27.0, 21.5, 0.80],
                 [-50.0, -45.0, 26.0, 0.78],
                 [-53.0, -70.0, 31.5, 0.77],
                 [-50.0, -100.0, 38.0, 0.78],
                 [-42.0, -128.0, 45.0, 0.80],
                 [-36.0, -155.0, 50.0, 0.82]])
CREST = np.array([[ -4.0,   2.0, 6.0], [-24.0,   2.5, 8.5], [-45.0,  -7.0, 10.5],
                  [-64.0, -28.0, 12.0], [-76.0, -58.0, 13.0], [-82.0, -95.0, 13.0], [-84.0, -155.0, 13.0]])

def _elliptic_seg(P, a, b, ra, rb, ka, kb):
    """tapered segment in the y-z plane with elliptical cross-section (x squashed)"""
    a3 = np.array([0, a[0] + POLL[1], a[1] + POLL[2]])
    b3 = np.array([0, b[0] + POLL[1], b[1] + POLL[2]])
    ab = b3 - a3; t = np.clip(((P - a3) @ ab) / (ab @ ab), 0, 1)
    q = P - (a3 + t[:, None] * ab)
    r = ra + (rb - ra) * t; k = ka + (kb - ka) * t
    qn = np.sqrt((q[:, 0] / k) ** 2 + q[:, 1] ** 2 + q[:, 2] ** 2)
    return (qn - r) * np.minimum(k, 1.0)

_NECK_SP = None
def _neck_spline():
    global _NECK_SP
    if _NECK_SP is None:
        from scipy.interpolate import CubicSpline
        c = np.r_[0, np.cumsum(np.linalg.norm(np.diff(NECK[:, :2], axis=0), axis=1))]
        sp = CubicSpline(c, NECK, bc_type="natural")
        tt = np.linspace(0, c[-1], 90)
        _NECK_SP = (sp, tt, sp(tt))
    return _NECK_SP

def neck(P):
    """swept ellipse along a spline spine; the closest spine parameter is found
    on a dense polyline, then radius and squash come from the spline there,
    so the surface has no joints"""
    sp, tt, S_ = _neck_spline()
    lo = np.array([-60.0, -130.0, -10.0]); hi = np.array([60.0, 30.0, 175.0])
    m = np.all((P > lo) & (P < hi), axis=1)
    d = np.linalg.norm(np.maximum(np.maximum(lo - P, P - hi), 0), axis=1) + 5.0
    Q = P[m][:, 1:] - POLL[1:]
    # soft-weighted closest parameter (streaming log-sum-exp) so the
    # parameter varies smoothly even on the inside of the spine's bend
    tau = 2.0
    mref = np.full(len(Q), 1e18); Sw = np.zeros(len(Q)); St = np.zeros(len(Q))
    for i in range(len(S_) - 1):
        a, b = S_[i, :2], S_[i + 1, :2]; ab = b - a
        t = np.clip(((Q - a) @ ab) / (ab @ ab), 0, 1)
        dd = np.sqrt(np.sum((Q - (a + t[:, None] * ab)) ** 2, 1))
        tp = tt[i] + t * (tt[i + 1] - tt[i])
        newm = np.minimum(mref, dd)
        sc = np.exp(-(mref - newm) / tau)
        w = np.exp(-(dd - newm) / tau)
        Sw = Sw * sc + w; St = St * sc + w * tp; mref = newm
    tb = St / Sw
    s = sp(tb)                                   # centre (y, z), half-depth, squash at the closest parameter
    q = Q - s[:, :2]
    qn = np.sqrt((P[m][:, 0] / s[:, 3]) ** 2 + np.sum(q * q, 1))
    dn = (qn - s[:, 2]) * np.minimum(s[:, 3], 1.0)
    c = np.full(len(Q), 1e9)
    for i in range(len(CREST) - 1):
        a, b = CREST[i], CREST[i + 1]
        c = np.minimum(c, _elliptic_seg(P[m], a[:2], b[:2], a[2], b[2], 0.9, 0.9))
    d[m] = smin(dn, c, 9.0)
    return d

# ----------------------------------------------------------------- body field without hair (for draping)
def bare(P):
    Ph = w2h(P)
    kb = 8.0 * np.clip((0.55 * L - Ph[:, 1]) / (0.15 * L), 0, 1) + 0.01
    return smin(head_field_bare(Ph), neck(P), kb)

def _grads(F, P, h=0.2):
    """field values and unit gradients at points P, in one batched call"""
    E = np.eye(3) * h
    Q = np.concatenate([P] + [P + e for e in E] + [P - e for e in E])
    v = F(Q).reshape(7, len(P))
    g = np.stack([(v[1 + i] - v[4 + i]) / (2 * h) for i in range(3)], 1)
    return v[0], g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)

def drape(F, P0, D0, lengths, step=2.0, offset=0.4, gravity=0.35):
    """walk hair locks over the surface F from points P0 along headings D0,
    falling under 'gravity', held 'offset' mm off the surface.  All locks
    walk together; returns a list of point arrays."""
    P = np.array(P0, float); D = np.array(D0, float); D /= np.linalg.norm(D, axis=1, keepdims=True)
    nst = (np.asarray(lengths) / step).astype(int)
    track = [P.copy()]
    for _ in range(nst.max()):
        _, n = _grads(F, P)
        D = D + gravity * np.array([0, 0, -1.0])
        D = D - n * np.sum(D * n, 1, keepdims=True); D /= np.linalg.norm(D, axis=1, keepdims=True)
        P = P + step * D
        for _ in range(3):
            f, n = _grads(F, P); P = P - (f - offset)[:, None] * n
        track.append(P.copy())
    track = np.stack(track, 1)
    return [track[i, :nst[i] + 1] for i in range(len(P))]

def _crest_point(t):
    """point on top of the crest at fraction t of its length (world)"""
    seg = np.diff(CREST[:, :2], axis=0); l = np.linalg.norm(seg, axis=1); cum = np.r_[0, np.cumsum(l)]
    sl = t * cum[-1]; k = min(np.searchsorted(cum, sl) - 1, len(seg) - 1); k = max(k, 0)
    u = (sl - cum[k]) / l[k]
    yz = CREST[k, :2] + u * seg[k]; rad = CREST[k, 2] + u * (CREST[k + 1, 2] - CREST[k, 2])
    tang = seg[k] / l[k]; nrm = np.array([-tang[1], tang[0]])          # outward (up/back) normal of the crest line
    if nrm[0] > 0: nrm = -nrm
    yz = yz + nrm * rad
    return np.array([0.0, yz[0] + POLL[1], yz[1] + POLL[2]]), np.array([0.0, tang[0], tang[1]])

_LOCKS = None
def locks():
    """mane and forelock as lists of (points, radii)"""
    global _LOCKS
    if _LOCKS is not None: return _LOCKS
    rng = np.random.default_rng(7)
    out = []
    # mane: locks rooted along the top of the crest, combed over to the horse's right (-x)
    n = 34
    P0, D0, Ls, R0 = [], [], [], []
    for i in range(n):
        t = 0.08 + 0.80 * (i + 0.6 * rng.random()) / n
        p0, tang = _crest_point(t)
        P0.append(p0 + np.array([0.5 + rng.normal(0, 0.8), 0, 0]))
        D0.append(np.array([-1.0, 0, -0.15]) + tang * (0.30 + 0.15 * rng.normal()))
        Ls.append((18 + 14 * np.sin(np.pi * min(t * 1.4, 1.0))) * (0.8 + 0.4 * rng.random()))
        R0.append((3.6 + 0.8 * np.sin(np.pi * t)) * (0.85 + 0.3 * rng.random()))
    for pts, r0 in zip(drape(bare, P0, D0, Ls, offset=-0.4, gravity=0.06), R0):
        out.append((pts, r0 * (1 - np.linspace(0, 1, len(pts)) ** 1.6) + 0.5))
    # a second, shorter layer between them so the roots don't show as ribs
    P0, D0, Ls = [], [], []
    for i in range(n - 1):
        t = 0.08 + 0.80 * (i + 1.0) / n
        p0, tang = _crest_point(t)
        P0.append(p0 + np.array([-0.5, 0, 0.5])); D0.append(np.array([-1.0, 0, -0.10]) + 0.25 * tang)
        Ls.append(9 + 8 * rng.random())
    for pts in drape(bare, P0, D0, Ls, offset=0.6, gravity=0.04):
        out.append((pts, 3.0 * (1 - np.linspace(0, 1, len(pts)) ** 1.4) + 0.6))
    # forelock: from between the ears down the forehead, flat strands
    xs = np.linspace(-5.0, 5.0, 7)
    P0 = [h2w(H(0.015, 0.06, 0.0)) + np.array([xo, 0, 0]) for xo in xs]
    D0 = [R @ np.array([xo * 0.05, 1.0, 0.0]) for xo in xs]
    Ls = [15 + 5 * np.cos(xo / 3.0) + rng.normal(0, 1.5) for xo in xs]
    for pts in drape(bare, P0, D0, Ls, offset=-0.5, gravity=0.10):
        out.append((pts, 1.9 * (1 - np.linspace(0, 1, len(pts)) ** 1.3) + 0.5))
    _LOCKS = out
    return out

def _lock_dist(Q, pts, rad, flat=0.55):
    """distance-like field of a tapered ribbon along pts: thinner across the
    surface normal than along it"""
    _, nrm = _LOCK_N[id(pts)]
    best = np.full(len(Q), 1e9)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]; ab = b - a
        t = np.clip(((Q - a) @ ab) / (ab @ ab), 0, 1)
        v = Q - (a + t[:, None] * ab)
        nn = nrm[i] + (nrm[i + 1] - nrm[i]) * t[:, None]
        vn = np.sum(v * nn, 1)
        vt2 = np.maximum(np.sum(v * v, 1) - vn * vn, 0)
        dd = np.sqrt(vt2 + (vn / flat) ** 2) - (rad[i] + (rad[i + 1] - rad[i]) * t)
        best = np.minimum(best, dd * flat)
    return best

_LOCK_N = {}
def hair(P, d):
    """add the locks to field d"""
    for pts, rad in locks():
        if id(pts) not in _LOCK_N:
            _LOCK_N[id(pts)] = _grads(bare, pts)
        lo = pts.min(0) - rad.max() - 2; hi = pts.max(0) + rad.max() + 2
        m = np.all((P > lo) & (P < hi), axis=1)
        if not m.any(): continue
        d[m] = smin(d[m], _lock_dist(P[m], pts, rad), 0.8)
    return d

# ----------------------------------------------------------------- plinth
PLINTH_H = 9.0
PLINTH_C = np.array([0.0, -20.0]); PLINTH_R = np.array([44.0, 79.0])
PLINTH_FRONT = 22.0      # the plinth stops short of the head so the slicer's supports reach the lips from the plate
def plinth(P):
    e = np.linalg.norm((P[:, :2] - PLINTH_C) / PLINTH_R, axis=1)
    side = (e - 1.0) * min(PLINTH_R)
    side = smax(side, P[:, 1] - PLINTH_FRONT, 8.0)          # flat front with rounded corners
    top = P[:, 2] - PLINTH_H
    d = np.maximum(side, top)
    return np.maximum(d, (side + top + 3.0) / np.sqrt(2))

# ----------------------------------------------------------------- the whole sculpt
def head_field_bare(Ph):
    d = base_head(Ph)
    d = head_details(Ph, d)
    return ears(Ph, d)

def head_field(Ph):
    return head_field_bare(Ph)

def body_base(P):
    Ph = w2h(P)
    # head and neck blend only around the throat and poll, never under the face
    kb = 8.0 * np.clip((0.55 * L - Ph[:, 1]) / (0.15 * L), 0, 1) + 0.01
    return smin(head_field(Ph), neck(P), kb)

def sculpt(P):
    d = body_base(P)
    d = hair(P, d)
    d = np.maximum(d, PLINTH_H - 0.5 - P[:, 2])
    d = smin(d, plinth(P), 3.0)
    return np.maximum(d, -P[:, 2])
