// =====================================================================
//  Train-Tripped Semaphore Signal  -  Brio-compatible straight track
// =====================================================================
//  A 144 mm straight track with a hidden see-saw "treadle" in one groove.
//  When a wheel rolls over the treadle it presses it flush with the
//  groove floor; the other end of the see-saw lifts a push-rod inside the
//  signal post, which raises the semaphore blade from "danger"
//  (horizontal) to "clear" (~43 deg up).  When the train has passed,
//  gravity drops everything back.  No batteries, springs or glue.
//
//  Parts (select with `part`):
//    "base"         track + signal post (print upright, as modelled)
//    "seesaw"       treadle lever      (print lying on its flat side)
//    "rod"          push-rod           (print lying down)
//    "blade"        semaphore blade    (single colour)
//    "blade_red"    blade minus stripe (AMS: red)
//    "blade_white"  stripe only        (AMS: white)
//    "assembly"     everything in place, at rest
//    "assembly_pressed"  everything with the treadle pressed
//
//  Hardware: two pieces of 1.75 mm filament used as axle pins
//    - see-saw pin: ~14 mm, pushed in from the track side
//    - blade pin:   ~8 mm, pushed through the signal post
//
//  Coordinates: track runs along +X (0..144), centred on Y=0,
//  bottom at Z=0.  The signal stands on the +Y side.
// =====================================================================

part = "assembly";
female_female = false;     // true -> female sockets on both ends

$fn = 64;

// ---------------- Brio track standard ----------------
track_len   = 144;
track_w     = 40;
track_h     = 12;
groove_w    = 6;
groove_d    = 3;
groove_c    = 13;          // groove centre offset from track centreline
floor_z     = track_h - groove_d;   // 9

// connectors
peg_d       = 11.6;
peg_c       = 12.5;        // face -> peg centre
neck_w      = 6;
peg_h       = 11.5;
sock_d      = 13.2;
sock_c      = 12.5;
sock_neck_w = 7.4;

// ---------------- mechanism ----------------
pin_tight   = 1.9;         // hole for 1.75 filament, press fit (in base)
pin_free    = 2.3;         // hole for 1.75 filament, free rotation
P           = 66;          // see-saw pivot X
pivot_z     = 4;           // see-saw pivot height
theta       = 9.6;         // treadle travel (deg)
plate_t     = 2.4;         // see-saw plate thickness (Y)
plate_y0    = groove_c - plate_t/2;      // 11.8
arm_r       = 20;          // pivot -> push-rod distance
rod_x       = P - arm_r;   // push-rod position
rod_y       = 30;
rod_s       = 3.0;         // rod square section
rod_clear   = 0.3;
arm_top     = 3.0;         // top of see-saw arm at rest (rod sits here)
arm_bot     = 0.4;
roof_z      = 6.8;         // underside of cavity roof under the groove
arm_roof_z  = 7.2;         // roof of the arm channel

// signal post
rod_d    = 4.7;            // blade pivot -> rod contact (keeps rod clear of hub)
blade_px = rod_x - rod_d;  // blade pivot X
mast_x0 = blade_px - 3.5;  mast_x1 = rod_x + 3;
mast_y0 = 26;  mast_y1 = 34;
blade_pz = 60;             // blade pivot Z
blade_t  = 2.4;
slot_w   = 3.0;
slot_z0  = 52;
slot_z1  = 74.5;
cap_z1   = 78;
contact_z = -2.2;          // blade underside at rod contact (blade frame)
rod_len  = blade_pz + contact_z - arm_top;

// platform beside the track that carries the post
plat_x0 = mast_x0 - 6; plat_x1 = rod_x + 9; plat_y1 = 36;

// =====================================================================
//  helpers
// =====================================================================
module teardrop_y(d, y0, y1) {
    // hole along Y, printable on its side (point up = +Z)
    translate([0, y1, 0]) rotate([90, 0, 0])
        linear_extrude(y1 - y0)
            union() {
                circle(d = d);
                rotate(45) square(d/2);
            }
}

module chamfer_box(size, c) {
    // box with top edges chamfered by c
    hull() {
        cube([size[0], size[1], size[2] - c]);
        translate([c, c, 0]) cube([size[0] - 2*c, size[1] - 2*c, size[2]]);
    }
}

// =====================================================================
//  track base
// =====================================================================
module groove(sign) {
    yc = sign * groove_c;
    // straight groove
    translate([-1, yc - groove_w/2, floor_z]) cube([track_len + 2, groove_w, 10]);
    // entry flares at both ends
    for (xe = [0, track_len])
        translate([xe, yc, track_h])
            hull() for (dx = [-0.01, 0.01]) translate([dx, 0, 0])
                rotate([0, 90, 0]) linear_extrude(4, center = true)
                    polygon([[0, -groove_w/2 - 1], [0, groove_w/2 + 1],
                             [1, groove_w/2], [1, -groove_w/2]]);
}

