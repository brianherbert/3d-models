# Horse Head with a Secret Compartment

A desk-size horse bust whose lower jaw swings open to reveal a hidden
compartment. **One print, one part, no assembly:** the jaw, its hinge pin and
a click detent are all printed in place. After printing you pull off the
slicer's supports under the muzzle, work the jaw a few times, and it's done.

| Closed | Open |
|---|---|
| ![closed](images/horse_closed.png) | ![open](images/horse_open.png) |

| Face | Side |
|---|---|
| ![face](images/horse_face.png) | ![side](images/horse_side.png) |

![cutaway](images/horse_cutaway.png)
*Section through the centre. The jaw (blue) hangs from a pin printed with the
body. The compartment is the hollow of the jaw plus a chamber above it inside
the face. The flexible tongue on the jaw's arm clicks into a dimple in the
slot wall when the mouth is shut.*

## What it is

- **Size:** 164 mm tall and 151 mm long, on an 88 × 121 mm plinth under the neck.
- **Sculpt:** an original parametric sculpt, not a downloaded model. It has a
  realistic, calm head carried low on an arched neck, with:
  - cupped, leaf-shaped ears;
  - lidded almond eyes under a bony brow;
  - flat cheeks with a defined jowl;
  - comma-shaped nostrils;
  - separate upper and lower lips and a chin;
  - a forelock and a mane of draped locks falling to the right.
- **Compartment:** about 16 cm³. The jaw is a hollow scoop with 2.2 mm
  walls, and it lines up with a chamber in the face above it. It holds a ring,
  a few coins, a USB stick, a folded note or a key. The mouth opens 16°,
  which leaves a gap of about 20 mm at the lips.
- **Hinge:** the jaw pivots where a real horse's does, just behind and below
  the eye.
  - The pin is printed as part of the head, running across an internal slot.
  - A ring on the end of the jaw's arm turns on the pin.
  - The visible seams follow the jaw line: from the corner of the mouth back
    under the cheek, then round the front of the jowl. A closed mouth looks
    like a closed mouth.
- **Detent:** the jaw's arm carries a thin flexible tongue on each face with a
  small nub. The nub clicks into a dimple when the mouth is shut, so the jaw
  doesn't fall open on its own. Pull the chin down past the click to open;
  push it up until it clicks to close.

## Files

| File | What |
|---|---|
| `horse_head.3mf` | **Open this in Bambu Studio.** A ready-to-print project with the model on an A1 plate and the print settings already chosen. |
| `stl/horse_head.stl` | The same part as a plain STL, for other slicers. Body and jaw in one file, already positioned. |
| `horse_sculpt.py` | The sculpt: a signed-distance-field model in Python. |
| `build_horse.py` | Cuts and hinges the jaw, hollows the compartment, adds the detent and the breakaway tabs, and meshes the part. |
| `verify_horse.py` | Checks: watertight, jaw swing without collisions, no mid-air islands, overhang report, compartment volume. `tools/skin_steep.py` reports steep visible surfaces. |
| `stl/preview_*.stl` | Body, closed jaw and open jaw as separate meshes, for viewing. |
| `tools/make_3mf.py` | Builds `horse_head.3mf` from the STL and the Bambu presets in `tools/bambu_profiles/`. |
| `tools/` | Renderers and quick-draft scripts used while sculpting. |

## Printing in Bambu Studio

1. **Open `horse_head.3mf`** (File > Open Project, or drag it onto Bambu
   Studio). If it asks, choose to open it as a project, not to import
   geometry only.
2. **Check the presets it selected:**
   - Printer: **Bambu Lab A1 0.4 nozzle**
   - Filament: **Bambu PLA Basic @BBL A1**
   - Process: **0.16mm High Quality @BBL A1**, shown as modified because of
     the changes below
3. If you're using a different PLA, pick it in the filament list. The
   process settings stay as they are.
4. **Slice and print.** Nothing needs painting or adjusting. Supports are
   already set up, and the model is already placed and turned on the plate.

The process changes this project makes to Bambu's High Quality preset:

| Setting | Value | Why |
|---|---|---|
| Wall loops | 3 | A stronger shell around the hollow jaw and the hinge. |
| Wall generator | Arachne | Smooth variable-width walls in the thin ears and jaw. |
| Seam position | Back | The model faces the front of the printer, so seams land on the back of the neck under the mane. |
| Brim type | No brim | The plinth is wide enough. |
| Supports | On: tree (auto), on build plate only | Holds up the lips and chin from the plate. "Build plate only" stops supports from growing inside the hinge, the compartment or the 0.45 mm gaps. |

The High Quality preset itself prints the outer wall slowly (60 mm/s) with
gyroid infill and 0.16 mm layers, for the smoothest surface on the face and mane.

