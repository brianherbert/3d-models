// =====================================================================
//  Battery Box-Cab Locomotive  -  Brio-compatible, self-propelled  (v2)
// =====================================================================
//  A small electric "box-cab" engine that drives itself along any
//  Brio-style wooden track.  The motor's dual output shaft IS the drive
//  axle, so there are no printed gears.  Everything electrical simply
//  plugs together (no soldering):
//
//    2xAAA holder (Adafruit #4191, JST-PH)  -> its own switch left ON
//      -> click on/off cable (Adafruit #3064, JST-PH) under the big
//         roof button at the front
//      -> 50 mm PH2.0-to-SH1.0 wire (Bambu XC004)
//      -> N20 dual-shaft worm gear motor 3 V 130 rpm (Bambu LA009)
//
//  Layout (front = button end, X increases toward the rear):
//
//      front coupler | switch cab | battery bay ............ | rear coupler
//                        ^ front axle (printed)     ^ drive axle = motor shaft
//                               motor can points forward under the battery
//
//  The axles sit close to the ends, like a real Brio engine, so the
//  couplers stay near the track centreline on curves.  About two thirds
//  of the weight rests on the driven axle.
//
//  Toddler safety: batteries sit under a roof hatch held by one M3
//  screw; the coupler magnets are sealed inside the print
//  (pause-at-height); the roof button is captive; no wires or moving
//  parts other than the wheels can be reached.
//
//  Axles are held in "keyhole" bearings: a 3.4 mm slot from above lets
//  the 3 mm shaft drop in through the battery floor, then the 7 mm wheel
//  hubs are pressed on from the outside and can never lift out through
//  the slot.  A bar behind the gearbox and a saddle under the nose of the
//  can stop the motor body turning under load.
//
//  Parts (select with `part`):
//    "body"         main body / chassis (exported upside down - print as is)
//    "hatch"        roof hatch          (exported upside down - print as is)
//    "button"       roof push button (inline switch variant only)
//    "wheel"        plain front wheel - print 2
//    "wheel_drive"  drive wheel with a groove for a TPU tyre - print 2 (optional)
//    "wheel_drive_oring"  drive wheel grooved for a 22 x 2.5 mm O-ring - print 2 (default)
//    "tyre"         TPU tyre ring for the drive wheel - print 2 (optional)
//    "axle"         front axle (lies on its flat)
//    "shim"         2 mm spacer under the click switch, only if needed
//    "assembly"     everything in place, with dummy motor/battery/switch
//    "cutaway", "underside"   preview views
//
//  Coordinates: X along the loco (drive axle at X=0, front axle at
//  X=-wheelbase), Y across, Z=0 is the TOP of the track (wheels drop
//  3 mm into the grooves).
// =====================================================================

part = "assembly";
$fn = 64;

// ---------------- Brio track ----------------
groove_c = 13;          // groove centre from track centreline
groove_d = 3;

// ---------------- wheels & axles ----------------
wheel_d    = 26;        // 26 mm: keeps the motor body 2.6 mm above the track
wheel_w    = 4.0;
wheel_y0   = 10.9;      // inner face of the tread (|Y|)
axle_z     = wheel_d/2 - groove_d;   // 8
wheelbase  = 45;
front_x    = -wheelbase;
hub_d      = 7;         // hub that runs in the frame bearing
hub_y0     = 6.6;       // inner end of the hub
ring_d     = 9;         // spacer ring between hub and tread
frame_y0   = 6.8;       // frame bearing wall, inner face
frame_y1   = 8.5;       //                    outer face
bearing_d  = hub_d + 0.35;
slot_w     = 3.4;       // lets the 3 mm shaft in, never the 7 mm hub
brg_hx     = 6;         // half-length of a plain bearing wall
dish_depth = 2.0;       // recess in the wheel face (the shaft end sits 0.4 mm below it)

// optional traction tyres on the drive wheels
//   "tpu"   : printed TPU ring (tyre.stl)
//   "oring" : hardware-store nitrile O-ring, 22 mm ID x 2.5 mm section
groove_w   = 2.6;  groove_dp = 1.2;               // TPU ring groove
tyre_t     = 1.7;  tyre_w    = groove_w - 0.2;
tyre_id    = wheel_d - 2*groove_dp - 0.4;        // slight stretch
oring_cs   = 2.5;  oring_id = 22;
og_w       = oring_cs + 0.3;                     // O-ring groove
og_dp      = (wheel_d - (oring_id + 0.4))/2;     // groove bottom = ID + 0.4 (stretch)

