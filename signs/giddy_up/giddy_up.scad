// Auto-generated draft by tools/sign_factory/build_signs.py
// "Giddy Up" / mâci-pimipahtâ / ᒫᒋᐱᒥᐸᐦᑖ  [icon: cowboyhat]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#7a5230") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { union(){translate([0,-8])scale([1.6,0.5])circle(34);translate([0,6])scale([1,1.3])circle(20);} }
}

module lettering() {
  // English (bottom)
  translate([0, -68.500, 1.750]) linear_extrude(height=1.500) text("Giddy Up", size=15.000, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 66.500, 1.750]) linear_extrude(height=1.500) text("mâci-pimipahtâ", size=8.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 42.500, 1.750]) linear_extrude(height=2.600) text("ᒫᒋᐱᒥᐸᐦᑖ", size=13.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
