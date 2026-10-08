#!/usr/bin/env python3
"""Preview renders (VTK, off-screen; on a headless machine run it under xvfb-run).

    python3 render.py [tile_dir] [out_dir]

The wheel and wedge come from stl/; the tile from tile_dir (default stl/).
Writes:
    wheel_closed.png   assembled
    wheel_open.png     wedge slid out, tile showing
    wheel_reveal.png   looking down into the open notch (also used to check the QR scans)
    tile_top.png       the tile on its own, straight down
"""
import os, sys, vtk

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_wheel import BASE, TILE_TOP, R, HEIGHT

CHEESE = (0.98, 0.80, 0.32)
INK = (0.16, 0.11, 0.08)

def actor(path, colour, move=(0, 0, 0)):
    r = vtk.vtkSTLReader(); r.SetFileName(path)
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(12)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.SetPosition(*move)
    p = a.GetProperty(); p.SetColor(*colour); p.SetInterpolationToPhong()
    p.SetAmbient(0.25); p.SetDiffuse(0.75); p.SetSpecular(0.12); p.SetSpecularPower(20)
    return a

def shot(actors, path, focus, az, el, zoom=1.2, size=(1200, 1000), dist=900, scale=None):
    ren = vtk.vtkRenderer()
    for a in actors: ren.AddActor(a)
    ren.GradientBackgroundOn(); ren.SetBackground(0.93, 0.93, 0.92); ren.SetBackground2(0.99, 0.99, 0.99)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.AddRenderer(ren); win.SetSize(*size)
    ren.AutomaticLightCreationOff()
    for pos, inten in (((0.6, 1.0, 1.6), 0.95), ((-1.4, 0.3, 0.6), 0.4), ((0.2, -1.5, 0.4), 0.3)):
        l = vtk.vtkLight(); l.SetLightTypeToCameraLight(); l.SetPosition(*pos); l.SetFocalPoint(0, 0, 0)
        l.SetIntensity(inten); ren.AddLight(l)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(*focus)
    if el >= 89:
        cam.SetPosition(focus[0], focus[1], focus[2] + dist); cam.SetViewUp(-1, 0, 0)   # rim at the bottom of the picture
    else:
        cam.SetPosition(focus[0] + dist, focus[1], focus[2]); cam.SetViewUp(0, 0, 1)
        cam.Azimuth(az); cam.Elevation(el)
    cam.OrthogonalizeViewUp(); cam.SetViewAngle(22)
    if scale:                                       # straight-down shots: fixed framing, no perspective
        cam.ParallelProjectionOn(); cam.SetParallelScale(scale); ren.ResetCameraClippingRange()
    else:
        ren.ResetCamera(); cam.Zoom(zoom)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(path); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()

def render(tile_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    stl = os.path.join(HERE, "stl")
    wheel = lambda: actor(os.path.join(stl, "wheel.stl"), CHEESE)
    tile = lambda: [actor(os.path.join(tile_dir, "tile_plate.stl"), CHEESE, (0, 0, BASE)),
                    actor(os.path.join(tile_dir, "tile_qr.stl"), INK, (0, 0, BASE))]
    wedge = lambda move: actor(os.path.join(stl, "wedge.stl"), CHEESE, move)
    mid = (0, 0, HEIGHT / 2)
    shot([wheel(), wedge((0, 0, TILE_TOP))] + tile(), os.path.join(out_dir, "wheel_closed.png"), mid, 35, 28)
    shot([wheel(), wedge((R * 0.85, 0, 0))] + tile(), os.path.join(out_dir, "wheel_open.png"), (R * 0.4, 0, HEIGHT / 2), 35, 30, 1.15)
    shot([wheel()] + tile(), os.path.join(out_dir, "wheel_reveal.png"), (R * 0.55, 0, BASE), 0, 90, scale=R * 0.6)
    shot(tile(), os.path.join(out_dir, "tile_top.png"), (R * 0.55, 0, BASE), 0, 90, scale=R * 0.5)

if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "stl"),
           sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "images"))