module male_connector() {
    translate([track_len, 0, 0]) {
        hull() {
            translate([-1, -neck_w/2, 0]) cube([peg_c, neck_w, peg_h - 0.8]);
            translate([-1, -neck_w/2 + 0.8, 0]) cube([peg_c, neck_w - 1.6, peg_h]);
        }
        translate([peg_c, 0, 0]) cylinder(d = peg_d, h = peg_h - 0.8);
        translate([peg_c, 0, peg_h - 0.8]) cylinder(d1 = peg_d, d2 = peg_d - 1.6, h = 0.8);
    }
}

module female_socket(at_start = true) {
    m = at_start ? [0, 0, 0] : [track_len, 0, 0];
    r = at_start ? 0 : 180;
    translate(m) rotate([0, 0, r]) {
        translate([-1, -sock_neck_w/2, -1]) cube([sock_c + 1, sock_neck_w, track_h + 2]);
        translate([sock_c, 0, -1]) cylinder(d = sock_d, h = track_h + 2);
        // top lead-in
        translate([sock_c, 0, track_h - 0.6]) cylinder(d1 = sock_d, d2 = sock_d + 1.2, h = 0.61);
    }
}

module base_solid() {
    // main track body with chamfered long top edges
    hull() {
        translate([0, -track_w/2, 0]) cube([track_len, track_w, track_h - 1]);
        translate([0, -track_w/2 + 1, 0]) cube([track_len, track_w - 2, track_h]);
    }
    // platform carrying the signal post
    translate([plat_x0, 0, 0]) chamfer_box([plat_x1 - plat_x0, plat_y1, track_h], 1);
    // post: flared foot, shaft, cap and finial
    hull() {
        translate([mast_x0 - 2, mast_y0 - 2, track_h - 0.01]) cube([mast_x1 - mast_x0 + 4, mast_y1 - mast_y0 + 4, 0.01]);
        translate([mast_x0, mast_y0, track_h + 5]) cube([mast_x1 - mast_x0, mast_y1 - mast_y0, 0.01]);
    }
    translate([mast_x0, mast_y0, 0]) cube([mast_x1 - mast_x0, mast_y1 - mast_y0, cap_z1]);
    // cap overhang + finial
    translate([mast_x0 - 0.8, mast_y0 - 0.8, cap_z1 - 1.2])
        chamfer_box([mast_x1 - mast_x0 + 1.6, mast_y1 - mast_y0 + 1.6, 2.4], 0.8);
    mx = (mast_x0 + mast_x1)/2; my = (mast_y0 + mast_y1)/2;
    translate([mx, my, cap_z1 + 1]) cylinder(d1 = 4, d2 = 2.4, h = 2);
    translate([mx, my, cap_z1 + 4.2]) sphere(d = 4.4, $fn = 32);
    // ladder rungs on the outer face (decoration, printable)
    for (z = [track_h + 8 : 5 : slot_z0 - 3])
        translate([mast_x0 + 2, mast_y1 - 0.01, z]) cube([mast_x1 - mast_x0 - 4, 0.8, 1]);
    if (!female_female) male_connector();
}

module base_cuts() {
    groove(1);
    groove(-1);
    female_socket(true);
    if (female_female) female_socket(false);

    // --- see-saw cavity (open underneath) ---
    // lower cavity under the groove
    translate([rod_x - 2.6, 10.6, -1]) cube([P + 28 - (rod_x - 2.6), 16.4 - 10.6, roof_z + 1]);
    // treadle slot through the groove floor
    translate([P - 1.2, groove_c - 1.6, roof_z - 0.8]) cube([29.2, 3.2, 10]);
    // channel for the see-saw arm, running out under the post
    translate([rod_x - 2.6, 10.6, -1]) cube([5.2, rod_y + 3.2 - 10.6, arm_roof_z + 1]);
    // push-rod channel up the post into the blade slot
    rc = rod_s + 2*rod_clear;
    translate([rod_x - rc/2, rod_y - rc/2, arm_roof_z - 1]) cube([rc, rc, slot_z0 + 2]);
    // blade slot through the post head
    translate([mast_x0 - 1, rod_y - slot_w/2, slot_z0]) cube([mast_x1 - mast_x0 + 2, slot_w, slot_z1 - slot_z0]);
    // see-saw pivot pin hole (push filament in from the track side)
    translate([P, 0, pivot_z]) teardrop_y(pin_tight, 6.5, track_w/2 + 0.1);
    // blade pivot pin hole (through both cheeks)
    translate([blade_px, 0, blade_pz]) teardrop_y(pin_tight, mast_y0 - 1, mast_y1 + 1);
}

module base() {
    difference() { base_solid(); base_cuts(); }
}

// =====================================================================
//  see-saw treadle (modelled in world coordinates, rest pose)
// =====================================================================
// profile in (r = x - P, z)
plate_profile = [
    [-arm_r - 2, arm_bot], [-arm_r - 2, arm_top], [-arm_r + 2, arm_top], [-1, 6.3],
    [0, 8.9],                 // treadle starts flush with floor at the pivot
    [16, 11.4], [18, 11.4],   // peak 2.4 mm above the groove floor
    [27, 8.6],                // ramps back down below the floor
    [27, 5.0], [4, 1.0]
];

