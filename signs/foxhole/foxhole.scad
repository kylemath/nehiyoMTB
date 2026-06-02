// Auto-generated draft by tools/sign_factory/build_signs.py
// "Foxhole" / mahkêsîso-wâti / ᒪᐦᑫᓰᓱ ᐧᐋᑎ  [icon: fox]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#d3792b") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { union(){polygon([[-30,18],[30,18],[0,-34]]);polygon([[-30,18],[-14,40],[-6,20]]);polygon([[30,18],[14,40],[6,20]]);} }
  color("#f2f2f2") translate([0, -10.000, 1.750]) linear_extrude(height=1.800) scale([0.6304,0.6304,1]) { polygon([[-8,-16],[8,-16],[0,-36]]); }
}

module lettering() {
  // English (bottom)
  translate([0, -68.500, 1.750]) linear_extrude(height=1.500) text("Foxhole", size=16.000, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 66.500, 1.750]) linear_extrude(height=1.500) text("mahkêsîso-wâti", size=8.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 49.820, 1.750]) linear_extrude(height=2.600) text("ᒪᐦᑫᓰᓱ", size=12.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 35.180, 1.750]) linear_extrude(height=2.600) text("ᐧᐋᑎ", size=12.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