// D-shaft (N20 output shaft and printed front axle)
shaft_d    = 3.0;
shaft_flat = 2.5;       // across the flat
bore_d     = 3.05;      // press-fit bore for the D shaft
bore_flat  = 2.55;

// ---------------- battery holder (Adafruit #4191) ----------------
batt_l = 62.5; batt_w = 25.3; batt_h = 15.4;
batt_clear = 0.4;
batt_z0  = 23.5;        // underside of the holder (0.5 mm above the wheel tops)
batt_xc  = -14;         // holder centre: ~2/3 of its weight on the drive axle

// ---------------- motor geometry (Bambu LA009, from Bambu's own 3D model) ----------------
// The motor is a 12 x 10 mm bar with the 3 mm D-shaft through its centre
// line.  Positions along X are relative to the shaft; the can points
// FORWARD (-X).  Heights are relative to the shaft axis.
m_rear    = 3.96;                // gearbox face behind the shaft
m_body    = -28.6;               // front end of the 12 x 10 body (can)
m_cap0    = -30.1;  m_cap1 = -31.4;   // plastic end cap (12 x 10), 1.5 mm gap before it
m_end     = -34.32;              // tips of the solder tabs / lead exit
m_h       = 12;                  // body height (Z), centred on the shaft
m_w       = 10;                  // body width (Y), centred on the shaft
m_boss_d  = 4;  m_boss_y = 5.5;  // bearing boss on each side face
m_shaft_tip = 12.5;              // |Y| of each shaft tip
m_gap     = 0.4;                 // clearance of the cage bar and saddle
gb_x1 = m_rear;  can_x0 = m_end;

// ---------------- on/off switch ----------------
//  "p16"    : 16 mm panel-mount latching pushbutton (Adafruit #1442 family,
//             any "16 mm 1NO1NC latching") through the roof hatch, soldered
//             into the battery holder's red lead.  Documented dimensions,
//             no printed button, ~25 cm of wire in total.      <- default
//  "pbs11"  : same idea with a 12 mm PBS-11A type button.
//  "inline" : Adafruit #3064 click-switch cable on a shelf under a printed
//             captive roof button.  No soldering, ~80 cm of wire to stow.
switch_type = "p16";
p16 = (switch_type == "p16");
// panel-mount button dimensions (16 mm family / PBS-11A)
pbs_hole   = p16 ? 16.4 : 12.4;          // panel hole for the thread
pbs_cap_d  = p16 ? 16 : 12;  pbs_cap_h = p16 ? 5 : 6;    // button above the bezel
pbs_flange = p16 ? 18 : 14.5;            // bezel on top of the panel
pbs_body_d = p16 ? 15.6 : 10;            // threaded body
pbs_nut    = p16 ? 20 : 15;              // nut, across corners
pbs_below  = p16 ? 24 : 17;              // body + terminals below the panel
well_clear = 0.6;                        // radial clearance in the well
// inline switch (Adafruit #3064), assumed housing size
sw_len_x = 12;  sw_len_y = 24;  sw_h_nom = 9;
cab_len  = switch_type == "inline" ? sw_len_x + 4 : pbs_nut + 1.6;   // switch cab interior length

// ---------------- body ----------------
wall      = 1.6;
rwall     = 6.4;        // thick rear wall carries the hatch screw
in_w      = batt_w + 2*batt_clear;                 // 26.1 interior width
out_w     = in_w + 2*wall;                         // 29.3 body width
tray_x0   = batt_xc - (batt_l + 2*batt_clear)/2;   // battery bay front
tray_x1   = batt_xc + (batt_l + 2*batt_clear)/2;   // battery bay rear
cab_x1    = tray_x0 - 0.4;                         // switch cab rear (fence)
cab_x0    = cab_x1 - cab_len;                      // switch cab front (wall face)
body_x0   = cab_x0 - wall;                         // outer front
body_x1   = tray_x1 + rwall;                       // outer rear
floor_z0  = batt_z0 - 2;                           // battery floor underside
top_z     = batt_z0 + batt_h + 2.5;                // top of the walls
hatch_t   = 2.0;
brg_z0    = 2.6;                                   // bottom of the bearing walls and can saddle
bunk_z0   = 6;  bunk_t = 1.5;                      // cable bunker floor

