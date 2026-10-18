# Emily's Cup

A little stand to park a 70 mm cup on, with "Emily's Cup" on it in raised
letters. There are three designs to pick from. Each has a shallow pocket the
cup drops into, so it sits in the same spot every time, and the letters
print in a second colour.

![the three designs](images/options.png)

| | Design | Size | Lettering |
|---|---|---|---|
| ![tab](images/tab_cup.png) | **1. Name tab:** a round coaster with a rounded tab out the front | 102 × 111 × 6.6 mm | Pacifico (script), pink on white |
| ![arch](images/arch_cup.png) | **2. Arch:** a wide round coaster with the name curving round the front of the rim and a heart at each end | 122 mm across, 6.6 mm tall | Fredoka (rounded), white on lilac |
| ![nameplate](images/nameplate_cup.png) | **3. Nameplate:** a coaster with a 45° ramp across the front, like a desk name sign, so the name faces you | 98 × 118 × 26 mm | Pacifico (script), white on mint |

The colours are only suggestions: change them in Bambu Studio.

## Fit

- **Pocket:** 73 mm across and 3 mm deep, with a 1 mm chamfer round the top
  edge to guide the cup in. That's 1.5 mm of room each side of a 70 mm cup
  bottom.
- **Measure the bottom of the cup**, not the rim. If it's not 70 mm, change
  `CUP_D` in `build.py` and rebuild; every design resizes round it.
- The floor under the cup is 2.4 mm thick.

## Printing

Open the design's project in Bambu Studio: `emilys_cup_tab.3mf`,
`emilys_cup_arch.3mf` or `emilys_cup_nameplate.3mf`. Each has one plate on
**0.20mm Standard @BBL A1**, with the base on filament 1 and the letters on
filament 2 (AMS).

| Setting | Value | Why |
|---|---|---|
| Supports | off | the steepest overhang is the underside of the nameplate's letters, at 45° |
| Brim | off | it lies on a wide flat bottom |
| Walls | 3 | |
| Infill | 15% | |
| Flush into infill | on | the purge between colours goes into the base's infill |

- **Filament:** about 35 g for the tab, 45 g for the arch and 65 g for the
  nameplate (my estimates from the volume; Bambu Studio will show the exact
  amount when you slice).
- **No AMS?** On the tab and the arch the letters sit on the flat top, so
  they start at one height: print from the STL and add a filament change
  (right-click the layer slider, "Add pause") at the first layer above
  5.4 mm. The nameplate's letters are on a slope, so they need the AMS, or
  print it in one colour and paint the letters.
- The letters stand 1.2 mm proud. Every stroke is at least 0.8 mm wide (the
  build script checks it).

## Changing it

The parameters at the top of `build.py` set:

- `NAME`, the text (it fits itself to each design, so a different name works)
- `CUP_D`, `CLEARANCE`, `POCKET_DEPTH` and `FLOOR`, the pocket
- `LETTER_H`, how far the letters stand up
- `TAB_W` and `TAB_TEXT_W` for the tab, `ARCH_D`, `ARCH_TEXT_CAP` and
  `ARCH_TEXT_R` for the arch, and `RAMP_RISE`, `RAMP_ANGLE` and
  `PLATE_TEXT_W` for the nameplate

The script stops with an error if the name would run into the pocket or off
the edge, if a stroke is too thin to print, or if a mesh is broken.

```
pip install trimesh numpy manifold3d matplotlib vtk pillow
python3 build.py               # -> stl/
xvfb-run -a python3 render.py  # -> images/ (drop xvfb-run on a desktop)
python3 make_3mf.py            # -> emilys_cup_*.3mf
```

## Files

| File | What |
|---|---|
| `build.py` | Builds all three designs. Its key dimensions are parameters at the top. |
| `render.py` | Preview renders (VTK), with a 70 mm cup for scale. |
| `make_3mf.py` | Builds the Bambu Studio projects with `../tools/bambu3mf.py`. |
| `emilys_cup_*.3mf` | The three Bambu Studio projects, ready to slice. |
| `stl/` | `<design>.stl` (the base) and `<design>_text.stl` (the letters) for each design. |
| `fonts/` | Pacifico and Fredoka SemiBold, from Google Fonts, under the SIL Open Font License (`OFL-*.txt`). |
