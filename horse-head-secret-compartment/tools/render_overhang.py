#!/usr/bin/env python3
"""Render a mesh with faces coloured by overhang (red > 65 deg from vertical, orange > 50).
    python3 tools/render_overhang.py mesh.stl out_prefix view..."""
import sys, numpy as np, trimesh, vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
sys.path.insert(0, "tools"); from render import VIEWS
m = trimesh.load(sys.argv[1]); n = m.face_normals
over = np.degrees(np.arcsin(np.clip(-n[:, 2], 0, 1)))       # 0 = vertical wall, 90 = flat ceiling
col = np.tile([205, 160, 110], (len(n), 1)).astype(np.uint8)
col[over > 50] = [240, 150, 30]; col[over > 65] = [220, 30, 30]
pts = vtk.vtkPoints(); pts.SetData(numpy_to_vtk(m.vertices.astype(np.float64), deep=True))
cells = np.hstack([np.full((len(m.faces), 1), 3), m.faces]).astype(np.int64).ravel()
ca = vtk.vtkCellArray(); ca.SetCells(len(m.faces), numpy_to_vtkIdTypeArray(cells, deep=True))
pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(ca)
c = numpy_to_vtk(col, deep=True); c.SetName("c"); pd.GetCellData().SetScalars(c)
mp = vtk.vtkPolyDataMapper(); mp.SetInputData(pd); mp.SetColorModeToDirectScalars()
a = vtk.vtkActor(); a.SetMapper(mp)
ren = vtk.vtkRenderer(); ren.AddActor(a); ren.SetBackground(1, 1, 1)
win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.AddRenderer(ren); win.SetSize(900, 900)
b = m.bounds; ctr = b.mean(0)
for v in sys.argv[3:]:
    az, el = VIEWS[v]
    cam = ren.GetActiveCamera(); cam.SetFocalPoint(*ctr); cam.SetPosition(ctr[0], ctr[1] + 500, ctr[2]); cam.SetViewUp(0, 0, 1)
    cam.Azimuth(az); cam.Elevation(el); cam.OrthogonalizeViewUp(); ren.ResetCamera(); cam.Zoom(1.2)
    win.Render(); w = vtk.vtkWindowToImageFilter(); w.SetInput(win); w.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(f"{sys.argv[2]}_{v}.png"); wr.SetInputConnection(w.GetOutputPort()); wr.Write()