module plate2d() { translate([P, 0]) polygon(plate_profile); }

module seesaw_rest() {
    difference() {
        union() {
            // main plate (Y = plate_y0 .. plate_y0 + plate_t)
            translate([0, plate_y0 + plate_t, 0]) rotate([90, 0, 0])
                linear_extrude(plate_t) plate2d();
            // arm out to the push-rod
            translate([rod_x - 2, plate_y0, arm_bot]) cube([4, rod_y + 2 - plate_y0, arm_top - arm_bot]);
            // stop flange (hits the cavity roof at rest)
            translate([0, plate_y0 + plate_t + 1.6, 0]) rotate([90, 0, 0])
                linear_extrude(1.6 + 0.01)
                    intersection() {
                        plate2d();
                        translate([P + 18, 0]) square([8, roof_z - 0.05]);
                    }
        }
        // pivot hole
        translate([P, plate_y0 - 1, pivot_z]) rotate([-90, 0, 0]) cylinder(d = pin_free, h = 30);
    }
}

module seesaw_pose(pressed = false) {
    if (pressed)
        translate([P, 0, pivot_z]) rotate([0, theta, 0]) translate([-P, 0, -pivot_z]) seesaw_rest();
    else seesaw_rest();
}

// =====================================================================
//  push-rod (modelled standing, rest pose)
// =====================================================================
module rod_rest() {
    // square rod with both ends rounded about Y so it rocks cleanly on the
    // tilting see-saw arm and slides under the blade
    translate([rod_x, rod_y - rod_s/2, arm_top])
        hull() for (z = [rod_s/2, rod_len - rod_s/2])
            translate([0, 0, z]) rotate([-90, 0, 0])
                intersection() {
                    cylinder(d = rod_s, h = rod_s);
                    translate([-rod_s/2, -rod_s/2, 0]) cube([rod_s, rod_s, rod_s]);
                }
}

// rod lift when pressed = rise of the arm at r = -arm_r
rod_lift = arm_r * sin(theta);

// =====================================================================
//  semaphore blade (blade frame: pivot at origin, X along blade, Z up)
// =====================================================================
blade_len = 36;
stripe_x0 = 28; stripe_x1 = 31;

module blade2d() {
    difference() {
        union() {
            circle(r = 3.0);
            // neck with flat underside where the rod pushes
            translate([0, contact_z]) square([12.5, 2 - contact_z]);
            // blade
            polygon([[12, -4], [blade_len, -4], [blade_len, 4], [12, 4], [10, 2], [10, contact_z]]);
        }
        circle(d = pin_free);
    }
}

module stripe2d() { translate([stripe_x0, -4]) square([stripe_x1 - stripe_x0, 8]); }

module blade_flat(which = "all") {
    // lying flat for printing, thickness along Z
    linear_extrude(blade_t)
        if (which == "red") difference() { blade2d(); stripe2d(); }
        else if (which == "white") intersection() { blade2d(); stripe2d(); }
        else blade2d();
}

// blade angle that matches a given rod lift (solved numerically)
// (rounded rod tip of radius rod_s/2 staying tangent to the blade's flat)
function lift_at(phi) = (rod_d*sin(phi) + contact_z - rod_s/2)/cos(phi) - (contact_z - rod_s/2);
function solve_phi(lift, lo = 0, hi = 80, n = 30) =
    n == 0 ? (lo + hi)/2 :
    lift_at((lo + hi)/2) > lift ? solve_phi(lift, lo, (lo + hi)/2, n - 1)
                                : solve_phi(lift, (lo + hi)/2, hi, n - 1);
blade_up = solve_phi(rod_lift);
echo(str("rod lift = ", rod_lift, " mm, blade raises to ", blade_up, " deg"));

module blade_pose(phi = 0, which = "all") {
    translate([blade_px, rod_y + blade_t/2, blade_pz])
        rotate([90, 0, 0]) rotate([0, 0, phi]) blade_flat(which);
}

// =====================================================================
//  output
// =====================================================================
module assembly(pressed = false) {
    color("BurlyWood") base();
    color("Gold") seesaw_pose(pressed);
    color("DimGray") translate([0, 0, pressed ? rod_lift : 0]) rod_rest();
    color("Red")   blade_pose(pressed ? blade_up : 0, "red");
    color("White") blade_pose(pressed ? blade_up : 0, "white");
}

if (part == "base") base();
else if (part == "seesaw")
    // plate face (Y = plate_y0) down on the bed, arm pointing up
    translate([0, 0, -plate_y0]) rotate([90, 0, 0]) seesaw_rest();
else if (part == "rod")
    translate([0, 0, rod_s/2]) rotate([0, 90, 0]) translate([-rod_x, -rod_y, -arm_top]) rod_rest();
else if (part == "blade") blade_flat("all");
else if (part == "blade_red") blade_flat("red");
else if (part == "blade_white") blade_flat("white");
else if (part == "assembly") assembly(false);
else if (part == "assembly_pressed") assembly(true);
