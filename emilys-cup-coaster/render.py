#!/usr/bin/env python3
"""Preview renders (VTK, off-screen; on a headless machine run it under xvfb-run).

    python3 render.py            stl/ -> images/

Writes, for each design (tab, arch, nameplate):
    <design>.png        three-quarter view from the front
    <design>_cup.png    with a 70 mm cup standing in it
and options.png, the three side by side.
"""
import os, sys
import vtk
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import BASE_H, POCKET_DEPTH, CUP_D, DESIGNS

HERE = os.path.dirname(os.path.abspath(__file__))
# the colours the projects use: base, letters
COLOURS = {
    "tab": ((0.96, 0.95, 0.92), (0.90, 0.36, 0.58)),        # white and pink
    "arch": ((0.74, 0.66, 0.88), (0.98, 0.98, 0.97)),       # lilac and white
    "nameplate": ((0.55, 0.80, 0.78), (0.98, 0.98, 0.97)),  # mint and white
}
CUP = (0.80, 0.86, 0.93)
# where the pocket is in each design (x, y), for standing the cup in it
POCKET_AT = {"tab": (0, 0), "arch": (0, 0)}


def actor(src, colour, move=(0, 0, 0), spec=0.25, opacity=1.0):
    if isinstance(src, str):
        r = vtk.vtkSTLReader(); r.SetFileName(src); src = r
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(src.GetOutputPort()); n.SetFeatureAngle(50)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.SetPosition(*move)
    p = a.GetProperty(); p.SetColor(*colour); p.SetInterpolationToPhong(); p.SetOpacity(opacity)
    p.SetAmbient(0.2); p.SetDiffuse(0.8); p.SetSpecular(spec); p.SetSpecularPower(25)
    return a


def cup():
    """a plain tumbler: 70 mm across the bottom, 82 mm across the top, 95 mm tall"""
    pts = vtk.vtkPoints()
    prof = [(0, 0), (CUP_D / 2 - 2, 0), (CUP_D / 2, 2), (41, 95), (38.5, 95), (36.5, 6), (0, 6)]
    for r, z in prof:
        pts.InsertNextPoint(r, 0, z)
    line = vtk.vtkPolyLine(); line.GetPointIds().SetNumberOfIds(len(prof))
    for i in range(len(prof)):
        line.GetPointIds().SetId(i, i)
    cells = vtk.vtkCellArray(); cells.InsertNextCell(line)
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetLines(cells)
    src = vtk.vtkTrivialProducer(); src.SetOutput(pd)
    rot = vtk.vtkRotationalExtrusionFilter(); rot.SetInputConnection(src.GetOutputPort()); rot.SetResolution(120)
    tri = vtk.vtkTriangleFilter(); tri.SetInputConnection(rot.GetOutputPort())
    return tri


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
    if el >= 89:                                          # straight down, front at the bottom
        cam.SetPosition(focus[0], focus[1], focus[2] + dist); cam.SetViewUp(0, 1, 0)
    else:
        cam.SetPosition(focus[0], focus[1] - dist, focus[2]); cam.SetViewUp(0, 0, 1)
        cam.Azimuth(az); cam.Elevation(el)
    cam.OrthogonalizeViewUp(); cam.SetViewAngle(20)
    ren.ResetCamera(); cam.Zoom(zoom)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(path); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()


def pocket_centre(d, name):
    """the pocket's centre: the middle of the circle of the cut, found from the base's floor"""
    if name in POCKET_AT:
        return POCKET_AT[name]
    r = vtk.vtkSTLReader(); r.SetFileName(os.path.join(d, name + ".stl")); r.Update()
    pts = r.GetOutput().GetPoints()
    floor = BASE_H - POCKET_DEPTH
    ys = [pts.GetPoint(i)[1] for i in range(pts.GetNumberOfPoints()) if abs(pts.GetPoint(i)[2] - floor) < 1e-3]
    return (0, (min(ys) + max(ys)) / 2)


def render(d, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    o = lambda name: os.path.join(out_dir, name + ".png")
    row = []
    for i, name in enumerate(DESIGNS):
        base, ink = COLOURS[name]
        parts = lambda move=(0, 0, 0): [actor(os.path.join(d, name + ".stl"), base, move),
                                        actor(os.path.join(d, name + "_text.stl"), ink, move, 0.4)]
        shot(parts(), o(name), (0, 0, 3), 0, 48, 1.25)
        px, py = pocket_centre(d, name)
        shot(parts() + [actor(cup(), CUP, (px, py, BASE_H - POCKET_DEPTH), 0.6, 0.55)], o(name + "_cup"),
             (0, 0, 30), 15, 22, 1.15, size=(1000, 1100))
        row += parts(((i - 1) * 140, 0, 0))
    shot(row, o("options"), (0, 0, 3), 0, 50, 2.1, size=(1800, 750))


if __name__ == "__main__":
    render(os.path.join(HERE, "stl"), os.path.join(HERE, "images"))
