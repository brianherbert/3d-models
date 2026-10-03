#!/usr/bin/env python3
"""README images: closed, open, front, side, cutaway, face close-up.
Run after build_horse.py and verify_horse.py (which writes the open jaw)."""
import sys, numpy as np, trimesh, manifold3d as mf, vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray

TAN, JAW, CUT = (0.80, 0.62, 0.42), (0.62, 0.70, 0.80), (0.55, 0.38, 0.25)

def actor(m, color):
    pts = vtk.vtkPoints(); pts.SetData(numpy_to_vtk(np.asarray(m.vertices, np.float64), deep=True))
    cells = np.hstack([np.full((len(m.faces), 1), 3), m.faces]).astype(np.int64).ravel()
    ca = vtk.vtkCellArray(); ca.SetCells(len(m.faces), numpy_to_vtkIdTypeArray(cells, deep=True))
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(ca)
    n = vtk.vtkPolyDataNormals(); n.SetInputData(pd); n.SetFeatureAngle(70); n.SplittingOn(); n.ConsistencyOn()
    mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(mp)
    p = a.GetProperty(); p.SetColor(*color); p.SetInterpolationToPhong()
    p.SetAmbient(0.22); p.SetDiffuse(0.78); p.SetSpecular(0.18); p.SetSpecularPower(25)
    return a

def render(parts, out, az, el, zoom=1.15, focus=None, size=(1100, 1100)):
    ren = vtk.vtkRenderer()
    for m, c in parts: ren.AddActor(actor(m, c))
    ren.GradientBackgroundOn(); ren.SetBackground(0.90, 0.90, 0.89); ren.SetBackground2(1, 1, 1)
    ren.AutomaticLightCreationOff()
    for pos, inten in (((1.0, 1.2, 1.6), 1.0), ((-1.4, 0.3, 0.6), 0.45), ((0.2, -1.5, 0.4), 0.35)):
        l = vtk.vtkLight(); l.SetLightTypeToCameraLight(); l.SetPosition(*pos); l.SetFocalPoint(0, 0, 0); l.SetIntensity(inten); ren.AddLight(l)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.AddRenderer(ren); win.SetSize(*size)
    b = np.vstack([m.bounds for m, _ in parts]); ctr = (b.min(0) + b.max(0)) / 2 if focus is None else np.asarray(focus, float)
    cam = ren.GetActiveCamera(); cam.SetFocalPoint(*ctr); cam.SetPosition(ctr[0], ctr[1] + 500, ctr[2]); cam.SetViewUp(0, 0, 1)
    cam.Azimuth(az); cam.Elevation(el); cam.OrthogonalizeViewUp(); cam.SetViewAngle(22)
    if focus is None: ren.ResetCamera()
    else: ren.ResetCameraClippingRange()
    cam.Zoom(zoom)
    win.Render()
    w = vtk.vtkWindowToImageFilter(); w.SetInput(win); w.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(out); wr.SetInputConnection(w.GetOutputPort()); wr.Write()
    print("wrote", out)

def M(m): return mf.Manifold(mf.Mesh(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.uint32)))
def T(x):
    m = x.to_mesh(); return trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts))

body = trimesh.load("stl/preview_body.stl"); jaw = trimesh.load("stl/preview_jaw.stl")
jaw_open = trimesh.load("stl/preview_jaw_open.stl")
render([(body, TAN), (jaw, TAN)], "images/horse_closed.png", 40, 12)
render([(body, TAN), (jaw_open, JAW)], "images/horse_open.png", 40, 12)
render([(body, TAN), (jaw, TAN)], "images/horse_side.png", 90, 5)
render([(body, TAN), (jaw, TAN)], "images/horse_front.png", 0, 8)
render([(body, TAN), (jaw, TAN)], "images/horse_face.png", 55, 10, zoom=2.3, focus=(0, 18, 112))
# cutaway: keep x < 0 and look at the cut face from +x
box = mf.Manifold.cube([200, 400, 400]).translate([-200, -200, -50])
render([(T(M(body) ^ box), TAN), (T(M(jaw) ^ box), JAW)], "images/horse_cutaway.png", -90, 5, zoom=1.9, focus=(0, 10, 105))
