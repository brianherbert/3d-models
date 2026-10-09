#!/usr/bin/env python3
"""Two-colour preview renders of a built wedge (VTK, off-screen).

    python3 render.py [stl_dir] [out_dir]

Writes wedge_iso.png, wedge_top.png (also used to check the QR decodes),
wedge_side.png and wedge_back.png.
"""
import os, sys, vtk

HERE = os.path.dirname(os.path.abspath(__file__))
CHEESE = (0.98, 0.80, 0.32)
INK = (0.16, 0.11, 0.08)
VIEWS = {"iso": (-35, 32), "top": (0, 90), "side": (-90, 12), "back": (180, 20)}

def actor(path, colour):
    r = vtk.vtkSTLReader(); r.SetFileName(path)
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(40)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m)
    p = a.GetProperty(); p.SetColor(*colour); p.SetInterpolationToPhong()
    p.SetAmbient(0.25); p.SetDiffuse(0.75); p.SetSpecular(0.12); p.SetSpecularPower(20)
    return a, r

def render(stl_dir, out_dir, size=(1200, 1000)):
    os.makedirs(out_dir, exist_ok=True)
    ren = vtk.vtkRenderer()
    a, r = actor(os.path.join(stl_dir, "cheese_body.stl"), CHEESE); ren.AddActor(a)
    q, _ = actor(os.path.join(stl_dir, "cheese_qr.stl"), INK); ren.AddActor(q)
    ren.GradientBackgroundOn(); ren.SetBackground(0.93, 0.93, 0.92); ren.SetBackground2(0.99, 0.99, 0.99)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.AddRenderer(ren); win.SetSize(*size)
    ren.AutomaticLightCreationOff()
    for pos, inten in (((0.6, 1.0, 1.6), 0.95), ((-1.4, 0.3, 0.6), 0.4), ((0.2, -1.5, 0.4), 0.3)):
        l = vtk.vtkLight(); l.SetLightTypeToCameraLight(); l.SetPosition(*pos); l.SetFocalPoint(0, 0, 0)
        l.SetIntensity(inten); ren.AddLight(l)
    r.Update(); b = r.GetOutput().GetBounds()
    c = [(b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2]
    for name, (az, el) in VIEWS.items():
        cam = ren.GetActiveCamera()
        cam.SetFocalPoint(*c); cam.SetViewUp(0, 0, 1)
        if el == 90:
            cam.SetPosition(c[0], c[1], c[2] + 600); cam.SetViewUp(1, 0, 0)   # the rind at the top of the picture
        else:
            cam.SetPosition(c[0], c[1] - 600, c[2]); cam.Azimuth(az); cam.Elevation(el)
        cam.OrthogonalizeViewUp(); cam.SetViewAngle(22)
        ren.ResetCamera(); cam.Zoom(1.25)
        win.Render()
        w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
        wr = vtk.vtkPNGWriter(); wr.SetFileName(os.path.join(out_dir, f"wedge_{name}.png"))
        wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()

if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "stl"),
           sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "images"))
