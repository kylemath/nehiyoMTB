// Auto-generated draft by tools/sign_factory/build_signs.py
// "Spanish Switchblade" / Aspayôl kîskatahikan / ᐊᔅᐸᔪᓪ ᑮᐢᑎᑲᐦᐃᑲᐣ  [icon: blade]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#8a8a8a") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { polygon([[-36,-6],[24,-6],[36,2],[24,10],[-36,10]]); }
  color("#7a5230") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { translate([-40,2])square([16,16],center=true); }
}

module lettering() {
  // English (bottom)
  translate([0, -62.095, 1.750]) linear_extrude(height=1.500) text("Spanish", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -74.905, 1.750]) linear_extrude(height=1.500) text("Switchblade", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 70.465, 1.750]) linear_extrude(height=1.500) text("Aspayôl", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 62.535, 1.750]) linear_extrude(height=1.500) text("kîskatahikan", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 49.515, 1.750]) linear_extrude(height=2.600) text("ᐊᔅᐸᔪᓪ", size=11.500, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 35.485, 1.750]) linear_extrude(height=2.600) text("ᑮᐢᑎᑲᐦᐃᑲᐣ", size=11.500, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
