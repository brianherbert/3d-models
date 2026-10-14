# Samosa

A life-size samosa, standing on its flat triangular bottom the way it sits
on a plate. It's the size of a real Punjabi samosa: 86 mm across the
bottom corners and 55 mm tall, so it fits easily in a cereal box. Lay it on
its side, with the tip pointing to the front or back of the box. A standard
box is about 65–75 mm deep. It prints in one piece, in one colour, with
no supports.

| | | |
|---|---|---|
| ![samosa](images/samosa.png) | ![back](images/samosa_back.png) | ![scale](images/samosa_scale.png) |

The last picture shows it next to a credit card (85.6 × 54 mm) for size.

## What it is

- **Shape:** a plump three-sided pastry cone. The bottom is a triangle with
  rounded corners, about 92 mm on each side if the corners were sharp. The
  faces bulge out where the filling pushes the pastry, and the top comes to
  a rounded point.
- **Seam:** one face has the overlapping flap where the pastry was folded
  and sealed, with a slightly wavy edge, the way a hand-folded one looks.
- **Surface:** smooth pastry with a very slight hand-made unevenness and a
  few soft bubbles. The bottom 2 mm are smooth and flat so it sits flat on the bed and
  on a plate.

## Printing

Open `samosa.3mf` in Bambu Studio. It has one plate with these settings on
top of **0.20mm Standard @BBL A1**:

| Setting | Value | Why |
|---|---|---|
| Supports | off | nothing overhangs more than 40°; the build script checks this |
| Brim | off | it stands on a wide flat triangle |
| Walls | 3 | |
| Infill | 15% | |
| Seam | aligned | keeps the seam to one line on the smooth surface |

- **Filament:** a tan, golden or light-brown PLA looks most like fried
  pastry. A matte PLA looks better still, because it hides the layer lines.
  The project uses the **Bambu PLA Basic** profile, so switch it to your
  filament's profile if it's different.
- **How much:** roughly 40–45 g of filament (my estimate from the model's
  volume and surface; Bambu Studio will show the exact amount and time when
  you slice).
- Or import `stl/samosa.stl` and use the settings above.

**Making it look cooked:** for a school project, a quick dry-brush of darker
brown acrylic paint over the bumps picks out the seam and the soft bumps, and
makes it look fried.

## Changing it

The parameters at the top of `build_samosa.py` set:

- `SIDE` and `HEIGHT`, the size (92 mm and 55 mm; keep `HEIGHT` under
  about 60 mm if it has to fit in a cereal box)
- `FACE_BULGE` and `BELLY`, how plump it is
- `SEAM_STEP` and `SEAM_AT`, the folded flap
- `LUMP_AMP`, `BLISTERS`, `BLISTER_AMP` and `BLISTER_SIZE`, the surface
  (raise them for a bumpier, more blistered pastry)
- `SEED`, for a slightly different samosa each time (useful for printing a plateful)

The script stops with an error if a change makes any part overhang more than
40° (it would need supports) or breaks the mesh.

```
pip install trimesh numpy scipy vtk pillow
python3 build_samosa.py        # -> stl/
xvfb-run -a python3 render.py  # -> images/ (drop xvfb-run on a desktop)
python3 make_3mf.py            # -> samosa.3mf
```

## Files

| File | What |
|---|---|
| `build_samosa.py` | Builds the samosa. Its key dimensions are parameters at the top. |
| `render.py` | Preview renders (VTK). |
| `make_3mf.py` | Builds the Bambu Studio project with `../tools/bambu3mf.py`. |
| `samosa.3mf` | The Bambu Studio project, ready to slice. |
| `stl/samosa.stl` | The samosa. |
