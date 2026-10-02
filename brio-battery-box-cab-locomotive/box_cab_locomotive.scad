// =====================================================================
//  Battery Box-Cab Locomotive  -  Brio-compatible, self-propelled
// =====================================================================
//  A small electric "box-cab" engine that drives itself along any
//  Brio-style wooden track.  The motor's dual output shaft IS the drive
//  axle, so there are no printed gears.  Everything electrical simply
//  plugs together (no soldering):
//
//    2xAAA holder (Adafruit #4191, JST-PH)  -> its own switch left ON
//      -> click on/off cable (Adafruit #3064, JST-PH) under the big
//         roof button
//      -> 50 mm PH2.0-to-SH1.0 wire (Bambu XC004)
//      -> N20 dual-shaft worm gear motor 3 V 130 rpm (Bambu LA009)
//
//  Toddler safety: batteries sit under a roof hatch held by one M3
//  screw; the coupler magnets are sealed inside the print
//  (pause-at-height); the roof button is captive; no wires or moving
//  parts other than the wheels can be reached.
//
//  A box-cab looks right running either way, so it does not matter
//  which way the motor happens to turn.
//
//  Axles are held in "keyhole" bearings: a 3.4 mm slot from below lets
//  the 3 mm shaft in, then the 7 mm wheel hubs are pressed on from the
//  outside and can never come back out through the slot.  Nothing has
//  to snap or flex, and it does not depend on the exact motor size.
//
//  Parts (select with `part`):
//    "body"      main body / chassis   (exported upside down - print as is)
//    "hatch"     roof hatch            (exported upside down - print as is)
//    "button"    roof push button
//    "wheel"     wheel  - print 4
//    "axle"      front axle            (lies on its flat)
//    "shim"      2 mm spacer under the click switch, only if needed
//    "assembly"  everything in place, with dummy motor/battery/switch
//    "cutaway", "underside"  preview views
//
//  Coordinates: X along the loco (drive axle at X=0, front axle at
//  X=-34), Y across, Z=0 is the TOP of the track (wheels drop 3 mm into
//  the grooves).
// =====================================================================

part = "assembly";
$fn = 64;

// ---------------- Brio track ----------------
groove_c = 13;          // groove centre from track centreline
groove_d = 3;

// ---------------- wheels & axles ----------------
wheel_d    = 22;
wheel_w    = 4.0;
wheel_y0   = 10.9;      // inner face of the tread (|Y|)
axle_z     = wheel_d/2 - groove_d;   // 8
wheelbase  = 34;
front_x    = -wheelbase;
hub_d      = 7;         // hub that runs in the frame bearing
hub_y0     = 8.6;       // inner end of the hub
ring_d     = 9;         // spacer ring between hub and tread
frame_y0   = 8.8;       // frame bearing wall, inner face
frame_y1   = 10.5;      //                    outer face
bearing_d  = hub_d + 0.35;
slot_w     = 3.4;       // lets the 3 mm shaft in, never the 7 mm hub
brg_hx     = 6;         // half-length of a bearing wall

// D-shaft (N20 output shaft and printed front axle)
shaft_d    = 3.0;
shaft_flat = 2.5;       // across the flat
bore_d     = 3.05;      // press-fit bore for the D shaft
bore_flat  = 2.55;

// ---------------- battery holder (Adafruit #4191) ----------------
batt_l = 62.5; batt_w = 25.3; batt_h = 15.4;
batt_clear = 0.4;
batt_z0  = 22;          // underside of the holder (clears the motor gearbox)
batt_xc  = -11;         // holder centre: ~2/3 of its weight on the drive axle

// ---------------- body ----------------
wall      = 1.6;
fwall     = 6.4;        // thick front wall carries the hatch screw
in_w      = batt_w + 2*batt_clear;                 // 26.1 interior width
out_w     = in_w + 2*wall;                         // 29.3 body width
tray_x0   = batt_xc - (batt_l + 2*batt_clear)/2;   // interior front
tray_x1   = batt_xc + (batt_l + 2*batt_clear)/2;   // rear of battery bay
cab_x1    = 44.4;                                  // interior rear of the cab
body_x0   = tray_x0 - fwall;                       // outer front
body_x1   = cab_x1 + wall;                         // outer rear
floor_z0  = batt_z0 - 2;                           // battery floor underside (above the wheels)
top_z     = batt_z0 + batt_h + 2.0;                // top of the walls
hatch_t   = 2.0;
cab_floor_z0 = 6;                                  // motor can rests on this
cab_floor_t  = 1.5;
brg_z0    = 2.9;                                   // bottom of the bearing walls

