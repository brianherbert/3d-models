#!/usr/bin/env python3
"""Preview renders (VTK, off-screen; on a headless machine run it under xvfb-run).

    python3 render.py [build_dir] [out_dir]          default: stl/ -> images/

Writes:
    wheel_closed.png     assembled
    wheel_open.png       wedge slid out, the code showing
    wheel_exploded.png   wheel, tile and wedge pulled apart vertically
    wheel_section.png    cut through the middle of the wedge: how the parts stack
    wheel_reveal.png     straight down into the open notch (also a scan test)
"""
import os, sys, tempfile
import numpy as np, trimesh, vtk
import manifold3d as mf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_wheel import BASE, TILE_TOP, HEIGHT

CHEESE = (0.98, 0.80, 0.32)
WEDGE = (0.99, 0.86, 0.45)      # a touch lighter in the exploded and section views, to tell the parts apart
TILE = (1.00, 0.92, 0.62)
INK = (0.16, 0.11, 0.08)
TMP = tempfile.mkdtemp()

def actor(path, colour, move=(0, 0, 0)):
    r = vtk.vtkSTLReader(); r.SetFileName(path)
    n = vtk.vtkPolyDataNormals(); n.SetInputConnection(r.GetOutputPort()); n.SetFeatureAngle(12)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m); a.SetPosition(*move)
    p = a.GetProperty(); p.SetColor(*colour); p.SetInterpolationToPhong()
    p.SetAmbient(0.25); p.SetDiffuse(0.75); p.SetSpecular(0.12); p.SetSpecularPower(20)
    return a

def halved(path, dz):
    """The part moved up by dz and cut along y = 0, keeping the y < 0 half."""
    t = trimesh.load(path); t.apply_translation([0, 0, dz])
    m = mf.Manifold(mf.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))
    g = m.trim_by_plane([0, -1, 0], 0).to_mesh()
    out = os.path.join(TMP, "cut_" + os.path.basename(path))
    trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts)).export(out)
    return out

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
    if scale:                                       # fixed framing, no perspective
        cam.ParallelProjectionOn(); cam.SetParallelScale(scale); ren.ResetCameraClippingRange()
    else:
        ren.ResetCamera(); cam.Zoom(zoom)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(path); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()

def render(d, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    R = float(open(os.path.join(d, "layout.txt")).read().split()[0])
    f = lambda name: os.path.join(d, name + ".stl")
    o = lambda name: os.path.join(out_dir, name + ".png")
    wheel = lambda c=CHEESE: actor(f("wheel"), c)
    wedge = lambda move, c=CHEESE: actor(f("wedge"), c, move)
    tile = lambda dz=BASE, c=CHEESE: [actor(f("tile_plate"), c, (0, 0, dz)), actor(f("tile_qr"), INK, (0, 0, dz))]

    shot([wheel(), wedge((0, 0, TILE_TOP))] + tile(), o("wheel_closed"), (0, 0, HEIGHT / 2), 30, 28)
    shot([wheel(), wedge((R * 0.9, 0, 0))] + tile(), o("wheel_open"), (R * 0.45, 0, HEIGHT / 2), 28, 34, 1.1)
    shot([wheel(), wedge((0, 0, TILE_TOP + 80), WEDGE)] + tile(BASE + 38, TILE),
         o("wheel_exploded"), (0, 0, 55), 35, 26, 1.05)
    cut = [actor(halved(f("wheel"), 0), CHEESE), actor(halved(f("wedge"), TILE_TOP), WEDGE),
           actor(halved(f("tile_plate"), BASE), TILE), actor(halved(f("tile_qr"), BASE), INK)]
    shot(cut, o("wheel_section"), (R - 22, 0, 11), 90, 6, scale=19)          # close-up at the rim
    shot([wheel()] + tile(), o("wheel_reveal"), (R * 0.5, 0, BASE), 0, 90, scale=R * 0.62)
    if os.path.exists(f("fit_test")):
        shot([actor(f("fit_test"), CHEESE)], o("fit_test"), (0, 0, 6), -90, 25, 1.1)

if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "stl"),
           sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "images"))
