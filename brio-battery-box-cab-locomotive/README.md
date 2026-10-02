# Battery Box-Cab Locomotive (Brio-compatible)

This is a small electric engine that drives itself on any Brio-style wooden
track. A toddler presses the big red button on the roof and it goes; pressing it
again stops it.

- **No soldering, no gears to print, one screw.** The motor's double-ended
  output shaft *is* the drive axle. All the electrical parts plug into each other.
- **Toddler-minded:**
  - The batteries sit under a roof hatch held by one screw.
  - The coupler magnets are sealed inside the plastic during printing.
  - The roof button can't come out.
  - No wires or gears can be reached from outside.
- **Sized like a Brio engine:** 107 × 30 × 57 mm (L × W × H, on the track).
  Brio's own battery engine is about 90 × 37 × 50 mm. The loco is narrower than
  the 40 mm track, so it clears platforms, signals and tunnels.

| | |
|---|---|
| ![iso](images/loco_iso.png) | ![underside](images/loco_underside.png) |

![cutaway](images/loco_side_cutaway.png)
*Cut-away: 2×AAA holder on top, worm-gear motor below it driving the rear
axle, click switch under the roof button.*

## Bill of materials

| Qty | Part | Where | Notes |
|---|---|---|---|
| 1 | **N20 Dual Shaft Worm Gear Motor, 3 V 130 rpm (LA009)** | [Bambu Lab store](https://us.store.bambulab.com/products/n20-dual-shaft-worm-gear-motor) | The shaft is the drive axle. Rated 2–4 V, so it suits 2×AAA. |
| 1 | **50 mm PH2.0 to SH1.0 Conversion Wire (XC004)** | [Bambu Lab store](https://us.store.bambulab.com/products/50mm-ph2-0-to-sh1-0-conversion-wire) | Plugs the JST-PH battery lead into the motor's SH1.0 socket. |
| 1 | **2 × AAA Battery Holder with On/Off Switch & JST PH (#4191)** | [Adafruit](https://www.adafruit.com/product/4191) | 62.5 × 25.3 × 15.4 mm. The smallest pack that runs the motor well. Its own switch stays ON inside. |
| 1 | **JST 2-pin Extension Cable with On/Off Switch (#3064)** | [Adafruit](https://www.adafruit.com/products/3064) | Push-on/push-off click switch, worked by the roof button. |
| 4 | **D6 × 2 mm round magnets** (2 per coupler) | [Bambu Lab store – magnets](https://us.store.bambulab.com/collections/magnets) | Sealed inside the couplers during printing. |
| 1 | M3 × 10 mm screw (countersunk or button head) | Any hardware store / Bambu Maker's Supply | Holds the roof hatch closed. It self-taps into the plastic. |
| 2 | AAA batteries | — | Alkaline (fastest) or NiMH rechargeable (a bit slower). |
| — | PLA filament | Bambu Lab | About 30 g. Any colours: body, wheels and button look nice in three colours. |

### Why these parts

- **Battery:** 2×AAA is the smallest common battery pack that gives the motor
  its rated 3 V with real run time (roughly 2–3 hours of running on alkalines).
  Coin cells are too weak, and button batteries are dangerous around toddlers.
  A LiPo would need a charger board and is a puncture risk in a toy.
- **One-direction motor:** the motor runs in one direction only. Which way the
  loco travels depends on how the plugs happen to line up, and there's no reverse
  switch. A box-cab looks right running either way, so that's fine. Kids turn it
  around by hand, just like a Brio battery engine.
- **Pushing it by hand:** the worm gear self-locks, so if a child pushes the
  engine with the power off, the driving wheels just slide. Nothing can break.

## Printed parts (`stl/`)

| File | Qty | Orientation | Notes |
|---|---|---|---|
| `body.stl` | 1 | As exported (upside down) | **Pause for magnets** (below) |
| `hatch.stl` | 1 | As exported (upside down) | |
| `button.stl` | 1 | As exported | Red looks great |
| `wheel.stl` | **4** | As exported | |
| `axle.stl` | 1 | As exported (on its flat) | Front axle |
| `shim.stl` | 0–2 | As exported | Only if the button doesn't click (see below) |

Print settings for the Bambu Lab A1, PLA, 0.4 mm nozzle:

- **Layer height:** 0.16–0.2 mm. **Walls:** 3. **Infill:** 20 %.
- **Supports:** none. The body prints upside down so the battery floor and cab
  floor are just bridges.
- **Wheels, axle and button:** 100 % infill. They're tiny, and stiff wheels
  press on more securely.
- A brim on the body helps, because it stands on the thin rim of its walls.

### Sealing the coupler magnets (body print)

1. In Bambu Studio, slice `body.stl`. In the layer slider, find the first layer
   **above 32.55 mm** (32.6 mm at 0.2 mm layers). Right-click it and choose
   **Add Pause**.
2. Before printing, work out the magnet polarity so the loco couples to your
   existing Brio wagons. Make two stacks of two D6×2 magnets.
   - Let one stack jump onto the **front** coupler of a Brio wagon. Mark the face
     that is *touching the wagon*. That stack goes in the loco's **rear** pocket
     (the cab end, the end with the red button), marked face **outward**.
   - Let the other stack jump onto the **rear** coupler of a wagon. Mark the
     touching face. That stack goes in the loco's **front** pocket (the end with
     the screw), marked face **outward**.
3. When the printer pauses, drop each stack into its slot, standing on edge. Make
   sure the marked face points toward the end of the loco, then resume. The
   printer seals the magnets in with plastic.

## Assembly (about 10 minutes, a screwdriver is the only tool)

1. **Motor:** with the battery bay still empty, feed the motor up into the body
   from underneath, can first, through the opening in the battery floor above
   the rear axle. Swing the can back so it lies on
   the cab floor at the rear. At the same time, guide the bare shaft up the two
   narrow slots until it sits in the round bearing holes.
2. **Drive wheels:** press a wheel onto each end of the motor shaft, matching the
   flat in the bore to the flat on the shaft. Push until the wheel's small
   spacer ring touches the frame. The 7 mm hub now fills the bearing and can
   never drop back out through the 3.4 mm slot. That is what holds the motor in.
   Support the opposite shaft end while you press (squeeze both wheels
   together between your thumbs).
3. **Front wheels:** push the printed axle up into the front slots, then press a
   wheel onto each end the same way.
4. **Wiring:** connect battery holder → click-switch cable → Bambu conversion
   wire → motor. Every plug only fits one way. Lay the click switch on the shelf
   at the rear of the cab, button facing up, and coil the spare cable underneath
   it in the cab.
5. **Batteries:** put 2×AAA in the holder and slide its own switch to **ON**. Lay
   it in the battery bay, cable toward the cab. A notch at the front lets the
   cable run over the top if the holder's lead comes out of the other end.
6. **Roof:** drop the red button into the hatch from underneath (its flange keeps
   it captive). Hook the hatch's rear tongue under the rear wall, lower the front,
   and fit the M3 screw at the front.
7. **Test:** press the button. The motor should start, and press again to stop.
   If the button bottoms out without a click, the switch sits lower than
   expected. Put one or two `shim.stl` pads under it.

## Brio compatibility

- **Wheels:** 22 mm wheels at 26 mm gauge, 4 mm wide, running in the standard
  6 mm × 3 mm grooves.
- **Curves:** the 34 mm wheelbase is similar to Brio wagons, so it takes the
  tight short curves.
- **Couplers:** magnetic, centre 10 mm above the track surface, so it couples to
  Brio and other wooden-railway wagons.
- **Clearance:** lowest point 2.9 mm above the track surface. It clears
  switches, crossings and ramp transitions.

## Safety notes

This is a home-made toy, not a certified one. Before handing it to a toddler:

- **Wheels:** check that all four wheels are pressed on hard and can't be pulled
  off. A loose 22 mm wheel is a small part, so add a drop of superglue to each
  wheel bore if in doubt.
- **Hatch:** keep the hatch screw tight. Batteries must not be reachable without
  a screwdriver.
- **Magnets:** make sure no magnet is visible after printing. Swallowed magnets
  are dangerous.
- **Supervision:** supervise play, and remove the batteries if the toy is stored
  for a long time.

## Customising / checking the motor fit

Bambu doesn't publish a dimensioned drawing of the LA009, so before printing the
body, measure your motor. The frame only needs these to hold:

- 3 mm D-shaft.
- Gearbox narrower than 17 mm (it sits between the bearing walls).
- Gearbox top no more than 13 mm above the shaft centre (it must clear the
  battery holder).
- Gearbox bottom no more than 5 mm below the shaft centre (it must clear the
  track).
- Each shaft end reaches past 10 mm from the motor's centre (so it reaches into
  the wheel hub).

The `m_*` values in `box_cab_locomotive.scad` describe the assumed motor and
drive the preview. `batt_z0` raises the battery floor if your gearbox is taller.
`mag_z` moves the coupler height. `bore_d` / `bore_flat` tune the wheel press fit.

Export a part with:

```sh
openscad -o stl/body.stl -D 'part="body"' box_cab_locomotive.scad
```
