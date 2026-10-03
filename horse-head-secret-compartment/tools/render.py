#!/usr/bin/env python3
"""Smooth-shaded preview renders of an STL (VTK, off-screen).

    python3 tools/render.py <mesh.stl> <out_prefix> [view ...]

Views are named azimuth/elevation pairs (degrees) around the model's
vertical axis; the model is assumed +z up, +y forward.
"""
import sys, vtk

VIEWS = {"eyeside": (85, 5), "eyeq": (55, 10), "muzzle": (25, 15), "side": (90, 8), "threeq": (45, 15), "front": (0, 10), "left": (-90, 8),
         "back": (180, 15), "high": (60, 40), "low": (30, -15), "under": (60, -45), "under2": (120, -45)}

def render(stl, out, views, size=(1000, 1000), color=(0.80, 0.62, 0.42)):
    r = vtk.vtkSTLReader(); r.SetFileName(stl)
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort())
    n.SetFeatureAngle(70); n.SplittingOff(); n.ConsistencyOn()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m)
    p = a.GetProperty(); p.SetColor(*color); p.SetInterpolationToPhong()
    p.SetAmbient(0.22); p.SetDiffuse(0.78); p.SetSpecular(0.18); p.SetSpecularPower(25)
    ren = vtk.vtkRenderer(); ren.AddActor(a)
    ren.GradientBackgroundOn(); ren.SetBackground(0.93, 0.93, 0.92); ren.SetBackground2(0.99, 0.99, 0.99)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.AddRenderer(ren); win.SetSize(*size)
    ren.AutomaticLightCreationOff()
    for pos, inten in (((1.0, 1.2, 1.6), 1.0), ((-1.4, 0.3, 0.6), 0.45), ((0.2, -1.5, 0.4), 0.35)):
        l = vtk.vtkLight(); l.SetLightTypeToCameraLight(); l.SetPosition(*pos); l.SetFocalPoint(0, 0, 0)
        l.SetIntensity(inten); ren.AddLight(l)
    b = r.GetOutput(); r.Update(); b = r.GetOutput().GetBounds()
    c = [(b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2]
    for v in views:
        az, el = VIEWS[v] if isinstance(v, str) else v
        cam = ren.GetActiveCamera()
        cam.SetFocalPoint(*c); cam.SetPosition(c[0], c[1] + 500, c[2]); cam.SetViewUp(0, 0, 1)
        cam.Azimuth(az); cam.Elevation(el); cam.OrthogonalizeViewUp()
        cam.ParallelProjectionOff(); cam.SetViewAngle(22)
        ren.ResetCamera(); cam.Zoom(1.15)
        win.Render()
        w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
        wr = vtk.vtkPNGWriter(); wr.SetFileName(f"{out}_{v if isinstance(v, str) else '%d_%d' % v}.png")
        wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()

if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3:] or ["side", "threeq", "front"])
