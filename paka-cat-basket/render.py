#!/usr/bin/env python3
"""Preview renders (VTK, off-screen; on a headless machine run it under xvfb-run).

    python3 render.py            -> images/

Writes:
    basket.png        the basket with a bag of treats and two toy balls in it
    basket_empty.png  the empty basket from the front corner
    front.png         straight on from the front
    plaque.png        close-up of the paw and the name
    weave.png         close-up of the weave on the end wall
    top.png           looking down into it
"""
import os, sys
import numpy as np, vtk, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_basket as B

HERE = os.path.dirname(os.path.abspath(__file__))
CANE = (0.80, 0.66, 0.46)       # natural / tan PLA
BAG = (0.18, 0.42, 0.72)
BALL = (0.93, 0.35, 0.30)
BALL2 = (0.98, 0.80, 0.22)


def poly(t):
    pts = vtk.vtkPoints()
    pts.SetData(__import__("vtk.util.numpy_support", fromlist=["x"]).numpy_to_vtk(np.asarray(t.vertices, float), deep=True))
    faces = np.hstack([np.full((len(t.faces), 1), 3), t.faces]).astype(np.int64).ravel()
    cells = vtk.vtkCellArray()
    cells.SetCells(len(t.faces), __import__("vtk.util.numpy_support", fromlist=["x"]).numpy_to_vtkIdTypeArray(faces, deep=True))
    p = vtk.vtkPolyData(); p.SetPoints(pts); p.SetPolys(cells)
    return p


def actor(t, colour, spec=0.15):
    n = vtk.vtkPolyDataNormals(); n.SetInputData(poly(t)); n.SetFeatureAngle(50)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m)
    p = a.GetProperty(); p.SetColor(*colour); p.SetInterpolationToPhong()
    p.SetAmbient(0.2); p.SetDiffuse(0.8); p.SetSpecular(spec); p.SetSpecularPower(25)
    return a


def shot(actors, path, focus, offset, size=(1200, 1000), angle=20, fit=False):
    """camera at focus + offset looking at focus; ambient occlusion so the relief and the weave read"""
    ren = vtk.vtkRenderer()
    for a in actors: ren.AddActor(a)
    ren.GradientBackgroundOn(); ren.SetBackground(0.93, 0.93, 0.92); ren.SetBackground2(0.99, 0.99, 0.99)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetMultiSamples(8)
    win.AddRenderer(ren); win.SetSize(*size)
    ren.AutomaticLightCreationOff()
    for pos, inten in (((0.6, 1.0, 1.6), 0.95), ((-1.4, 0.3, 0.6), 0.4), ((0.2, -1.5, 0.4), 0.3)):
        l = vtk.vtkLight(); l.SetLightTypeToCameraLight(); l.SetPosition(*pos); l.SetFocalPoint(0, 0, 0)
        l.SetIntensity(inten); ren.AddLight(l)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(*focus); cam.SetPosition(*(np.add(focus, offset)))
    cam.SetViewUp(0, 1, 0) if abs(offset[0]) + abs(offset[1]) < 1e-6 else cam.SetViewUp(0, 0, 1)
    cam.SetViewAngle(angle); ren.ResetCameraClippingRange()
    ren.UseSSAOOn(); ren.SetSSAORadius(4.0); ren.SetSSAOBias(0.3); ren.SetSSAOKernelSize(128); ren.SSAOBlurOn()
    win.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(path); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
    print("wrote", path)


def main():
    out = os.path.join(HERE, "images"); os.makedirs(out, exist_ok=True)
    basket = trimesh.load(os.path.join(HERE, "stl", "basket.stl"))
    bag = trimesh.load(os.path.join(HERE, "stl", "treat_bag.stl"))
    bag.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-8), (1, 0, 0)))
    bag.apply_translation((-32 - bag.centroid[0], 12 - bag.bounds[0][1], B.FLOOR_T - bag.bounds[0][2]))
    balls = []
    for (x, y), c in (((76, -40), BALL), ((72, 18), BALL2)):
        s = trimesh.creation.icosphere(4, 19.0); s.apply_translation((x, y, B.FLOOR_T + 19.0))
        balls.append((s, c))
    mid = (0, 0, 52)
    full = [actor(basket, CANE), actor(bag, BAG, 0.35)] + [actor(s, c, 0.3) for s, c in balls]
    shot(full, os.path.join(out, "basket.png"), (0, 0, 72), (-360, -620, 360))
    shot([actor(basket, CANE)], os.path.join(out, "basket_empty.png"), mid, (-330, -560, 300))
    shot([actor(basket, CANE)], os.path.join(out, "front.png"), mid, (0, -560, 30), size=(1300, 800))
    shot([actor(basket, CANE)], os.path.join(out, "plaque.png"), (0, -70, B.PLAQUE_ZC), (15, -300, 15), size=(1000, 700))
    shot([actor(basket, CANE)], os.path.join(out, "weave.png"), (100, 0, 56), (300, -25, 25), size=(900, 900))
    shot([actor(basket, CANE)], os.path.join(out, "top.png"), (0, 0, 0), (0, 0, 640), size=(1200, 900))


if __name__ == "__main__":
    main()