// motor bay opening in the battery floor
bay_x0 = -7; bay_x1 = tray_x1 + 0.4; bay_hw = frame_y0 - 0.2;

// click switch (Adafruit #3064) shelf + roof button
shelf_z   = 27.5;       // top of the shelf the click switch lies on
shelf_x0  = 26.5;
btn_x     = 34;
btn_d     = 15;
btn_hole  = 16;
sw_h_nom  = 9;          // nominal height of the switch body
foot_x    = 12; foot_y = 18;

// hatch screw: M3 x 10 into a 2.5 mm pilot hole in the front wall
screw_x   = tray_x0 - fwall/2;

// couplers: 2 x Bambu D6x2 magnets stacked (6 x 4 mm), sealed in
mag_d = 6.3; mag_t = 4.2; mag_z = 10;              // magnet centre height above track top
cpl_len = 5.8;  cpl_hw = 6; cpl_z0 = 6; cpl_z1 = 20;
skin = 0.8;                                         // plastic over the magnet face

// ---------------- assumed motor geometry (Bambu LA009) ----------------
// Bambu does not publish a drawing; these are typical N20 worm-gear
// values, used only for the preview and clearance check.  The frame
// relies on: 3 mm D shaft, gearbox narrower than 17 mm, gearbox no more
// than 5 mm below / 13 mm above the shaft, shaft tips beyond |Y| = 10.
m_gb_x0 = -6; m_gb_x1 = 12;  m_gb_w = 12;  m_gb_z0 = -5; m_gb_z1 = 13;
m_can_d = 12; m_can_l = 15;  m_can_off = 7;     // can axis above the shaft
m_shaft_tip = 15.5;                              // |Y| of each shaft tip

// =====================================================================
//  helpers
// =====================================================================
module dshape(d, flat) {
    // 2D D-profile, flat at +Y
    intersection() { circle(d = d); translate([-d, -d]) square([2*d, d + flat - d/2]); }
}

module mirror_y() { children(); mirror([0, 1, 0]) children(); }

module rounded_box(p0, p1, r) {
    hull() for (x = [p0[0] + r, p1[0] - r], y = [p0[1] + r, p1[1] - r])
        translate([x, y, p0[2]]) cylinder(r = r, h = p1[2] - p0[2]);
}

// =====================================================================
//  wheel
// =====================================================================
module wheel_flat() {
    // printed lying down: outer face on the bed, hub pointing up
    difference() {
        union() {
            hull() {
                cylinder(d = wheel_d - 1.2, h = wheel_w);
                translate([0, 0, 0.6]) cylinder(d = wheel_d, h = wheel_w - 1.2);
            }
            cylinder(d = ring_d, h = wheel_w + (wheel_y0 - frame_y1));
            cylinder(d = hub_d,  h = wheel_w + (wheel_y0 - hub_y0));
        }
        translate([0, 0, -1]) linear_extrude(30) dshape(bore_d, bore_flat);
        // shallow dish on the outer face
        translate([0, 0, -0.01]) difference() {
            cylinder(d = wheel_d - 5, h = 0.8);
            cylinder(d = ring_d + 1, h = 1);
        }
    }
}

module wheel_at(x, side) {
    translate([x, side * (wheel_y0 + wheel_w), axle_z])
        rotate([side > 0 ? 90 : -90, 0, 0]) wheel_flat();
}

// =====================================================================
//  front axle (printed D-rod)
// =====================================================================
axle_len = 2 * (wheel_y0 + wheel_w) - 0.6;
module axle_flat() {
    translate([0, 0, shaft_flat - shaft_d/2]) rotate([0, 90, 0])
        linear_extrude(axle_len, center = true) rotate(-90) dshape(shaft_d, shaft_flat);
}
module axle_at() {
    translate([front_x, 0, axle_z]) rotate([90, 0, 0])
        linear_extrude(axle_len, center = true) dshape(shaft_d, shaft_flat);
}

