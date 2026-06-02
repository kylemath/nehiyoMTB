// Auto image-pipeline draft (tools/sign_factory/build_signs.py)
// "Wanyandi Access"  icon=wanyandi_access_icon.stl
$fn = 36;

module blank_plaque() {
  translate([-45, -82.5, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  translate([0, 6.0, 1.75]) import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/signs/wanyandi_access/wanyandi_access_icon.stl", convexity=10);
}

module lettering() {
  // English (bottom)
  translate([0, -62.095, 1.750]) linear_extrude(height=1.500) text("Wanyandi", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -74.905, 1.750]) linear_extrude(height=1.500) text("Access", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  // translit (top)
  translate([0, 71.465, 1.750]) linear_extrude(height=1.500) text("Wanyandi", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 63.535, 1.750]) linear_extrude(height=1.500) text("pîhtokêwi-meskanaw", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (overlaid, protruding)
  translate([0, 10.880, 1.750]) linear_extrude(height=3.500) text("ᐗᓐᔭᐣᑎ ᐱᐦᑐᑫᐎ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 1.120, 1.750]) linear_extrude(height=3.500) text("ᒣᐢᑲᓇᐤ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() { blank_plaque(); icon_model(); lettering(); syllabics_text(); }
