// Auto-generated draft by tools/sign_factory/build_signs.py
// "Patricia Ravine Doubletrack" / Patrishya wâtikamâw nîso-meskanaw / ᐸᕒᐃᔥᔭ ᐚᑎᑲᒫᐤ ᓃᓱ ᒣᐢᑲᓇᐤ  [icon: mountain]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#8a8a8a") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { union(){polygon([[-44,-26],[-6,34],[30,-26]]);polygon([[2,-26],[34,28],[46,-26]]);} }
  color("#f2f2f2") translate([0, -10.000, 1.750]) linear_extrude(height=1.800) scale([0.6304,0.6304,1]) { polygon([[-16,16],[-6,34],[4,16]]); }
}

module lettering() {
  // English (bottom)
  translate([0, -63.620, 1.750]) linear_extrude(height=1.500) text("Patricia Ravine", size=8.000, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -73.380, 1.750]) linear_extrude(height=1.500) text("Doubletrack", size=8.000, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 70.160, 1.750]) linear_extrude(height=1.500) text("Patrishya wâtikamâw", size=6.000, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 62.840, 1.750]) linear_extrude(height=1.500) text("nîso-meskanaw", size=6.000, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 47.380, 1.750]) linear_extrude(height=2.600) text("ᐸᕒᐃᔥᔭ ᐚᑎᑲᒫᐤ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 37.620, 1.750]) linear_extrude(height=2.600) text("ᓃᓱ ᒣᐢᑲᓇᐤ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