// =====================================================================
//  body
// =====================================================================
module bearing_walls(xc) {
    // a pair of frame walls with keyhole bearings (slot opens downward)
    mirror_y() difference() {
        translate([xc - brg_hx, frame_y0, brg_z0]) cube([2*brg_hx, frame_y1 - frame_y0, floor_z0 - brg_z0 + 0.01]);
        translate([xc, 0, axle_z]) rotate([-90, 0, 0]) cylinder(d = bearing_d, h = 20);
        translate([xc - slot_w/2, frame_y0 - 1, brg_z0 - 1]) cube([slot_w, 5, axle_z - brg_z0 + 1]);
        // lead-in chamfer at the slot mouth
        translate([xc, frame_y0 - 1, brg_z0]) rotate([-90, 0, 0])
            linear_extrude(5) polygon([[-slot_w/2 - 1, 0.01], [slot_w/2 + 1, 0.01], [slot_w/2, -1], [-slot_w/2, -1]]);
    }
}

module coupler_block(front) {
    // buffer-beam block; the top is bevelled 45 deg so it prints
    // without supports when the body is upside down
    xa = front ? body_x0 : body_x1;
    dir = front ? -1 : 1;
    hull() {
        translate([front ? xa - cpl_len : xa - 0.01, -cpl_hw, cpl_z0]) cube([cpl_len + 0.01, 2*cpl_hw, cpl_z1 - cpl_len - cpl_z0]);
        translate([front ? xa - 0.01 : xa - 0.01, -cpl_hw, cpl_z0]) cube([0.02, 2*cpl_hw, cpl_z1 - cpl_z0]);
    }
}

module magnet_pocket(front) {
    // closed cavity: the print is paused, the magnets dropped in, and
    // printing continues over them
    xo = front ? body_x0 - cpl_len + skin : body_x1 + cpl_len - skin - mag_t;
    translate([xo, -mag_d/2, mag_z - mag_d/2]) cube([mag_t, mag_d, mag_d + 0.3]);
}

module body_solid() {
    // battery bay + cab shell
    difference() {
        rounded_box([body_x0, -out_w/2, floor_z0], [body_x1, out_w/2, top_z], 2);
        translate([tray_x0, -in_w/2, batt_z0]) cube([cab_x1 - tray_x0, in_w, 50]);
    }
    // cab (rear) section: walls down to the cab floor, behind the drive wheels
    cab_x0 = bay_x1;
    difference() {
        rounded_box([cab_x0, -out_w/2, cab_floor_z0], [body_x1, out_w/2, floor_z0 + 0.01], 2);
        translate([cab_x0 - 1, -in_w/2, cab_floor_z0 + cab_floor_t]) cube([cab_x1 - cab_x0 + 1, in_w, 40]);
    }
    // front pilot plate between the front wheels, carries the coupler
    translate([body_x0, -frame_y1, cpl_z0]) cube([wall, 2*frame_y1, floor_z0 - cpl_z0 + 0.01]);
    // axle bearings
    bearing_walls(0);
    bearing_walls(front_x);
    // stiffeners from the front bearings to the pilot plate
    mirror_y() translate([body_x0, frame_y0, 12]) cube([front_x - brg_hx - body_x0 + 0.01, frame_y1 - frame_y0, floor_z0 - 12 + 0.01]);
    // couplers
    coupler_block(true);
    coupler_block(false);
    // click-switch shelf with a low front fence
    translate([shelf_x0, -in_w/2, shelf_z - 1.5]) cube([cab_x1 - shelf_x0 + 0.01, in_w, 1.5]);
    translate([shelf_x0, -in_w/2 + 4, shelf_z - 0.01]) cube([1.2, in_w - 8, 2]);
    // stops that keep the battery holder out of the cab
    mirror_y() translate([tray_x1, in_w/2 - 3, batt_z0 - 0.01]) cube([1.2, 3.01, 6]);
}

