// Nehiyo MTB Trail Sign Generator
// Customizable trail sign with English, transliteration, and Cree syllabics

// ===== CUSTOMIZATION PARAMETERS =====
// Text content
english_name = "I See You";           // English translation at bottom
transliteration = "kiwâpamitin";        // Cree transliteration at top  
cree_syllabics = "ᑭᐚᐸᒥᑎᐣ";            // Cree syllabics (paste from text editor)

// Text sizing and positioning
english_size = 18;                    // Size of English text at bottom
transliteration_size = 15;            // Size of transliteration at top
syllabics_size = 21;                  // Size of Cree syllabics
syllabics_boldness = 0.6;             // How much to thicken syllabics (0 = normal, 0.5-1.0 = bolder)
text_depth = 3;                     // How deep to emboss/deboss text
syllabics_depth = 5;                  // How deep to emboss/deboss syllabics

// Sign dimensions (adjust based on your blank_plaque_thinner.stl)
sign_width = 111;                     // Width of sign
sign_height = 210;                    // Height of sign  
sign_thickness = 3;                   // Thickness of sign
corner_radius = 8;                    // Rounded corner radius

// Text positioning (from bottom of sign)
english_y_offset = 12;                // Distance from bottom edge
syllabics_y_offset = 160;              // Distance from bottom edge
transliteration_y_offset = 193;       // Distance from bottom edge

top_hole_offset = 32;
bottom_hole_offset = 30;

// HueForge insert settings
hueforge_clearance = 0.05;            // Clearance around insert edge (mm)

// ===== MODULES =====
module hueforge_cutout() {
    // cutout a 100 x 100 square from the center between the two holes a few layers think to fit the hueforge logo
    translate([0, -13, 2]) {
        linear_extrude(height = 10) {
            square([100 + 2*hueforge_clearance, 100 + 2*hueforge_clearance], center = true);
        }
    }
}

module rounded_rectangle(width, height, thickness, radius) {
    linear_extrude(height = thickness) {
        offset(r = radius) {
            square([width - 2*radius, height - 2*radius], center = true);
        }
    }
}

module embossed_text(text_string, size, depth, x_pos = 0, y_pos = 0, use_unicode_font = false, boldness = 0) {
    translate([x_pos, y_pos, sign_thickness]) {
        linear_extrude(height = depth) {
            offset(r = boldness) {
                if (use_unicode_font) {
                    // Try multiple fonts that support Cree syllabics
                    // Uncomment the one that works best on your system:
                    
                    // Option 1: Arial Unicode MS (most common)
                    // text(text_string, size = size, halign = "center", valign = "center", 
                    //      font = "Arial Unicode MS:style=Regular");
                    
                    // Option 2: Mac-specific Cree font (uncomment if on Mac)
                    text(text_string, size = size, halign = "center", valign = "center", 
                         font = "Euphemia UCAS:style=Regular");
                    
                    // Option 3: Other Unicode fonts (try these if above don't work)
                    // text(text_string, size = size, halign = "center", valign = "center", 
                    //      font = "DejaVu Sans:style=Book");
                    // text(text_string, size = size, halign = "center", valign = "center", 
                    //      font = "Segoe UI:style=Regular");
                    // text(text_string, size = size, halign = "center", valign = "center", 
                    //      font = "Noto Sans:style=Regular");
                } else {
                    text(text_string, size = size, halign = "center", valign = "center", 
                         font = "Raleway:style=Bold");
                }
            }
        }
    }
}

module debossed_text(text_string, size, depth, x_pos = 0, y_pos = 0, use_unicode_font = false, boldness = 0) {
    translate([x_pos, y_pos, -0.1]) {
        linear_extrude(height = depth + 0.2) {
            offset(r = boldness) {
                if (use_unicode_font) {
                    // Try multiple fonts that support Cree syllabics
                    // Uncomment the one that works best on your system:
                    
                    // Option 1: Arial Unicode MS (most common)
                    text(text_string, size = size, halign = "center", valign = "center", 
                         font = "Arial Unicode MS:style=Bold");
                    
                    // Option 2: Mac-specific Cree font (uncomment if on Mac)
                    // text(text_string, size = size, halign = "center", valign = "center", 
                    //      font = "Euphemia UCAS:style=Regular");
                    
                    // Option 3: Other Unicode fonts (try these if above don't work)
                    // text(text_string, size = size, halign = "center", valign = "center", 
                    //      font = "DejaVu Sans:style=Book");
                    // text(text_string, size = size, halign = "center", valign = "center", 
                    //      font = "Segoe UI:style=Regular");
                    // text(text_string, size = size, halign = "center", valign = "center", 
                    //      font = "Noto Sans:style=Regular");
                } else {
                    text(text_string, size = size, halign = "center", valign = "center", 
                         font = "Raleway:style=Bold");
                }
            }
        }
    }
}

// ===== MAIN SIGN ASSEMBLY =====

module trail_sign() {
    difference() {
        union() {
            // Base sign shape
            difference() {
                translate([0, 0, 0]) {
                    rounded_rectangle(sign_width, sign_height, sign_thickness, corner_radius);
                }
                
                // Mounting holes (2 holes, positioned like in the reference image)
                translate([0, sign_height/2 - top_hole_offset, -0.1]) {
                    cylinder(h = sign_thickness + 0.2, d = 5, $fn = 20);
                }
                translate([0, -sign_height/2 + bottom_hole_offset, -0.1]) {
                    cylinder(h = sign_thickness + 0.2, d = 5, $fn = 20);
                }
            }
            
            // Embossed text (raised from sign surface)
            embossed_text(english_name, english_size, text_depth, 
                        0, -sign_height/2 + english_y_offset, false);
            
            embossed_text(transliteration, transliteration_size, text_depth, 
                        0, -sign_height/2 + transliteration_y_offset, false);
            
            embossed_text(cree_syllabics, syllabics_size, syllabics_depth,
                        0, -sign_height/2 + syllabics_y_offset, true, syllabics_boldness);
        }

        hueforge_cutout();
    }
}

// ===== RENDER =====
trail_sign();

// ===== INSTRUCTIONS =====
// 1. Customize the text variables at the top of this file
// 2. For Cree syllabics, copy and paste from your text editor
// 3. Adjust text sizes and positions as needed
// 4. EYES SETUP: The maskihkiwiyiniw eyes are automatically imported and positioned
//    - Adjust eyes_y_offset, eyes_scale, and eyes_z_offset if needed
//    - If you want to cut out just the eyes region from the STL, uncomment the intersection() code in maskihkiwiyiniw_eyes()
// 5. UNICODE FIX: If syllabics show as boxes/shapes, try different fonts:
//    - Uncomment different font options in the embossed_text/debossed_text modules
//    - On Mac: try "Euphemia UCAS" (built-in Cree font)
//    - On Windows: try "Arial Unicode MS" or "Segoe UI"
//    - Install "Noto Sans" from Google Fonts if needed
// 6. Export as STL for 3D printing
// 7. Print with the text side facing up for best quality

echo("=== Trail Sign Generator ===");
echo(str("English: ", english_name));
echo(str("Transliteration: ", transliteration)); 
echo(str("Cree Syllabics: ", cree_syllabics));
echo(str("Sign dimensions: ", sign_width, "x", sign_height, "x", sign_thickness, "mm"));
