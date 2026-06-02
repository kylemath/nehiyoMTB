// Auto-generated draft by tools/sign_factory/build_signs.py
// "Selkirk Knights" / Selkirk simâkanisak / ᓭᓪᑭᕒᐠ ᓯᒫᑲᓂᓴᐠ  [icon: star]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#e0b04a") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { polygon(points=[[0.00,-40.00],[9.99,-13.75],[38.04,-12.36],[16.17,5.25],[23.51,32.36],[0.00,17.00],[-23.51,32.36],[-16.17,5.25],[-38.04,-12.36],[-9.99,-13.75]]); }
}

module lettering() {
  // English (bottom)
  translate([0, -62.095, 1.750]) linear_extrude(height=1.500) text("Selkirk", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -74.905, 1.750]) linear_extrude(height=1.500) text("Knights", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 70.465, 1.750]) linear_extrude(height=1.500) text("Selkirk", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 62.535, 1.750]) linear_extrude(height=1.500) text("simâkanisak", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 49.820, 1.750]) linear_extrude(height=2.600) text("ᓭᓪᑭᕒᐠ", size=12.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 35.180, 1.750]) linear_extrude(height=2.600) text("ᓯᒫᑲᓂᓴᐠ", size=12.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