// motor cage: long bearing walls either side of the motor, a bar behind
// the gearbox and a saddle under the nose of the can (the motor drops in
// from above through the battery floor, so the saddle can be closed)
sad_x0    = m_body + 1.1;  sad_x1 = sad_x0 + 1.5;      // saddle under the can
cage_x0   = sad_x0;        cage_x1 = gb_x1 + m_gap + 1.2;
sad_z1    = axle_z - m_h/2 - m_gap;                    // saddle top
// opening in the battery floor over the motor (lead exit .. bunker)
bay_x0    = can_x0 - 3;  bay_x1 = tray_x1 - 0.01;  bay_hw = frame_y0 - 0.2;

// switch shelf + roof button (front)
shelf_z   = batt_z0 + 4;                           // shelf top; 4 mm cable slot beneath
btn_x     = switch_type == "inline" ? (cab_x0 + cab_x1)/2 : cab_x0 + pbs_nut/2 + 0.6;
well_r    = pbs_body_d/2 + well_clear;             // bore of the switch well
well_z0   = 10;                                     // bottom of the well (above the front axle)
btn_d     = 12;
btn_hole  = 13;
foot_x    = sw_len_x; foot_y = 18;

// hatch screw: M3 x 10 into a 2.5 mm pilot hole in the rear wall
screw_x   = tray_x1 + rwall/2;

// couplers: 2 x Bambu D6x2 magnets stacked (6 x 4 mm), sealed in
mag_d = 6.3; mag_t = 4.2; mag_z = 10;              // magnet centre height above track top
cpl_len = 5.8;  cpl_hw = 6; cpl_z0 = 6; cpl_z1 = 20;
skin = 0.8;                                         // plastic over the magnet face

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
//  wheels
// =====================================================================
module wheel_flat(drive = false, oring = false) {
    gw = oring ? og_w : groove_w;  gd = oring ? og_dp : groove_dp;
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
        // recessed outer face: a long shaft end stays below the rim
        translate([0, 0, -0.01]) difference() {
            cylinder(d = wheel_d - 7, h = dish_depth);
            cylinder(d = ring_d + 1.5, h = dish_depth + 1);
        }
        if (drive)
            translate([0, 0, (wheel_w - gw)/2]) difference() {
                cylinder(d = wheel_d + 2, h = gw);
                translate([0, 0, -1]) cylinder(d = wheel_d - 2*gd, h = gw + 2);
            }
    }
}

module tyre() {
    difference() {
        cylinder(d = tyre_id + 2*tyre_t, h = tyre_w);
        translate([0, 0, -1]) cylinder(d = tyre_id, h = tyre_w + 2);
    }
}

