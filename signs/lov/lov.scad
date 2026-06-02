// Auto image-pipeline draft (tools/sign_factory/build_signs.py)
// "LOV"  icon=lov_icon.stl
$fn = 36;

module blank_plaque() {
  translate([-45, -82.5, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  translate([0, 6.0, 1.75]) import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/signs/lov/lov_icon.stl", convexity=10);
}

module lettering() {
  // English (bottom)
  translate([0, -68.500, 1.750]) linear_extrude(height=1.500) text("LOV", size=16.000, halign="center", valign="center", font="Raleway:style=Bold");
  // translit (top)
  translate([0, 67.500, 1.750]) linear_extrude(height=1.500) text("sâkihiwêwin", size=11.000, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (overlaid, protruding)
  translate([0, 6.000, 1.750]) linear_extrude(height=3.500) text("ᓵᑭᐦᐃᐌᐎᐣ", size=13.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() { blank_plaque(); icon_model(); lettering(); syllabics_text(); }
