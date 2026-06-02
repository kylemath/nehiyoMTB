// Auto-generated draft by tools/sign_factory/build_signs.py
// "Rattlesnake" / sîsîkwan-kinêpik / ᓯᓯᑲᐤ ᑭᓀᐱᐠ  [icon: snake]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#3a8a3a") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { union(){polygon(points=[[-40.00,6.00],[-37.14,11.28],[-34.29,15.98],[-31.43,19.55],[-28.57,21.60],[-25.71,21.90],[-22.86,20.42],[-20.00,17.31],[-17.14,12.94],[-14.29,7.79],[-11.43,2.44],[-8.57,-2.51],[-5.71,-6.51],[-2.86,-9.10],[0.00,-10.00],[2.86,-9.10],[5.71,-6.51],[8.57,-2.51],[11.43,2.44],[14.29,7.79],[17.14,12.94],[20.00,17.31],[22.86,20.42],[25.71,21.90],[28.57,21.60],[31.43,19.55],[34.29,15.98],[37.14,11.28],[40.00,6.00],[40.00,-6.00],[37.14,-0.72],[34.29,3.98],[31.43,7.55],[28.57,9.60],[25.71,9.90],[22.86,8.42],[20.00,5.31],[17.14,0.94],[14.29,-4.21],[11.43,-9.56],[8.57,-14.51],[5.71,-18.51],[2.86,-21.10],[0.00,-22.00],[-2.86,-21.10],[-5.71,-18.51],[-8.57,-14.51],[-11.43,-9.56],[-14.29,-4.21],[-17.14,0.94],[-20.00,5.31],[-22.86,8.42],[-25.71,9.90],[-28.57,9.60],[-31.43,7.55],[-34.29,3.98],[-37.14,-0.72],[-40.00,-6.00]]);translate([40,0])circle(9);} }
  color("#c0392b") translate([0, -10.000, 1.750]) linear_extrude(height=1.800) scale([0.6304,0.6304,1]) { translate([50,0])polygon([[0,-3],[10,0],[0,3]]); }
}

module lettering() {
  // English (bottom)
  translate([0, -68.500, 1.750]) linear_extrude(height=1.500) text("Rattlesnake", size=11.000, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 66.500, 1.750]) linear_extrude(height=1.500) text("sîsîkwan-kinêpik", size=7.500, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 49.820, 1.750]) linear_extrude(height=2.600) text("ᓯᓯᑲᐤ", size=12.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 35.180, 1.750]) linear_extrude(height=2.600) text("ᑭᓀᐱᐠ", size=12.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
