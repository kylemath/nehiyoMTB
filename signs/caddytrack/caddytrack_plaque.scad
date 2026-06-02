$fn = 64;
module blank_plaque() {
  difference() {
    union() {
      linear_extrude(height=1.200)
        offset(r=3.500) offset(r=-3.500)
          square([73.000, 138.000], center=true);
      translate([0.000, 37.200, 0]) cylinder(h=1.700, r=3.500);
      translate([0.000, -42.200, 0]) cylinder(h=1.700, r=3.500);
    }
    translate([0.000, 37.200, -1]) cylinder(h=3.700, r=2.100);
    translate([0.000, -42.200, -1]) cylinder(h=3.700, r=2.100);
  }
}

blank_plaque();
