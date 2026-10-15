#!/usr/bin/env python3
"""Preview renders (VTK, off-screen; on a headless machine run it under xvfb-run).

    python3 render.py            -> images/

Writes:
    basket.png          the basket with the two pears, the cookie and the snack bag in it
    basket_top.png      looking down into it
    basket_empty.png    the empty basket and its handle
    parts.png           everything laid out as it prints
    treats.png          a pear, the cookie and the snack bag on their own
    samosa_compare.png  next to the samosa, for size
"""
import os, sys
import vtk, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_basket as B

HERE = os.path.dirname(os.path.abspath(__file__))
WICKER = (0.55, 0.36, 0.20)
PEAR = (0.62, 0.74, 0.25)
COOKIE = (0.85, 0.64, 0.38)
BAG = (0.93, 0.45, 0.12)
PASTRY = (0.86, 0.62, 0.30)


def poly(t):
    pts = vtk.vtkPoints()
    for v in t.vertices: pts.InsertNextPoint(*v)
    cells = vtk.vtkCellArray()
    for f in t.faces:
        cells.InsertNextCell(3); [cells.InsertCellPoint(int(i)) for i in f]
    p = vtk.vtkPolyData(); p.SetPoints(pts); p.SetPolys(cells)
    return p


def actor(t, colour, move=(0, 0, 0), spec=0.2):
    if isinstance(t, str):
        t = trimesh.load(t)
    n = vtk.vtkPolyDataNormals(); n.SetInputData(poly(t)); n.SetFeatureAngle(50)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.SetPosition(*move)
    p = a.GetProperty(); p.SetColor(*colour); p.SetInterpolationToPhong()
    p.SetAmbient(0.2); p.SetDiffuse(0.8); p.SetSpecular(spec); p.SetSpecularPower(25)
    return a


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


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    o = lambda name: os.path.join(out_dir, name + ".png")
    parts, _, _, items, h_in = B.build()
    bk = actor(parts["basket"], WICKER)
    full = [bk, actor(h_in, WICKER), actor(items["pear"], PEAR), actor(items["pear_2"], PEAR),
            actor(items["cookie"], COOKIE),
            actor(items["snack_bag"], BAG, spec=0.45)]
    shot(full, o("basket"), (0, 0, 32), 25, 22, 1.15)
    shot(full, o("basket_top"), (0, 0, 20), 0, 90, 1.25)
    shot([bk, actor(h_in, WICKER)], o("basket_empty"), (0, 0, 32), -30, 18, 1.15)
    lay = [actor(parts["basket"], WICKER, (-20, 0, 0)), actor(parts["handle"], WICKER, (75, -20, 0)),
           actor(parts["pear"], PEAR, (-45, -65, 0)), actor(parts["pear"], PEAR, (-15, -65, 0)),
           actor(parts["cookie"], COOKIE, (20, -65, 0)),
           actor(parts["snack_bag"], BAG, (55, -60, 0), 0.45)]
    shot(lay, o("parts"), (20, -25, 10), 0, 50, 1.2, size=(1400, 1000))
    tr = [actor(parts["pear"], PEAR, (-35, 0, 0)), actor(parts["cookie"], COOKIE, (0, 0, 0)),
          actor(parts["snack_bag"], BAG, (40, 0, 0), 0.45)]
    shot(tr, o("treats"), (5, 0, 8), 0, 35, 1.2, size=(1400, 800))
    samosa = os.path.join(HERE, "..", "samosa", "stl", "samosa.stl")
    if os.path.exists(samosa):
        cmp = full + [actor(samosa, PASTRY, (100, 0, 0))]
        shot(cmp, o("samosa_compare"), (50, 0, 30), 10, 15, 1.2, size=(1400, 900))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "images"))