module wheel_at(x, side, drive = false) {
    translate([x, side * (wheel_y0 + wheel_w), axle_z])
        rotate([side > 0 ? 90 : -90, 0, 0]) wheel_flat(drive);
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
module keyhole(xc) {
    // bearing hole (teardrop, point down, so it prints upside down) with a
    // slot running UP through the floor: the shaft drops in from above
    translate([xc, 0, axle_z]) rotate([-90, 0, 0]) linear_extrude(40, center = true)
        union() { circle(d = bearing_d); rotate(45) square(bearing_d/2); }
    translate([xc - slot_w/2, -20, axle_z]) cube([slot_w, 40, batt_z0 - axle_z + 1]);
}

module bearing_walls(x0, x1, xc) {
    // a pair of frame walls from x0 to x1 with a keyhole bearing at xc
    difference() {
        mirror_y() translate([x0, frame_y0, brg_z0]) cube([x1 - x0, frame_y1 - frame_y0, floor_z0 - brg_z0 + 0.01]);
        keyhole(xc);
    }
}

module coupler_block(front) {
    // buffer-beam block; the top is bevelled 45 deg so it prints
    // without supports when the body is upside down
    xa = front ? body_x0 : body_x1;
    hull() {
        translate([front ? xa - cpl_len : xa - 0.01, -cpl_hw, cpl_z0]) cube([cpl_len + 0.01, 2*cpl_hw, cpl_z1 - cpl_len - cpl_z0]);
        translate([xa - 0.01, -cpl_hw, cpl_z0]) cube([0.02, 2*cpl_hw, cpl_z1 - cpl_z0]);
    }
}

module magnet_pocket(front) {
    // closed cavity: the print is paused, the magnets dropped in, and
    // printing continues over them
    xo = front ? body_x0 - cpl_len + skin : body_x1 + cpl_len - skin - mag_t;
    translate([xo, -mag_d/2, mag_z - mag_d/2]) cube([mag_t, mag_d, mag_d + 0.3]);
}

module body_solid() {
    // upper shell: switch cab + battery bay, open on top
    difference() {
        rounded_box([body_x0, -out_w/2, floor_z0], [body_x1, out_w/2, top_z], 2);
        translate([cab_x0, -in_w/2, batt_z0]) cube([tray_x1 - cab_x0, in_w, 50]);
    }
    // cable bunker behind the drive wheels: walls down to a closed floor
    bunk_x0 = wheel_d/2 + 0.8;
    difference() {
        rounded_box([bunk_x0, -out_w/2, bunk_z0], [body_x1, out_w/2, floor_z0 + 0.01], 2);
        translate([bunk_x0 - 1, -in_w/2, bunk_z0 + bunk_t]) cube([tray_x1 - bunk_x0 + 1, in_w, 40]);
    }
    // front pilot plate between the front wheels, carries the coupler
    translate([body_x0, -frame_y1, cpl_z0]) cube([wall, 2*frame_y1, floor_z0 - cpl_z0 + 0.01]);
    // drive-axle bearing walls, running the length of the motor
    bearing_walls(cage_x0, cage_x1, 0);
    // bar behind the gearbox and saddle under the nose of the can, both
    // bridged between the walls: together they stop the motor turning
    translate([cage_x1 - 1.2, -frame_y0 - 0.01, brg_z0]) cube([1.2, 2*frame_y0 + 0.02, floor_z0 - brg_z0 + 0.01]);
    translate([sad_x0, -frame_y0 - 0.01, brg_z0]) cube([sad_x1 - sad_x0, 2*frame_y0 + 0.02, sad_z1 - brg_z0]);
    // front axle bearing walls
    bearing_walls(front_x - brg_hx, front_x + brg_hx, front_x);
    // stiffeners from the front bearings to the pilot plate
    mirror_y() translate([body_x0, frame_y0, 12]) cube([front_x - brg_hx - body_x0 + 0.01, frame_y1 - frame_y0, floor_z0 - 12 + 0.01]);
    // round well under the switch cab so the button's body is enclosed
    if (switch_type != "inline")
        translate([btn_x, 0, well_z0]) cylinder(r = well_r + 1.0, h = floor_z0 - well_z0 + 0.01);
    // couplers
    coupler_block(true);
    coupler_block(false);
    // inline switch: shelf across the front cab with a full-width fence at
    // its rear edge (both bridge wall to wall, so they print upside down).
    // pbs11: just a low fence to keep the battery holder off the switch body.
    if (switch_type == "inline")
        translate([cab_x0 - 0.01, -in_w/2 - 0.01, shelf_z - 1.5]) cube([cab_len + 0.02, in_w + 0.02, 1.5]);
    translate([cab_x1 - 1.2, -in_w/2 - 0.01, switch_type == "inline" ? shelf_z - 0.01 : batt_z0 - 0.01]) cube([1.2, in_w + 0.02, 2]);
}

module body_cuts() {
    // opening in the battery floor over the motor and the bunker
    translate([bay_x0, -bay_hw, floor_z0 - 1]) cube([bay_x1 - bay_x0, 2*bay_hw, 5]);
    // axle slots through the floor ledges (shafts drop in from above)
    for (x = [0, front_x]) translate([x - slot_w/2, -in_w/2 - 0.01, floor_z0 - 1]) cube([slot_w, in_w + 0.02, 5]);
    // wheel arches through the floor ledges and side walls
    for (x = [0, front_x]) mirror_y()
        translate([x, wheel_y0 - 0.3, axle_z]) rotate([-90, 0, 0]) cylinder(d = wheel_d + 2.4, h = 6);
    // cable slot under the switch shelf (open to the battery bay)
    if (switch_type == "inline")
        translate([cab_x0 - 0.01, -in_w/2, batt_z0 - 0.01]) cube([cab_len + 0.5, in_w, shelf_z - 1.5 - batt_z0]);
    // bore of the switch well
    if (switch_type != "inline")
        translate([btn_x, 0, well_z0 + 1.0]) cylinder(r = well_r, h = 40);
    // hatch screw pilot hole in the rear wall
    translate([screw_x, 0, top_z - 12]) cylinder(d = 2.5, h = 13);
    // hatch tongue slot through the front wall
    translate([body_x0 - 1, -8, top_z - 2.4]) cube([wall + 2, 16, 1.2]);
    // magnet pockets
    magnet_pocket(true);
    magnet_pocket(false);
    // decoration: recessed windows at both ends of each side
    for (x = [body_x0 + 4, body_x1 - 4 - 9]) mirror_y()
        translate([x, out_w/2 - 0.6, top_z - 12]) cube([9, 1, 8]);
    // engraved door outline, middle of each side
    mirror_y() translate([batt_xc, out_w/2 - 0.5, 0]) difference() {
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
    lip_x0  = cab_x0 + 2.5;            // lip stops short of the tongue end
    difference() {
        union() {
            rounded_box([body_x0, -out_w/2, top_z], [body_x1, out_w/2, top_z + hatch_t], 2);
            // locating lip just inside the walls
            difference() {
                translate([lip_x0, -in_w/2 + lip_gap, top_z - 2]) cube([tray_x1 - lip_gap - lip_x0, in_w - 2*lip_gap, 2.01]);
                translate([lip_x0 - 1, -in_w/2 + lip_gap + 1.2, top_z - 3]) cube([tray_x1 - lip_gap - lip_x0 - 0.2, in_w - 2*lip_gap - 2.4, 4]);
            }
            // tongue that passes through the front wall, hung from the
            // roof by a web just inside the wall
            translate([body_x0, -7.5, top_z - 2.2]) cube([cab_x0 + 0.3 - body_x0 + 0.01, 15, 1.0]);
            translate([cab_x0 + 0.3, -7.5, top_z - 2.2]) cube([lip_x0 - cab_x0 - 0.3 + 0.01, 15, 2.21]);
        }
        if (switch_type == "inline") {
            // keep the lip clear of the button flange
            translate([btn_x, 0, top_z - 3]) cylinder(d = btn_hole + 4, h = 3);
            // button hole with a soft chamfer
            translate([btn_x, 0, top_z - 5]) cylinder(d = btn_hole, h = 20);
            translate([btn_x, 0, top_z + hatch_t - 0.6]) cylinder(d1 = btn_hole, d2 = btn_hole + 1.2, h = 0.61);
        } else {
            // panel hole for the PBS-11A, nut clearance below
            translate([btn_x, 0, top_z - 5]) cylinder(d = pbs_hole, h = 20);
            translate([btn_x, 0, top_z - 3]) cylinder(d = pbs_nut + 1.5, h = 3);
        }
        // M3 screw hole over the rear wall, counterbored for a socket cap head
        // (5.5 mm head sits ~1.8 mm proud); a flat head also fits
        translate([screw_x, 0, top_z - 5]) cylinder(d = 3.4, h = 20);
        translate([screw_x, 0, top_z + hatch_t - 1.2]) cylinder(d = 6.2, h = 1.21);
        // engraved roof panel lines
        for (x = [tray_x0 + 6, tray_x1 - 10]) translate([x, -out_w/2 + 3, top_z + hatch_t - 0.5]) cube([0.8, out_w - 6, 1]);
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
        translate([0, 0, top_z - 2.4]) cylinder(d1 = btn_d, d2 = btn_hole + 1.6, h = 2.4);
        // domed top
        translate([0, 0, btn_top_z - 2]) scale([1, 1, 0.3]) sphere(d = btn_d);
    }
}

module shim() { cube([sw_len_x, 20, 2]); }

// =====================================================================
//  dummy purchased parts (preview and clearance checks only)
// =====================================================================
module dummy_motor() {
    translate([0, 0, axle_z]) {
        color("Silver") translate([m_body, -m_w/2, -m_h/2]) cube([m_rear - m_body, m_w, m_h]);
        color("Goldenrod") translate([m_body - 1.0, -m_w/2, -m_h/2]) cube([1.0, m_w, m_h]);   // gearbox-side detail omitted
        color("Black") translate([m_cap1, -m_w/2, -m_h/2]) cube([m_cap0 - m_cap1, m_w, m_h]);
        color("Silver") translate([m_cap0 - 1.5, -2, -2]) cube([1.5, 4, 4]);
        color("Goldenrod") for (y = [-2.2, 1.2]) translate([m_end, y, -2]) cube([m_cap1 - m_end, 1, 4]);
        color("Silver") rotate([90, 0, 0]) cylinder(d = shaft_d, h = 2*m_shaft_tip, center = true);
        color("Silver") mirror_y() translate([0, m_w/2 - 0.01, 0]) rotate([-90, 0, 0]) cylinder(d = m_boss_d, h = m_boss_y - m_w/2 + 0.01);
    }
}
module dummy_battery() {
    color("DimGray") translate([batt_xc - batt_l/2, -batt_w/2, batt_z0]) cube([batt_l, batt_w, batt_h]);
}
module dummy_switch() {
    if (switch_type == "inline")
        color("Black") translate([btn_x - sw_len_x/2, -sw_len_y/2, shelf_z]) cube([sw_len_x, sw_len_y, sw_h_nom]);
    else translate([btn_x, 0, top_z + hatch_t]) {
        color("Red")   cylinder(d = pbs_cap_d, h = pbs_cap_h);
        color("Black") translate([0, 0, -0.01]) cylinder(d = pbs_flange, h = 1.5);
        color("Black") translate([0, 0, -hatch_t - 4]) cylinder(d = pbs_nut, h = 4, $fn = 6);        // nut
        color("DimGray") translate([0, 0, -hatch_t - pbs_below]) cylinder(d = pbs_body_d, h = pbs_below);
    }
}
module dummy_track() {
    color("BurlyWood") translate([-90, -20, -12]) difference() {
        cube([180, 40, 12]);
        for (s = [-1, 1]) translate([-1, 20 + s*groove_c - 3, 9]) cube([182, 6, 5]);
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
echo(str("Overhang beyond the axles: front ", front_x - (body_x0 - cpl_len), " mm, rear ", body_x1 + cpl_len, " mm"));

module wheels(drive = false) {
    for (s = [-1, 1]) { wheel_at(0, s, drive); wheel_at(front_x, s); }
    axle_at();
}

module assembly() {
    color("SteelBlue") body();
    color("SteelBlue") hatch();
    if (switch_type == "inline") color("Red") button();
    color("Gold") wheels();
    dummy_motor();
    dummy_battery();
    dummy_switch();
    %dummy_track();
}

if (part == "body") translate([0, 0, top_z]) rotate([180, 0, 0]) body();
else if (part == "hatch") translate([0, 0, top_z + hatch_t]) rotate([180, 0, 0]) hatch();
else if (part == "button") translate([-btn_x, 0, -btn_rest_z]) button();
else if (part == "wheel") wheel_flat(false);
else if (part == "wheel_drive") wheel_flat(true);
else if (part == "wheel_drive_oring") wheel_flat(true, true);
else if (part == "tyre") tyre();
else if (part == "axle") axle_flat();
else if (part == "shim") shim();
else if (part == "assembly") assembly();
else if (part == "cutaway") {
    difference() {
        union() { color("SteelBlue") body(); color("SteelBlue") hatch(); if (switch_type == "inline") color("Red") button(); }
        translate([-100, -50, -10]) cube([200, 50, 100]);
    }
    color("Gold") { wheel_at(0, 1); wheel_at(front_x, 1); }
    dummy_motor(); dummy_battery(); dummy_switch();
}
else if (part == "underside") {
    color("SteelBlue") body(); color("SteelBlue") hatch();
    color("Gold") wheels();
    dummy_motor();
}
