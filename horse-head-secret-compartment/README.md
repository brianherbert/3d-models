# Horse Head with a Secret Compartment

A desk-size horse bust whose lower jaw hinges open to reveal a hidden
compartment. **One print, one part, no assembly:** the jaw and its hinge pin
are printed in place inside the head. After printing you snap off one thin
support strut under the chin, work the jaw a few times, and it's done.

| Closed | Open |
|---|---|
| ![closed](images/horse_closed.png) | ![open](images/horse_open.png) |

![cutaway](images/horse_cutaway.png)
*Section through the centre: the hollow jaw is the compartment; the diamond
hinge pin runs through the jowls; the mouth is a vaulted chamber so every
surface is self-supporting.*

## What it is

- **Size:** about 150 mm tall (ears to base), 55 mm wide, 125 mm long, on an
  oval plinth. Head lowered in a calm, grazing pose.
- **Compartment:** the lower jaw is a hollow scoop with 2.4 mm walls, open at
  the tongue. It holds a few coins, a ring, a USB stick, a folded note or a
  small key. The jaw opens to about 35°.
- **Mechanism:** a diamond-section pin, printed as part of the jaw, sits in a
  matching socket in the jowls. The jaw's heel is a cylinder around the pin
  so it turns without binding; the body is carved to the jaw's full swept path.
  The hinge is slightly tight by design (0.4 mm clearance) so the jaw stays
  where you put it instead of flopping open.

## Files

| File | What |
|---|---|
| `stl/horse_head.stl` | **The part to print.** Body and jaw in one file, already positioned. |
| `sculpt_horse_head.py` | The parametric sculpt (Python: numpy, scikit-image, trimesh, manifold3d). |
| `stl/preview_*.stl` | Body, jaw and solid-head meshes separately, for viewing or remixing. |

## Printing (Bambu Lab A1, PLA, 0.4 mm nozzle)

- **Orientation:** as exported, standing on the plinth.
- **Layer height:** 0.2 mm. **Walls:** 3. **Infill:** 15 %.
- **Supports: none.** The head is posed so the chin and muzzle undersides are
  at or under 45°, the mouth roof is a vault, the ear fronts are scooped at a
  printable angle, and the one spot that can't self-support (the tip of the
  chin, which hangs in front of the neck) has a built-in strut.
- **Do not enable "detect thin walls" or bridging tricks;** the 0.45 mm gaps
  between jaw and body are meant to print as air. Keep the default
  "detect overhang wall" on.
- Brim optional; the plinth is wide enough without.

### Estimated print time

See the table at the bottom; filled in from a slice with A1 speeds.

## After printing

1. **Snap the strut.** Under the chin there's a thin cross-shaped blade
   standing on the plinth. Grip it with pliers at its base and twist; it is
   notched there and comes away clean. Trim any stub flush.
2. **Free the jaw.** Push the chin down firmly. The first movement breaks the
   faint bond across the printed gaps; it may need a few firm pushes. Work it
   through its range a dozen times and it loosens to a smooth, slightly stiff
   hinge.
3. If it's too stiff after that, a drop of water-based lubricant (or just time)
   fixes it. If it's loose and flops open, print again with `PIN_GAP = 0.35`.

## Customising

Everything is parametric in `sculpt_horse_head.py`:

```sh
pip install numpy scikit-image trimesh manifold3d
python3 sculpt_horse_head.py            # final at 0.5 mm resolution (~15 min)
python3 sculpt_horse_head.py --res 0.8  # quick draft
```

- `L`, `TILT`, `POLL` – head length, nose-down angle, position on the neck.
- `GAP`, `PIN_GAP` – print-in-place clearances.
- `WALL` – compartment wall thickness. `OPEN_MAX` – designed opening angle.
- The sculpt itself is a list of blended ellipsoids, cones and capsules in
  `horse_sdf()`; move or resize them to change the horse.

To scale the whole thing, scale the STL in the slicer; the 0.45 mm gaps scale
too, so stay within about 80–130 %.

## How it's made

The bust is a signed distance field: smooth unions of a few dozen primitives,
meshed with marching cubes. The jaw is cut from the same field (so its
surface matches the head exactly), given a 0.45 mm offset, hinged on a diamond
pin whose socket lives in the jowls, and hollowed by eroding the field 2.4 mm.
The body is carved by the union of the jaw rotated from 0° to 35°, which
guarantees it can't bind. Every exported part was checked for watertightness,
for mid-air islands layer by layer in print orientation, and for collisions
through the full swing.
