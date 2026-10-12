#!/usr/bin/env python3
"""Preview renders (VTK, off-screen; on a headless machine run it under xvfb-run).

    python3 render.py            stl/ -> images/

Writes:
    crystal.png            assembled: white base, blue crystal
    crystal_lit.png        the same in the dark with the tea light on
    crystal_open.png       crystal lifted off, tea light lifted out of its pocket
    crystal_section.png    cut through the middle: how the tea light sits
    base_top.png           the base from above: socket, pocket and finger notches
"""
import os, sys, tempfile
import numpy as np, trimesh, vtk
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_crystal import SOCKET_FLOOR, POCKET_FLOOR, TEA_D, TEA_H

WHITE = (0.95, 0.94, 0.90)
BLUE = (0.35, 0.62, 0.95)
CANDLE = (0.97, 0.96, 0.93)
FLAME = (1.00, 0.80, 0.30)
TMP = tempfile.mkdtemp()

def tealight(path):
    """A stand-in for the LED tea light: body, then a flame bulb."""
    body_h = 20.0
    body = mf.Manifold.cylinder(body_h, TEA_D / 2, TEA_D / 2 - 0.6, 96)
    flame = mf.Manifold.sphere(5.5, 48).scale([1, 1, 1.9]).translate([0, 0, TEA_H - 10.5])
    neck = mf.Manifold.cylinder(TEA_H - body_h - 9, 3.0, 4.0, 48).translate([0, 0, body_h])
    g = (body + neck + flame).to_mesh()
    trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts)).export(path)
    return path

def actor(path, colour, move=(0, 0, 0), opacity=1.0, glow=0.0, flat=False):
    r = vtk.vtkSTLReader(); r.SetFileName(path)
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(20)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.SetPosition(*move)
    p = a.GetProperty(); p.SetColor(*colour); p.SetInterpolationToPhong(); p.SetOpacity(opacity)
    p.SetAmbient(0.25 + glow); p.SetDiffuse(0.75); p.SetSpecular(0.2); p.SetSpecularPower(30)
    return a

def halved(path, dz):
    t = trimesh.load(path); t.apply_translation([0, 0, dz])
    m = mf.Manifold(mf.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))
    g = m.trim_by_plane([0, 1, 0], 0).to_mesh()
    out = os.path.join(TMP, "cut_" + os.path.basename(path))
    trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts)).export(out)
    return out

def shot(actors, path, focus, az, el, zoom=1.0, size=(1000, 1200), dark=False, lamp=None, dist=700):
    ren = vtk.vtkRenderer()
    ren.SetUseDepthPeeling(1); ren.SetMaximumNumberOfPeels(8)
    for a in actors: ren.AddActor(a)
    ren.GradientBackgroundOn()
    if dark: ren.SetBackground(0.05, 0.06, 0.12); ren.SetBackground2(0.16, 0.19, 0.32)
    else: ren.SetBackground(0.93, 0.93, 0.92); ren.SetBackground2(0.99, 0.99, 0.99)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetAlphaBitPlanes(1); win.SetMultiSamples(0)
    win.AddRenderer(ren); win.SetSize(*size)
    ren.AutomaticLightCreationOff()
    key = 0.25 if dark else 0.95
    for pos, inten in (((0.6, 1.0, 1.6), key), ((-1.4, 0.3, 0.6), key * 0.4), ((0.2, -1.5, 0.4), key * 0.3)):
        l = vtk.vtkLight(); l.SetLightTypeToCameraLight(); l.SetPosition(*pos); l.SetFocalPoint(0, 0, 0)
        l.SetIntensity(inten); ren.AddLight(l)
    if lamp is not None:                            # the tea light, as a warm point light
        l = vtk.vtkLight(); l.SetLightTypeToSceneLight(); l.SetPositional(1); l.SetConeAngle(180)
        l.SetPosition(*lamp); l.SetFocalPoint(lamp[0], lamp[1], lamp[2] - 1); l.SetColor(1.0, 0.85, 0.55)
        l.SetIntensity(1.6); l.SetAttenuationValues(1, 0.0, 0.0002); ren.AddLight(l)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(*focus)
    if el >= 89:
        cam.SetPosition(focus[0], focus[1], focus[2] + dist); cam.SetViewUp(0, 1, 0)
    else:
        cam.SetPosition(focus[0], focus[1] - dist, focus[2]); cam.SetViewUp(0, 0, 1)
        cam.Azimuth(az); cam.Elevation(el)
    cam.OrthogonalizeViewUp(); cam.SetViewAngle(20)
    ren.ResetCamera(); cam.Zoom(zoom)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(path); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()

def render(d, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    f = lambda name: os.path.join(d, name + ".stl")
    o = lambda name: os.path.join(out_dir, name + ".png")
    tea = tealight(os.path.join(TMP, "tealight.stl"))
    flame_z = POCKET_FLOOR + TEA_H - 8
    scene = lambda crystal_dz=0, tea_dz=0, lit=False: [
        actor(f("base"), WHITE),
        actor(tea, FLAME if lit else CANDLE, (0, 0, POCKET_FLOOR + tea_dz), glow=0.75 if lit else 0.0),
        actor(f("crystal"), (0.45, 0.75, 1.0) if lit else BLUE, (0, 0, SOCKET_FLOOR + crystal_dz),
              opacity=0.6, glow=0.7 if lit else 0.0),
    ]
    mid = (0, 0, 76)
    shot(scene(), o("crystal"), mid, -25, 12, 1.05)
    shot(scene(lit=True), o("crystal_lit"), mid, -25, 12, 1.05, dark=True, lamp=(0, 0, flame_z))
    shot(scene(70, 30), o("crystal_open"), (0, 0, 110), -25, 14, 1.0)
    cut = [actor(halved(f("base"), 0), WHITE), actor(halved(tea, POCKET_FLOOR), CANDLE),
           actor(halved(f("crystal"), SOCKET_FLOOR), BLUE)]
    shot(cut, o("crystal_section"), mid, 0, 0, 1.05)
    shot([actor(f("base"), WHITE)], o("base_top"), (0, 0, 8), 0, 90, 1.1, size=(1000, 1000))

if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "stl"),
           sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "images"))
