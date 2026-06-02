// Auto-generated draft by tools/sign_factory/build_signs.py
// "Belgravia Dirt Jumps - Drop In" / Belgrêviya asiski-kwâskwêpayiwin pîhcipayi / ᐯᓪᑯᕒᐁᐲᔭ ᐊᓯᐢᑭ ᑵᐢᑴᐸᔨᐎᐣ ᐲᐦᑐᐺᐱᓇ  [icon: scooter]
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
  translate([0, -63.620, 1.750]) linear_extrude(height=1.500) text("Belgravia Dirt", size=8.000, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -73.380, 1.750]) linear_extrude(height=1.500) text("Jumps - Drop In", size=8.000, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 71.380, 1.750]) linear_extrude(height=1.500) text("Belgrêviya", size=4.000, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 66.500, 1.750]) linear_extrude(height=1.500) text("asiski-kwâskwêpayiwin", size=4.000, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 61.620, 1.750]) linear_extrude(height=1.500) text("pîhcipayi", size=4.000, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 51.650, 1.750]) linear_extrude(height=2.600) text("ᐯᓪᑯᕒᐁᐲᔭ ᐊᓯᐢᑭ", size=7.500, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 42.500, 1.750]) linear_extrude(height=2.600) text("ᑵᐢᑴᐸᔨᐎᐣ", size=7.500, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 33.350, 1.750]) linear_extrude(height=2.600) text("ᐲᐦᑐᐺᐱᓇ", size=7.500, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
