// Auto-generated draft by tools/sign_factory/build_signs.py
// "UofA-6" / okiskinohamâtowikamik 6 / ᐅᑭᐢᑭᓄᐦᐊᒫᑐᐎᑲᒥᐠ 6  [icon: gradcap]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#1c1c1c") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { union(){rotate(45)square([40,40],center=true);translate([0,-12])square([26,16],center=true);} }
  color("#e0b04a") translate([0, -10.000, 1.750]) linear_extrude(height=1.800) scale([0.6304,0.6304,1]) { union(){translate([26,2])square([3,24],center=false);translate([27,26])circle(5);} }
}

module lettering() {
  // English (bottom)
  translate([0, -68.500, 1.750]) linear_extrude(height=1.500) text("UofA-6", size=16.000, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 69.855, 1.750]) linear_extrude(height=1.500) text("okiskinohamâtowikamik", size=5.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 63.145, 1.750]) linear_extrude(height=1.500) text("6", size=5.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 46.770, 1.750]) linear_extrude(height=2.600) text("ᐅᑭᐢᑭᓄᐦᐊᒫᑐᐎᑲᒥᐠ", size=7.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 38.230, 1.750]) linear_extrude(height=2.600) text("6", size=7.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