module body_cuts() {
    // motor bay opening in the battery floor
    translate([bay_x0, -bay_hw, floor_z0 - 1]) cube([bay_x1 - bay_x0, 2*bay_hw, 5]);
    // cab interior (no battery floor behind the battery bay)
    translate([bay_x1 - 0.01, -in_w/2, cab_floor_z0 + cab_floor_t]) cube([cab_x1 - bay_x1 + 0.01, in_w, shelf_z - 1.5 - cab_floor_z0 - cab_floor_t]);
    // hatch screw pilot hole in the front wall
    translate([screw_x, 0, top_z - 12]) cylinder(d = 2.5, h = 13);
    // hatch tongue slot in the rear wall
    translate([cab_x1 - 0.5, -8, top_z - 2.2]) cube([wall, 16, 1.4]);
    // cable notch at the front of the battery bay (holder may face either way)
    translate([tray_x0 - 0.01, -5, top_z - 4]) cube([1.2, 10, 5]);
    // magnet pockets
    magnet_pocket(true);
    magnet_pocket(false);
    // decoration: recessed windows at both ends of each side
    for (x = [body_x0 + 4, body_x1 - 4 - 9]) mirror_y()
        translate([x, out_w/2 - 0.6, top_z - 12]) cube([9, 1, 8]);
    // engraved door outlines on each side
    mirror_y() translate([0, out_w/2 - 0.5, 0]) difference() {
        translate([-6, 0, floor_z0 + 2]) cube([12, 1, top_z - floor_z0 - 6]);
        translate([-5.4, -0.1, floor_z0 + 2.6]) cube([10.8, 1.2, top_z - floor_z0 - 7.2]);
    }
    // headlight discs (shallow) at both ends
    for (x = [body_x0 - 0.01, body_x1 - 0.6]) for (y = [-8, 8])
        translate([x, y, top_z - 7]) rotate([0, 90, 0]) cylinder(d = 5, h = 0.61);
}

module body() { difference() { body_solid(); body_cuts(); } }

// =====================================================================
//  hatch (roof) - modelled in place
// =====================================================================
module hatch() {
    lip_gap = 0.3;
    difference() {
        union() {
            rounded_box([body_x0, -out_w/2, top_z], [body_x1, out_w/2, top_z + hatch_t], 2);
            // locating lip just inside the walls
            difference() {
                translate([tray_x0 + lip_gap, -in_w/2 + lip_gap, top_z - 2]) cube([cab_x1 - tray_x0 - 2*lip_gap, in_w - 2*lip_gap, 2.01]);
                translate([tray_x0 + lip_gap + 1.2, -in_w/2 + lip_gap + 1.2, top_z - 3]) cube([cab_x1 - tray_x0 - 2*lip_gap - 2.4, in_w - 2*lip_gap - 2.4, 4]);
            }
            // tongue that hooks under the rear wall
            translate([cab_x1 - 1.0, -7.5, top_z - 2.0]) cube([1.4, 15, 1.0]);
        }
        // keep the lip clear of the button flange
        translate([btn_x, 0, top_z - 3]) cylinder(d = btn_hole + 4, h = 3);
        // button hole with a soft chamfer
        translate([btn_x, 0, top_z - 5]) cylinder(d = btn_hole, h = 20);
        translate([btn_x, 0, top_z + hatch_t - 0.6]) cylinder(d1 = btn_hole, d2 = btn_hole + 1.2, h = 0.61);
        // countersunk M3 screw hole over the front wall
        translate([screw_x, 0, top_z - 5]) cylinder(d = 3.4, h = 20);
        translate([screw_x, 0, top_z + hatch_t - 1.6]) cylinder(d1 = 3.4, d2 = 6.6, h = 1.61);
        // engraved roof panel lines
        for (x = [tray_x0 + 6, btn_x - 13]) translate([x, -out_w/2 + 3, top_z + hatch_t - 0.5]) cube([0.8, out_w - 6, 1]);
    }
}

