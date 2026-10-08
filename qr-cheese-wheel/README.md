# QR Cheese Wheel

A Swiss-cheese wheel with one wedge cut. Slide the wedge out and a QR code is
waiting underneath, with ありがとう ("thank you") above it. It's a way to hand
over a digital gift card in person. This is the bigger version of the
[QR cheese wedge](../qr-cheese-wedge/).

| Closed | Open |
|---|---|
| ![closed](images/wheel_closed.png) | ![open](images/wheel_open.png) |

![reveal](images/wheel_reveal.png)
*Looking down into the notch with the wedge out. The renders and `stl/tile*`
use a placeholder link (olympiaprovisions.com). Build your own tile as
described below.*

## How it works

The model has three parts:

- **Wheel:** 210 mm across and 36 mm tall, with an 80° notch.
  - At the bottom of the notch is a shallow bay for the tile.
  - At the rim, a 3 mm lip closes the bay so the tile can't slide out with the
    wedge.
- **Wedge:** sits in the notch on top of the tile, flush with the wheel's top
  and rind, with 0.3 mm clearance on each side.
  - The notch is open at the rim and its walls fan out from the centre, so the
    wedge comes free as soon as you slide it outward.
  - The big dimple on top is for a fingertip: press and pull toward you.
- **Tile:** a 1.6 mm yellow plate with the QR code and ありがとう standing
  0.8 mm proud in a dark colour.
  - It drops into the bay with 0.25 mm clearance.
  - The code reads upright for someone at the rim looking in, which is where
    you are once you've pulled the wedge out.

**The tile is the only part that holds the link.** The wheel and wedge are the
same for every build, so they live in `stl/`. If you want to give another gift
card later, you only need to print a new tile.

**Holes:** bubbles on the notch walls are shared, leaving half a dent in the
wheel and half in the wedge, so they line up when the wedge is in. There are
more holes round the rind and craters on top. Every side hole has a 45° pointed
roof, so nothing needs supports.

**QR code:** the build fits the largest square it can on the tile, which is
53 mm here.
- A ~90-character link (41 × 41 modules, error correction M) gets 1.3 mm
  modules. Shorter links get bigger modules, up to 1.6 mm.
- The build refuses links that would need modules finer than 1.1 mm.
- For bigger modules, raise `WHEEL_D` or `ANGLE` in `build_wheel.py`. The
  wheel has to stay under 256 mm to fit the A1.

## Making your tile

> **A gift-card QR code is the gift card.** Anyone who scans it can spend it.
> Keep the tile out of git and out of photos.

```
pip install qrcode manifold3d trimesh numpy matplotlib pillow vtk
python3 build_wheel.py "https://your-link-here"            # -> private/tile*.stl (git-ignored)
xvfb-run -a python3 render.py private private               # optional renders (plain `python3` on a desktop)
python3 make_3mf.py private                                 # -> private/tile.3mf
```

**Before you print, test the scan.** Point your phone at
`private/tile_top.png` or `private/wheel_reveal.png` on screen. ありがとう needs
a Japanese font (the script looks for IPAGothic, Hiragino or MS Gothic). Set
`THANKS = ""` to leave it off, or change the text.

Run `build_wheel.py` with no link to rebuild the wheel, the wedge and the
placeholder tile in `stl/`. Then run `python3 make_3mf.py` for their projects.

## Files

| File | What |
|---|---|
| `stl/wheel.3mf`, `stl/wedge.3mf` | Bambu Studio projects, one part per plate, in yellow. |
| `stl/tile.3mf` | Placeholder tile project, with two filaments assigned. |
| `stl/wheel.stl`, `stl/wedge.stl` | The same parts as plain STLs. |
| `stl/tile.stl` | Placeholder tile as one mesh, for a manual filament swap. |
| `stl/tile_plate.stl`, `stl/tile_qr.stl` | The tile's two colours as separate meshes that line up. |
| `build_wheel.py` | Builds all of the above. Its key dimensions are parameters at the top. |
| `make_3mf.py`, `bambu_profiles/` | The project builder and the A1 presets. |
| `render.py` | Preview renders. The top views double as a scan test. |

## Printing

All three parts print flat on their bottoms with no supports. They use
**Bambu Lab A1 0.4 nozzle**, **Bambu PLA Basic**, **0.16mm High Quality**, with
no brim.

1. **Wheel** (`wheel.3mf`), in yellow. It's the big one, filling most of the
   plate.
   - Lightning infill at 10% keeps it light, because it only has to hold up
     the top.
   - The seam is at the back.
2. **Wedge** (`wedge.3mf`), in yellow, with the same settings.
3. **Tile** (`private/tile.3mf`): slot 1 is yellow and slot 2 is dark.
   - Everything up to 1.6 mm is the plate. Everything above is the code and
     the text, so there's exactly one colour change.
   - **Without an AMS:** import `tile.stl` instead and add a pause at the
     first layer above **1.60 mm**. Swap to the dark filament and resume.
   - Use a matte filament for the cheese. Glare from silk or shiny PLA can
     stop phones reading the code.

**Assembly:** drop the tile into the bay with the code facing up and
ありがとう toward the centre. Slide the wedge in on top. Nothing is glued, so
the tile stays put because the lip and walls hold it, and the wedge rests on
it.

As a rough estimate, all three parts take 150–200 g of PLA in total. Most of
that is the wheel's outer shell.
