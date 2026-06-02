// Auto-generated draft by tools/sign_factory/build_signs.py
// "Kinnaird Killer" / Kinêrd onipahtâkêw / ᑭᓀᕒᐟ ᐅᓂᐸᐦᑖᑫᐤ  [icon: skull]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#f2f2f2") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { difference(){union(){circle(30);translate([0,-26])polygon([[-16,0],[16,0],[12,-16],[-12,-16]]);}translate([-12,4])circle(8);translate([12,4])circle(8);translate([0,-10])polygon([[-4,0],[4,0],[0,-8]]);} }
}

module lettering() {
  // English (bottom)
  translate([0, -62.095, 1.750]) linear_extrude(height=1.500) text("Kinnaird", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -74.905, 1.750]) linear_extrude(height=1.500) text("Killer", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 66.500, 1.750]) linear_extrude(height=1.500) text("Kinêrd onipahtâkêw", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 49.820, 1.750]) linear_extrude(height=2.600) text("ᑭᓀᕒᐟ", size=12.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 35.180, 1.750]) linear_extrude(height=2.600) text("ᐅᓂᐸᐦᑖᑫᐤ", size=12.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
