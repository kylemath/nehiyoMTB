// Auto-generated draft by tools/sign_factory/build_signs.py
// "Hawrelak Park Access" / Hawrêlak pîhtokêwi-meskanaw / ᐦᐊᐧᕒᐁᓚᐠ ᐱᐦᑐᑫᐎ ᒣᐢᑲᓇᐤ  [icon: sun_mountain]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#3a8a3a") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { polygon([[-46,-30],[-10,18],[10,-6],[28,22],[46,-30]]); }
  color("#e0b04a") translate([0, -10.000, 1.750]) linear_extrude(height=1.800) scale([0.6304,0.6304,1]) { union(){translate([0,24])circle(14);rotate(0)translate([0,42])square([3,10],center=true);rotate(45)translate([0,42])square([3,10],center=true);rotate(90)translate([0,42])square([3,10],center=true);rotate(135)translate([0,42])square([3,10],center=true);rotate(180)translate([0,42])square([3,10],center=true);rotate(225)translate([0,42])square([3,10],center=true);rotate(270)translate([0,42])square([3,10],center=true);rotate(315)translate([0,42])square([3,10],center=true);} }
}

module lettering() {
  // English (bottom)
  translate([0, -62.095, 1.750]) linear_extrude(height=1.500) text("Hawrelak", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -74.905, 1.750]) linear_extrude(height=1.500) text("Park Access", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 70.465, 1.750]) linear_extrude(height=1.500) text("Hawrêlak", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 62.535, 1.750]) linear_extrude(height=1.500) text("pîhtokêwi-meskanaw", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 47.380, 1.750]) linear_extrude(height=2.600) text("ᐦᐊᐧᕒᐁᓚᐠ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 37.620, 1.750]) linear_extrude(height=2.600) text("ᐱᐦᑐᑫᐎ ᒣᐢᑲᓇᐤ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
