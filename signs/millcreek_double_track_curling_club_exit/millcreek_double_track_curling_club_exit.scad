// Auto image-pipeline draft (tools/sign_factory/build_signs.py)
// "Millcreek Double Track - Curling Club Exit"  icon=millcreek_double_track_curling_club_exit_icon.stl
$fn = 36;

module blank_plaque() {
  translate([-45, -82.5, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  translate([0, 6.0, 1.75]) import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/signs/millcreek_double_track_curling_club_exit/millcreek_double_track_curling_club_exit_icon.stl", convexity=10);
}

module lettering() {
  // English (bottom)
  translate([0, -59.960, 1.750]) linear_extrude(height=1.500) text("Millcreek Double", size=7.000, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -68.500, 1.750]) linear_extrude(height=1.500) text("Track - Curling", size=7.000, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -77.040, 1.750]) linear_extrude(height=1.500) text("Club Exit", size=7.000, halign="center", valign="center", font="Raleway:style=Bold");
  // translit (top)
  translate([0, 70.855, 1.750]) linear_extrude(height=1.500) text("Milkrîk nîso-meskanaw", size=5.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 64.145, 1.750]) linear_extrude(height=1.500) text("sîswahikan", size=5.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (overlaid, protruding)
  translate([0, 10.270, 1.750]) linear_extrude(height=3.500) text("ᒥᓪᑯᕒᐃᐠ ᓃᓱ", size=7.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 1.730, 1.750]) linear_extrude(height=3.500) text("ᒣᐢᑲᓇᐤ ᓰᔅᐗᐦᐃᑲᐣ", size=7.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() { blank_plaque(); icon_model(); lettering(); syllabics_text(); }