### What's built into the model

The only supports are the slicer's, under the lips and chin. Everything else
is designed to print without help:

- The plinth stops short of the head, so the space under the muzzle is open
  plate where the supports can stand.
- Two tiny breakaway tabs tie the lower edge of each cheek to the jaw just
  below it. Without them, that edge would start in mid-air at the bottom of
  the hinge arc. They snap the first time you open the mouth.
- The jaw line is shaped so the underside of the jaw and cheeks stays within
  about 60° of vertical, which the A1 prints cleanly.
- The compartment's back walls are slanted.
- The cheeks are hollowed to a pitched roof over the hinge arc.
- The opening angle is limited so the clearance carved behind the jaw
  doesn't leave a flat ceiling under the throat.
- The only remaining steep spots are the tops of the nostril openings, which
  are short 2 mm bridges.

The 0.45 mm gaps between the jaw and the head are meant to print as air, so
leave "detect thin walls" off. It is already off in the project.

### Other slicers

Load `stl/horse_head.stl` standing on the plinth. Use 0.16 mm layers, 3
walls, 15 % gyroid infill and no brim. Turn supports on, but only from the
build plate, never on the model, so none grow inside the hinge or the
compartment. Use a slow outer wall if your slicer allows it.

### Estimated print time

**About 9 h 30 min and 200 g of PLA** at the project's settings, plus the A1's
start-up routine. That's an estimate from an A1-like PrusaSlicer profile;
Bambu Studio shows its own estimate after slicing. If you'd rather print
faster, switch the process to **0.20mm Standard @BBL A1** and choose to
transfer your changes when Bambu Studio asks. It finishes in about 7 hours,
with slightly more visible layer lines.

## After printing

1. **Remove the supports** under the muzzle. They're tree supports from the
   plate and pull away by hand or with pliers.
2. **Free the jaw.** Pull the chin down firmly. The first movement snaps the
   two small tabs inside the cheeks and breaks any faint bonds across the
   print-in-place gaps, and you'll feel the detent let go. Work it open and shut a dozen times until it moves smoothly.
3. The jaw should click shut and stay shut. If the click is too weak or too
   strong, change `NUB_PROUD` (default 0.75 mm) and reprint.

## Customising

```sh
pip install numpy scipy scikit-image trimesh manifold3d shapely vtk
python3 build_horse.py              # final, 0.3 mm grid (about 20 min)
python3 build_horse.py --res 0.6    # quick draft (about 3 min)
python3 verify_horse.py             # checks
python3 tools/make_images.py        # README pictures
```

- `horse_sculpt.py` holds the shape:
  - `L`, `TILT` and `POLL` set the head length, the nose-down angle and the
    position of the poll.
  - `ZT`, `ZB` and `W_ROWS` hold the head's measured profile and widths.
  - `NECK` and `CREST` define the neck. The features each have their own
    function: eyes, nostrils, ears, mane.
- `build_horse.py` holds the mechanism:
  - `OPEN_MAX` is the opening angle.
  - `GAP` and `PIN_GAP` are the print-in-place clearances.
  - `WALL` is the compartment wall.
  - `NUB_PROUD` sets the detent strength.
  - `TMJ` and `R_ARC` set the hinge position and the cheek arc.

To scale the whole thing, scale the STL in the slicer. The 0.45 mm gaps scale
too, so stay within about 85–125 %.

## How it's made

The bust is a signed distance field built from simple pieces:

- **Head:** a loft whose top line, bottom line and widths at seven heights
  were calibrated against a real horse head.
- **Face features:** sculpted shapes blended onto the loft for the brow,
  eyes, cheeks, nostrils, lips and ears.
- **Neck:** an ellipse swept along a spline.
- **Hair:** locks laid onto the surface by a little gravity simulation.

The field is meshed with marching cubes, evaluating it exactly only near the
surface.

The jaw is cut from the same field below the mouth line and in front of an
arc centred on the hinge, so it can turn without opening any visible gap. The
head is carved by the union of the jaw at every angle from shut to fully
open, plus 0.45 mm, so it cannot bind.

The checks in `verify_horse.py` show:

- both parts are watertight;
- the jaw only touches the head at the detent nubs and the breakaway tabs
  through the whole swing;
- the only layers that start in mid-air are the lips, and the slicer's
  build-plate supports reach them.

### Reference

The head's proportions were measured from the **Cyberware horse scan**, a
public 3D-scanning test model from the Georgia Tech Large Geometric Models
Archive, obtained via
[alecjacobson/common-3d-test-models](https://github.com/alecjacobson/common-3d-test-models).
It was used as a measuring reference only: profile heights, widths and
landmark positions. No geometry from it is in this model.
