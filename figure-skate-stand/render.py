#!/usr/bin/env python3
"""Preview renders (VTK, off-screen; on a headless machine run it under xvfb-run).

    python3 render.py            stl/ -> images/

Writes:
    stand.png          the stand on its own
    stand_blade.png    with a stand-in figure skate blade slotted in
    stand_top.png      from above
    stand_section.png  cut across the groove, with the blade in
    stand_short.png    the short (1 in) version, with the blade in
    stand_3in.png      the 3 in wide version, 2 in tall, with the blade in
    stand_3in_short.png  the 3 in wide version, 1 in tall, with the blade in
"""
import os, sys, tempfile
import numpy as np, trimesh, vtk
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build import DISC_H, SHORT_H, GROOVE_DEPTH, to_trimesh

WHITE = (0.95, 0.94, 0.90)
STEEL = (0.72, 0.74, 0.78)
TMP = tempfile.mkdtemp()

def blade(path):
    """A rough figure skate blade, 3.9 mm thick: a long runner with a rocker
    (about a 2.2 m radius), a toe pick at the front and two stanchions up to
    the boot's sole plate. Only for scale."""
    L, T, H = 290.0, 3.9, 22.0
    R = 2200.0
    rocker = mf.Manifold.cylinder(T, R, R, 2048).rotate([90, 0, 0]).translate([0, T / 2, R])
    runner = mf.Manifold.cube([L, T, H], True).translate([0, 0, H / 2]) ^ rocker
    pick = mf.Manifold.hull_points([[L / 2 - 2, -T / 2, 6], [L / 2 - 2, T / 2, 6], [L / 2 + 14, -T / 2, 20],
                                    [L / 2 + 14, T / 2, 20], [L / 2 - 2, -T / 2, H], [L / 2 - 2, T / 2, H]])
    stanch = mf.Manifold()
    for x, w in ((95, 50), (-105, 40)):
        stanch += mf.Manifold.cube([w, T, 45], True).translate([x, 0, H + 20])
    plate = mf.Manifold.cube([L - 20, 60, 4], True).translate([0, 0, H + 44])
    t = to_trimesh(runner + pick + stanch + plate)
    t.export(path)
    return path

def actor(path, colour, move=(0, 0, 0)):
    r = vtk.vtkSTLReader(); r.SetFileName(path)
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(30)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.SetPosition(*move)
    p = a.GetProperty(); p.SetColor(*colour); p.SetInterpolationToPhong()
    p.SetAmbient(0.25); p.SetDiffuse(0.75); p.SetSpecular(0.25); p.SetSpecularPower(30)
    return a

def halved(path, dz):
    t = trimesh.load(path); t.apply_translation([0, 0, dz])
    m = mf.Manifold(mf.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))
    out = os.path.join(TMP, "cut_" + os.path.basename(path))
    to_trimesh(m.trim_by_plane([-1, 0, 0], 0)).export(out)
    return out

def shot(actors, path, focus, az, el, zoom=1.0, size=(1200, 900), dist=700):
    ren = vtk.vtkRenderer()
    for a in actors: ren.AddActor(a)
    ren.GradientBackgroundOn(); ren.SetBackground(0.93, 0.93, 0.92); ren.SetBackground2(0.99, 0.99, 0.99)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetMultiSamples(0)
    win.AddRenderer(ren); win.SetSize(*size)
    ren.AutomaticLightCreationOff()
    for pos, inten in (((0.6, 1.0, 1.6), 0.95), ((-1.4, 0.3, 0.6), 0.4), ((0.2, -1.5, 0.4), 0.3)):
        l = vtk.vtkLight(); l.SetLightTypeToCameraLight(); l.SetPosition(*pos); l.SetFocalPoint(0, 0, 0)
        l.SetIntensity(inten); ren.AddLight(l)
    cam = ren.GetActiveCamera(); cam.SetFocalPoint(*focus)
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
    stand = os.path.join(d, "stand.stl")
    o = lambda name: os.path.join(out_dir, name + ".png")
    b = blade(os.path.join(TMP, "blade.stl"))
    # the blade's lowest point is at x=0, z=0: drop it to the groove floor
    seat = (0, 0, DISC_H - GROOVE_DEPTH)
    shot([actor(stand, WHITE)], o("stand"), (0, 0, 25), -30, 25, 1.1)
    shot([actor(stand, WHITE), actor(b, STEEL, seat)], o("stand_blade"), (0, 0, 50), -35, 18, 1.05)
    shot([actor(stand, WHITE)], o("stand_top"), (0, 0, 25), 0, 90, 1.15, size=(1000, 1000))
    shot([actor(halved(stand, 0), WHITE), actor(halved(b, seat[2]), STEEL)], o("stand_section"),
         (0, 0, 45), 90, 0, 1.0, size=(1000, 1000))
    short = os.path.join(d, "stand_short.stl")
    shot([actor(short, WHITE), actor(b, STEEL, (0, 0, SHORT_H - GROOVE_DEPTH))], o("stand_short"),
         (0, 0, 40), -35, 18, 1.05)
    for name, h in (("stand_3in", DISC_H), ("stand_3in_short", SHORT_H)):
        shot([actor(os.path.join(d, name + ".stl"), WHITE), actor(b, STEEL, (0, 0, h - GROOVE_DEPTH))],
             o(name), (0, 0, 40 if h == SHORT_H else 50), -35, 18, 1.05)

if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "stl"),
           sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "images"))
