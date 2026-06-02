// Auto-generated draft by tools/sign_factory/build_signs.py
// "Riverside Dr Descent" / sîpiy-cîki meskanaw nîhtâciwin / ᓰᐱᐃ ᒋᑭ ᒣᐢᑲᓇᐤ ᓂᐦᑖᒋᐎᐣ  [icon: wave]
$fn = 40;

module blank_plaque() {
  translate([-45.000, -82.500, 0])
    scale([0.004994, 0.004832, 0.003793])
      translate([-10458.010, -1925.350, -522.360])
        import("/Users/kylemathewson/Coding/HARDWARE/nehiyoMTB/blanks/blank_plaque_thinner.stl", convexity=10);
}

module icon_model() {
  color("#2c6fb0") translate([0, -10.000, 1.750]) linear_extrude(height=1.200) scale([0.6304,0.6304,1]) { union(){polygon(points=[[-44.00,10.50],[-40.33,13.18],[-36.67,15.45],[-33.00,16.97],[-29.33,17.50],[-25.67,16.97],[-22.00,15.45],[-18.33,13.18],[-14.67,10.50],[-11.00,7.82],[-7.33,5.55],[-3.67,4.03],[0.00,3.50],[3.67,4.03],[7.33,5.55],[11.00,7.82],[14.67,10.50],[18.33,13.18],[22.00,15.45],[25.67,16.97],[29.33,17.50],[33.00,16.97],[36.67,15.45],[40.33,13.18],[44.00,10.50],[44.00,1.50],[40.33,4.18],[36.67,6.45],[33.00,7.97],[29.33,8.50],[25.67,7.97],[22.00,6.45],[18.33,4.18],[14.67,1.50],[11.00,-1.18],[7.33,-3.45],[3.67,-4.97],[0.00,-5.50],[-3.67,-4.97],[-7.33,-3.45],[-11.00,-1.18],[-14.67,1.50],[-18.33,4.18],[-22.00,6.45],[-25.67,7.97],[-29.33,8.50],[-33.00,7.97],[-36.67,6.45],[-40.33,4.18],[-44.00,1.50]]);polygon(points=[[-44.00,-11.50],[-40.33,-8.82],[-36.67,-6.55],[-33.00,-5.03],[-29.33,-4.50],[-25.67,-5.03],[-22.00,-6.55],[-18.33,-8.82],[-14.67,-11.50],[-11.00,-14.18],[-7.33,-16.45],[-3.67,-17.97],[0.00,-18.50],[3.67,-17.97],[7.33,-16.45],[11.00,-14.18],[14.67,-11.50],[18.33,-8.82],[22.00,-6.55],[25.67,-5.03],[29.33,-4.50],[33.00,-5.03],[36.67,-6.55],[40.33,-8.82],[44.00,-11.50],[44.00,-20.50],[40.33,-17.82],[36.67,-15.55],[33.00,-14.03],[29.33,-13.50],[25.67,-14.03],[22.00,-15.55],[18.33,-17.82],[14.67,-20.50],[11.00,-23.18],[7.33,-25.45],[3.67,-26.97],[0.00,-27.50],[-3.67,-26.97],[-7.33,-25.45],[-11.00,-23.18],[-14.67,-20.50],[-18.33,-17.82],[-22.00,-15.55],[-25.67,-14.03],[-29.33,-13.50],[-33.00,-14.03],[-36.67,-15.55],[-40.33,-17.82],[-44.00,-20.50]]);} }
}

module lettering() {
  // English (bottom)
  translate([0, -62.095, 1.750]) linear_extrude(height=1.500) text("Riverside", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, -74.905, 1.750]) linear_extrude(height=1.500) text("Dr Descent", size=10.500, halign="center", valign="center", font="Raleway:style=Bold");
  // transliteration (top)
  translate([0, 70.160, 1.750]) linear_extrude(height=1.500) text("sîpiy-cîki meskanaw", size=6.000, halign="center", valign="center", font="Raleway:style=Bold");
  translate([0, 62.840, 1.750]) linear_extrude(height=1.500) text("nîhtâciwin", size=6.000, halign="center", valign="center", font="Raleway:style=Bold");
}

module syllabics_text() {
  // syllabics (protruding)
  translate([0, 52.260, 1.750]) linear_extrude(height=2.600) text("ᓰᐱᐃ ᒋᑭ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 42.500, 1.750]) linear_extrude(height=2.600) text("ᒣᐢᑲᓇᐤ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
  translate([0, 32.740, 1.750]) linear_extrude(height=2.600) text("ᓂᐦᑖᒋᐎᐣ", size=8.000, halign="center", valign="center", font="Euphemia UCAS:style=Bold");
}

union() {
  color("#d9d3c4") blank_plaque();
  color("#2a2a2a") lettering();
  icon_model();
  color("#b23b3b") syllabics_text();
}
