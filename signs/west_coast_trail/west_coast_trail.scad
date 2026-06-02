// Auto-generated draft by tools/sign_factory/build_signs.py
// "West Coast Trail" / pahkisimohtâhk sîpiya meskanaw / ᐹᐦᑭᓯᒧᑖᐦᐠ ᓰᐱᔭ ᒣᐢᑲᓇᐤ  [icon: pine]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#3a8a3a") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { union(){translate([-4,-34])square([8,16],center=true);polygon([[-22,-22],[22,-22],[0,4]]);polygon([[-18,-2],[18,-2],[0,20]]);polygon([[-13,16],[13,16],[0,36]]);} }
}

module lettering() {
  // English (bottom)
  translate([0, -62.095, 1.750]) linear_extrude(height=1.500) text("West Coast", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -74.905, 1.750]) linear_extrude(height=1.500) text("Trail", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 70.465, 1.750]) linear_extrude(height=1.500) text("pahkisimohtâhk", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 62.535, 1.750]) linear_extrude(height=1.500) text("sîpiya meskanaw", size=6.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 48.600, 1.750]) linear_extrude(height=2.600) text("ᐹᐦᑭᓯᒧᑖᐦᐠ", size=10.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 36.400, 1.750]) linear_extrude(height=2.600) text("ᓰᐱᔭ ᒣᐢᑲᓇᐤ", size=10.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
