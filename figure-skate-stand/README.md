# Figure skate stand

A plain round stand that holds a figure skate upright on a table. The blade
drops into a groove across the top and the skate stands on its own.

![the stand](images/stand.png)

| | |
|---|---|
| ![with a blade](images/stand_blade.png) | ![cut through the groove](images/stand_section.png) |

The grey blade in the renders is a rough stand-in, just for scale.

There's also a **short version**, half as tall (1 in), with the same disc
and the same groove:

![the short version](images/stand_short.png)

## Size

- **Disc:** 101.6 mm (4 in) across and 50.8 mm (2 in) tall, solid. The
  short version is 25.4 mm (1 in) tall. Even on the short one, the blade
  stands about 15 mm clear of the table.
- **Groove:** 4.1 mm wide and 10 mm deep, straight across the whole top and
  out both sides, so a blade of any length fits. The blade's rocker (its
  curve) lifts its ends only about 0.6 mm over the 4 in of the disc, so a
  straight groove holds it along its full length.
- The groove has a 0.8 mm lead-in along both top edges to guide the blade
  in, the top edge of the disc has a 1.5 mm chamfer, and the bottom edge
  has a 0.6 mm chamfer so the first layer doesn't leave a lip.

## Printing

Open `figure_skate_stand.3mf` (2 in) or `figure_skate_stand_short.3mf`
(1 in) in Bambu Studio. Each has one plate on
**0.20mm Standard @BBL A1**, with the stand groove up. Print in white PLA.

| Setting | Value | Why |
|---|---|---|
| Supports | off | the groove is open at the top, so nothing overhangs |
| Brim | off | it lies on a wide flat bottom |
| Walls | 3 | |
| Infill | 15% | |

- **Filament:** about 110 g for the tall one and 65 g for the short one (my estimates from the walls and 15% infill;
  Bambu Studio will show the exact amount when you slice). For a heavier,
  steadier stand, raise the infill.
- **Fit:** printed slots often come out a touch narrower than drawn. If the
  blade is tight, raise `GROOVE_W` to 4.2 or 4.3 and rebuild; if it's
  loose, lower it.

## Changing it

The parameters at the top of `build.py` set the disc (`DISC_D`, `DISC_H`, `SHORT_H`,
`TOP_CHAMFER`, `FOOT_CHAMFER`) and the groove (`GROOVE_W`, `GROOVE_DEPTH`,
`GROOVE_LEAD`). The script checks the mesh is watertight and measures the
groove's width and depth before writing the STL.

```
pip install trimesh numpy manifold3d vtk
python3 build.py               # -> stl/stand.stl, stl/stand_short.stl
xvfb-run -a python3 render.py  # -> images/ (drop xvfb-run on a desktop)
python3 make_3mf.py            # -> figure_skate_stand.3mf
```

## Files

| File | What |
|---|---|
| `build.py` | Builds both stands. Its key dimensions are parameters at the top. |
| `render.py` | Preview renders (VTK), with a stand-in blade for scale. |
| `make_3mf.py` | Builds the Bambu Studio projects with `../tools/bambu3mf.py`. |
| `figure_skate_stand.3mf` | The Bambu Studio project for the 2 in stand, ready to slice. |
| `figure_skate_stand_short.3mf` | The same for the 1 in stand. |
| `stl/stand.stl` | The 2 in stand. |
| `stl/stand_short.stl` | The 1 in stand. |
