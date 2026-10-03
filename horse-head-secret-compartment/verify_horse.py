#!/usr/bin/env python3
"""Checks on the exported part (run after build_horse.py):

  * body and jaw are watertight, separate shells;
  * the jaw swings from closed to OPEN_MAX without hitting the body
    (the only contact allowed is the detent nubs riding on the slot walls);
  * no mid-air islands when printed standing on the plinth;
  * steep downward-facing surfaces (> 55 degrees from vertical) are listed;
  * compartment volume.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, trimesh, manifold3d as mf
from shapely.geometry import Polygon
from shapely.ops import unary_union
import horse_sculpt as S, build_horse as B
B.STRUTS_SAVED = np.load("stl/.struts.npy")

body = trimesh.load("stl/preview_body.stl"); jaw = trimesh.load("stl/preview_jaw.stl")
def M(m): return mf.Manifold(mf.Mesh(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.uint32)))
print(f"body: watertight={body.is_watertight} volume={body.volume / 1000:.0f} cm3")
print(f"jaw:  watertight={jaw.is_watertight} volume={jaw.volume / 1000:.1f} cm3")
both = trimesh.load("stl/horse_head.stl")
print("overall size (mm):", np.round(both.extents, 1), " bounds:", np.round(both.bounds, 1).tolist())

# ---- swing
Bm = M(body)
hinge = S.h2w([0, B.TMJ[0], B.TMJ[1]])
nubs = [S.h2w(c) for c in B.nub_centres()]
print("closed overlap: %.2f mm3" % (Bm ^ M(jaw)).volume())
for deg in [2, 5, 10, 15, 20]:
    j = jaw.copy()
    j.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-deg), [1, 0, 0], hinge))
    I = Bm ^ M(j)
    v = I.volume()
    msg = ""
    if v > 0.01:
        m = I.to_mesh(); pts = np.asarray(m.vert_properties)[:, :3]
        # contact near the nubs is the detent working; anything else is a collision
        nub_now = [trimesh.transformations.transform_points([n], trimesh.transformations.rotation_matrix(np.radians(-deg), [1, 0, 0], hinge))[0] for n in nubs]
        dn = np.min([np.linalg.norm(pts - n, axis=1) for n in nub_now], axis=0)
        far = pts[dn > B.NUB_R + 1.0]
        # the breakaway struts are snapped off before the jaw is used
        st = np.array([s[:2] for s in B.STRUTS_SAVED]) if hasattr(B, "STRUTS_SAVED") else np.zeros((0, 2))
        if len(st) and len(far):
            ds = np.min([np.hypot(far[:, 0] - sx, far[:, 1] - sy) for sx, sy in st], axis=0)
            far = far[ds > 7.0]
        msg = "only at the detent nubs / struts" if len(far) == 0 else f"ELSEWHERE near {np.round(far.mean(0), 1)} ({len(far)} verts)"
    print(f"open {deg:2d} deg: overlap {v:7.2f} mm3  {msg}")
    if deg == 20: j.export("stl/preview_jaw_open.stl")

# ---- compartment: the hollow of jaw + body cavity, from the field
F = np.load("/tmp/claude-0/horse_fields.npz")
st = max(1, int(round(0.6 / (F["xs"][1] - F["xs"][0]))))          # sample at about 0.6 mm
xs, ys, zs = F["xs"][::st], F["ys"][::st], F["zs"][::st]; res = xs[1] - xs[0]
X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
P = np.c_[X.ravel(), Y.ravel(), Z.ravel()]
sel = (F["B"][::st, ::st, ::st].ravel() > 0) & (F["J"][::st, ::st, ::st].ravel() > 0)
Pc = P[sel]; Ph = S.w2h(Pc)
inside = (B.jaw_cavity(Ph, S.head_field(Ph)) < 0) | (B.body_cavity(Ph, S.head_field(Ph)) < 0)
print(f"compartment: about {inside.sum() * res ** 3 / 1000:.1f} cm3")

# ---- islands: a region of a layer with nothing under it in the layer below
def layer(m, z):
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None: return None
    T = np.eye(4); T[2, 3] = -z
    p2, _ = sec.to_planar(to_2D=T)
    return unary_union([Polygon(np.asarray(pp.exterior.coords), [np.asarray(i.coords) for i in pp.interiors]).buffer(0)
                        for pp in p2.polygons_full])
# a region with nothing in the layer below is either printed onto the other
# part across a print-in-place gap (like a support interface) or truly in mid-air
hist = []; bad = []; gapped = []
for z in np.arange(0.1, both.bounds[1][2], 0.2):
    cur = layer(both, z)
    if cur is None or cur.is_empty: cur = None
    if cur is not None and hist and hist[-1] is not None:
        for g in (cur.geoms if cur.geom_type == "MultiPolygon" else [cur]):
            if g.area > 0.2 and g.intersection(hist[-1].buffer(0.6)).area < 1e-6:
                below = [h for h in hist[-4:-1] if h is not None]
                rec = (round(z, 1), round(g.area, 1), tuple(np.round(g.centroid.coords[0], 1)))
                if below and any(g.intersection(h).area > 0.5 * g.area for h in below): gapped.append(rec)
                else: bad.append(rec)
    hist.append(cur)
print("regions printed onto the part below across the clearance gap:", gapped if gapped else "none")
print("mid-air islands (0.2 mm layers):", bad if bad else "none")

# ---- steep overhangs: downward faces steeper than 55 deg from vertical, grouped
n = both.face_normals; a = both.area_faces; c = both.triangles_center
steep = (n[:, 2] < -np.cos(np.radians(35))) & (c[:, 2] > B.PLINTH_H + 1)
print(f"faces facing down more than 55 deg from vertical: {a[steep].sum():.0f} mm2 total")
if steep.any():
    from scipy.cluster.hierarchy import fcluster, linkage
    pts = c[steep]; w = a[steep]
    if len(pts) > 6000:
        k = np.random.default_rng(0).choice(len(pts), 6000, replace=False); pts, w = pts[k], w[k] * len(c[steep]) / 6000
    lab = fcluster(linkage(pts, "single"), 2.0, "distance")
    groups = sorted([(w[lab == l].sum(), pts[lab == l].mean(0)) for l in np.unique(lab)], key=lambda t: -t[0])
    for area, ctr in groups[:12]:
        if area < 4: break
        print(f"   {area:6.0f} mm2 around {np.round(ctr, 1)}")