// =====================================================================
//  roof button (captive plunger)
// =====================================================================
btn_rest_z = shelf_z + sw_h_nom + 0.3;     // underside of the foot at rest
btn_top_z  = top_z + hatch_t + 4.0;        // top of the button at rest (4 mm proud)
module button() {
    translate([btn_x, 0, 0]) {
        // foot that presses anywhere on the switch body
        translate([-foot_x/2, -foot_y/2, btn_rest_z]) cube([foot_x, foot_y, 2]);
        // stem
        translate([0, 0, btn_rest_z]) cylinder(d = btn_d, h = btn_top_z - btn_rest_z - 2);
        // flange under the hatch keeps it captive
        translate([0, 0, top_z - 2.4]) cylinder(d1 = btn_d, d2 = btn_hole + 2.4, h = 2.4);
        // domed top
        translate([0, 0, btn_top_z - 2]) scale([1, 1, 0.27]) sphere(d = btn_d);
    }
}

module shim() { cube([12, 20, 2]); }

// =====================================================================
//  dummy purchased parts (preview and clearance checks only)
// =====================================================================
module dummy_motor() {
    translate([0, 0, axle_z]) {
        color("Goldenrod") translate([m_gb_x0, -m_gb_w/2, m_gb_z0]) cube([m_gb_x1 - m_gb_x0, m_gb_w, m_gb_z1 - m_gb_z0]);
        color("Silver") translate([m_gb_x1, 0, m_can_off]) rotate([0, 90, 0]) cylinder(d = m_can_d, h = m_can_l);
        color("White") translate([m_gb_x1 + m_can_l, -4, m_can_off - 3]) cube([3, 8, 6]);
        color("Silver") rotate([90, 0, 0]) cylinder(d = shaft_d, h = 2*m_shaft_tip, center = true);
    }
}
module dummy_battery() {
    color("DimGray") translate([batt_xc - batt_l/2, -batt_w/2, batt_z0]) cube([batt_l, batt_w, batt_h]);
}
module dummy_switch() {
    color("Black") translate([btn_x - 6, -12, shelf_z]) cube([12, 24, sw_h_nom]);
}
module dummy_track() {
    color("BurlyWood") translate([-80, -20, -12]) difference() {
        cube([160, 40, 12]);
        for (s = [-1, 1]) translate([-1, 20 + s*groove_c - 3, 9]) cube([162, 6, 5]);
    }
}

// =====================================================================
//  output
// =====================================================================
// body is printed upside down: print Z = top_z - model Z
mag_pause = top_z - (mag_z - mag_d/2);
echo(str("BODY: add a pause at layer height ", mag_pause, " mm to drop in the magnets"));
echo(str("Overall: length ", body_x1 + cpl_len - (body_x0 - cpl_len), " mm, width ",
         max(out_w, 2*(wheel_y0 + wheel_w)), " mm, height above table ", btn_top_z + 12, " mm"));

module assembly() {
    color("SteelBlue") body();
    color("SteelBlue") hatch();
    color("Red") button();
    color("Gold") { for (s = [-1, 1]) { wheel_at(0, s); wheel_at(front_x, s); } axle_at(); }
    dummy_motor();
    dummy_battery();
    dummy_switch();
    %dummy_track();
}

if (part == "body") translate([0, 0, top_z]) rotate([180, 0, 0]) body();
else if (part == "hatch") translate([0, 0, top_z + hatch_t]) rotate([180, 0, 0]) hatch();
else if (part == "button") translate([-btn_x, 0, -btn_rest_z]) button();
else if (part == "wheel") wheel_flat();
else if (part == "axle") axle_flat();
else if (part == "shim") shim();
else if (part == "assembly") assembly();

// cut-away preview (front half of the body removed along Y)
module cutaway() {
    difference() {
        union() { color("SteelBlue") body(); color("SteelBlue") hatch(); color("Red") button(); }
        translate([-100, -50, -10]) cube([200, 50, 100]);
    }
    color("Gold") { wheel_at(0, 1); wheel_at(front_x, 1); }
    dummy_motor(); dummy_battery(); dummy_switch();
}
if (part == "cutaway") cutaway();
if (part == "underside") {
    color("SteelBlue") body(); color("SteelBlue") hatch();
    color("Gold") { for (s = [-1, 1]) { wheel_at(0, s); wheel_at(front_x, s); } axle_at(); }
    dummy_motor();
}
