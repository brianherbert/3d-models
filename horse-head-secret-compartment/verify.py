#!/usr/bin/env python3
"""Checks on the exported part: watertightness, jaw swing without collision,
no mid-air islands in print orientation, and a volume for the compartment."""
import sys, numpy as np, trimesh, manifold3d as mf
from shapely.geometry import Polygon
from shapely.ops import unary_union
sys.path.insert(0, '.'); import sculpt_horse_head as H

body = trimesh.load('stl/preview_body.stl'); jaw = trimesh.load('stl/preview_jaw.stl')
def M(m): return mf.Manifold(mf.Mesh(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.uint32)))
print(f"body watertight={body.is_watertight} {body.volume/1000:.0f} cm3 | jaw watertight={jaw.is_watertight} {jaw.volume/1000:.1f} cm3")
print("bounds (mm):", np.round(np.vstack([body.bounds, jaw.bounds]).min(0), 1), np.round(np.vstack([body.bounds, jaw.bounds]).max(0), 1))

B = M(body); axis_pt = H.head_to_world([0, H.HY, H.HZ]); ax = np.array([1, 0, 0])
print("closed overlap", round((B ^ M(jaw)).volume(), 2), "mm3")
for deg in [10, 20, 30, 35, 40]:
    j = jaw.copy(); j.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-deg), ax, axis_pt))
    I = B ^ M(j); v = I.volume()
    print(f"open {deg:2d} deg: overlap {v:8.1f} mm3", np.round(I.bounding_box(), 0).tolist() if v > 5 else "")
    if deg == 30: j.export('stl/preview_jaw_open.stl')

# compartment: the jaw's hull minus the jaw, limited to the cavity region
cav = M(jaw.convex_hull) - M(jaw)
print("compartment (jaw cavity + hull slack) ~", round(cav.volume() / 1000, 1), "cm3")

def lp(m, z):
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None: return None
    T = np.eye(4); T[2, 3] = -z; p2, _ = sec.to_planar(to_2D=T)
    return unary_union([Polygon(np.asarray(pp.exterior.coords), [np.asarray(i.coords) for i in pp.interiors]) for pp in p2.polygons_full])
m = trimesh.load('stl/horse_head.stl'); prev = None; bad = []
for z in np.arange(0.1, m.bounds[1][2], 0.2):
    cur = lp(m, z)
    if cur is None: prev = None; continue
    if prev is not None:
        for g in (cur.geoms if cur.geom_type == 'MultiPolygon' else [cur]):
            if g.area > 0.3 and g.intersection(prev.buffer(0.5)).area < 1e-6:
                bad.append((round(z, 1), round(g.area, 1), tuple(np.round(g.centroid.coords[0], 1))))
    prev = cur
print("mid-air islands (0.2 mm layers, >0.3 mm2):", bad if bad else "none")
