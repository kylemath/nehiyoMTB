// Auto-generated draft by tools/sign_factory/build_signs.py
// "Silverberry Dirt Jumps" / Silvêrbêri asiski-kwâskwêpayiwina / ᓯᓪᕓᕒᐯᕒᐃ ᐊᓯᐢᑭ ᑵᐢᑴᐸᔨᐎᓇ  [icon: scooter]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#1c1c1c") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { union(){difference(){translate([-22,-16])circle(13);translate([-22,-16])circle(7);}difference(){translate([22,-16])circle(13);translate([22,-16])circle(7);}polygon([[-22,-16],[18,18],[26,18],[24,12],[-18,-20]]);translate([22,22])square([20,6],center=true);} }
}

module lettering() {
  // English (bottom)
  translate([0, -62.095, 1.750]) linear_extrude(height=1.500) text("Silverberry", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -74.905, 1.750]) linear_extrude(height=1.500) text("Dirt Jumps", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 69.855, 1.750]) linear_extrude(height=1.500) text("Silvêrbêri", size=5.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 63.145, 1.750]) linear_extrude(height=1.500) text("asiski-kwâskwêpayiwina", size=5.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 52.260, 1.750]) linear_extrude(height=2.600) text("ᓯᓪᕓᕒᐯᕒᐃ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 42.500, 1.750]) linear_extrude(height=2.600) text("ᐊᓯᐢᑭ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 32.740, 1.750]) linear_extrude(height=2.600) text("ᑵᐢᑴᐸᔨᐎᓇ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
