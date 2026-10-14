#!/usr/bin/env python3
"""Preview renders (VTK, off-screen; on a headless machine run it under xvfb-run).

    python3 render.py            stl/ -> images/

Writes:
    samosa.png          three-quarter view, the seam side
    samosa_back.png     from the other side
    samosa_scale.png    next to a credit card (85.6 x 54 mm) for size
    dip.png             the dipping cup with the sauce in it
    dip_parts.png       the cup and the sauce apart, as they print
    samosa_dip.png      the samosa with its dipping cup
"""
import os, sys
import vtk
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_dip import FLOOR

HERE = os.path.dirname(os.path.abspath(__file__))
PASTRY = (0.86, 0.62, 0.30)
CARD = (0.30, 0.45, 0.75)
CUP = (0.95, 0.94, 0.90)
SAUCE = (0.75, 0.12, 0.10)

def actor(src, colour, move=(0, 0, 0), spec=0.25):
    if isinstance(src, str):
        r = vtk.vtkSTLReader(); r.SetFileName(src); src = r
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(src.GetOutputPort()); n.SetFeatureAngle(60)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.SetPosition(*move)
    p = a.GetProperty(); p.SetColor(*colour); p.SetInterpolationToPhong()
    p.SetAmbient(0.2); p.SetDiffuse(0.8); p.SetSpecular(spec); p.SetSpecularPower(25)
    return a

def card():
    c = vtk.vtkCubeSource(); c.SetXLength(85.6); c.SetYLength(54.0); c.SetZLength(0.8)
    return c

def shot(actors, path, focus, az, el, zoom=1.0, size=(1200, 1000), dist=500):
    ren = vtk.vtkRenderer()
    for a in actors: ren.AddActor(a)
    ren.GradientBackgroundOn(); ren.SetBackground(0.93, 0.93, 0.92); ren.SetBackground2(0.99, 0.99, 0.99)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetMultiSamples(8)
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
    s = os.path.join(d, "samosa.stl")
    o = lambda name: os.path.join(out_dir, name + ".png")
    mid = (0, 0, 22)
    shot([actor(s, PASTRY)], o("samosa"), mid, 150, 18, 1.15)
    shot([actor(s, PASTRY)], o("samosa_back"), mid, -30, 18, 1.15)
    shot([actor(s, PASTRY), actor(card(), CARD, (100, -5, 0.4), 0.1)], o("samosa_scale"),
         (50, 0, 20), 160, 25, 1.25, size=(1400, 900))
    cup, sauce = os.path.join(d, "dip_cup.stl"), os.path.join(d, "dip_sauce.stl")
    in_cup = (0, 0, FLOOR + 0.05)
    shot([actor(cup, CUP), actor(sauce, SAUCE, in_cup, 0.6)], o("dip"), (0, 0, 15), 20, 40, 1.2,
         size=(1000, 900))
    shot([actor(cup, CUP, (-40, 0, 0)), actor(sauce, SAUCE, (40, 0, 0), 0.6)], o("dip_parts"),
         (0, 0, 15), 10, 22, 1.15, size=(1400, 800))
    shot([actor(s, PASTRY, (-35, 0, 0)), actor(cup, CUP, (55, 10, 0)),
          actor(sauce, SAUCE, (55, 10, FLOOR + 0.05), 0.6)], o("samosa_dip"),
         (10, 5, 18), 160, 28, 1.2, size=(1400, 900))

if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "stl"),
           sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "images"))
