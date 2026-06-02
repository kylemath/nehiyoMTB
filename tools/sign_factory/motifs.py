"""
motifs.py — procedural OpenSCAD icon motifs for the sign factory.

Each motif is a function returning a list of "layers":
    {"color": "#rrggbb", "z": <int layer index>, "code": "<2D OpenSCAD>"}

The 2D code draws shapes centred near the origin within roughly a
[-45, 45] box (≈ 90 units wide). The builder scales this to the desired
icon width, extrudes each layer to base + z*step millimetres (so different
"z" values print as different filament-swap heights), and colours it for the
preview render.

These are intentionally simple, flat, closed shapes — a *draft* gestural icon
that is trivially extrudable. Swap in a real generated image via the Icon
Extruder when you want higher fidelity.
"""
import math
import re

BLACK = "#1c1c1c"
RED = "#c0392b"
WHITE = "#f2f2f2"
YELLOW = "#e0b04a"
BLUE = "#2c6fb0"
GREEN = "#3a8a3a"
ORANGE = "#d3792b"
GREY = "#8a8a8a"
BROWN = "#7a5230"


def _poly(points):
    pts = ",".join("[%.2f,%.2f]" % (x, y) for x, y in points)
    return "polygon(points=[%s]);" % pts


def _star(cx, cy, ro, ri, n=5, rot=-90):
    pts = []
    for i in range(2 * n):
        r = ro if i % 2 == 0 else ri
        a = math.radians(rot + i * 180.0 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return _poly(pts)


def _wave_band(y, amp, thick, span=44, steps=24):
    top, bot = [], []
    for i in range(steps + 1):
        x = -span + 2 * span * i / steps
        yy = y + amp * math.sin(i / steps * 2 * math.pi * 1.5)
        top.append((x, yy + thick / 2))
        bot.append((x, yy - thick / 2))
    return _poly(top + bot[::-1])


# --------------------------------------------------------------------------- #
def m_heart():
    code = ("union(){translate([-16,9])circle(17);translate([16,9])circle(17);"
            "polygon([[-31,8],[31,8],[0,-34]]);}")
    return [{"color": RED, "z": 1, "code": code}]


def m_crescent():
    code = "difference(){circle(36);translate([15,7])circle(32);}"
    return [{"color": YELLOW, "z": 1, "code": code}]


def m_star():
    return [{"color": YELLOW, "z": 1, "code": _star(0, 0, 40, 17)}]


def m_burst():
    rings = "".join("difference(){circle(%d);circle(%d);}" % (r, r - 5)
                    for r in (40, 28, 16))
    return [{"color": RED, "z": 1, "code": "union(){%scircle(6);}" % rings}]


def m_skull():
    code = ("difference(){union(){circle(30);translate([0,-26])"
            "polygon([[-16,0],[16,0],[12,-16],[-12,-16]]);}"
            "translate([-12,4])circle(8);translate([12,4])circle(8);"
            "translate([0,-10])polygon([[-4,0],[4,0],[0,-8]]);}")
    return [{"color": WHITE, "z": 1, "code": code}]


def m_tooth():
    code = ("union(){translate([0,8])offset(6)square([34,24],center=true);"
            "translate([-12,-26])polygon([[-7,28],[7,28],[3,-6],[-3,-6]]);"
            "translate([12,-26])polygon([[-7,28],[7,28],[3,-6],[-3,-6]]);}")
    return [{"color": WHITE, "z": 1, "code": code}]


def m_dice():
    pips = "".join("translate([%d,%d])circle(4);" % (x, y)
                   for x, y in [(-14, 14), (14, 14), (-14, -14), (14, -14), (0, 0)])
    base = "offset(7)square([54,54],center=true);"
    return [{"color": WHITE, "z": 1, "code": base},
            {"color": BLACK, "z": 2, "code": pips}]


def m_bird():
    # gestural flying bird (raven): body + swept wings + beak + tail
    code = ("union(){translate([-2,2])scale([1.5,1])circle(13);"
            "polygon([[6,6],[40,26],[20,4]]);"
            "polygon([[-8,4],[-42,22],[-20,2]]);"
            "polygon([[8,2],[26,-2],[10,-8]]);"
            "polygon([[6,2],[20,2],[12,12]]);}")
    return [{"color": BLACK, "z": 1, "code": code}]


def m_owl():
    code = ("union(){scale([1.05,1.2])circle(30);"
            "polygon([[-26,18],[-12,30],[-18,12]]);"
            "polygon([[26,18],[12,30],[18,12]]);}")
    eyes = ("union(){translate([-13,6])circle(9);translate([13,6])circle(9);}")
    beak = "polygon([[-4,2],[4,2],[0,-8]]);"
    return [{"color": BROWN, "z": 1, "code": code},
            {"color": WHITE, "z": 2, "code": eyes},
            {"color": YELLOW, "z": 2, "code": beak}]


def m_blade():
    code = ("union(){polygon([[-36,-6],[24,-6],[36,2],[24,10],[-36,10]]);"
            "translate([-44,2])square([18,18],center=true);}")
    return [{"color": GREY, "z": 1, "code":
             "polygon([[-36,-6],[24,-6],[36,2],[24,10],[-36,10]]);"},
            {"color": BROWN, "z": 1, "code":
             "translate([-40,2])square([16,16],center=true);"}]


def m_axe():
    handle = "rotate(28)translate([0,-6])square([10,76],center=true);"
    head = ("translate([6,26])difference(){polygon([[-22,-16],[22,-16],"
            "[14,18],[-14,18]]);translate([0,30])circle(20);}")
    return [{"color": BROWN, "z": 1, "code": handle},
            {"color": GREY, "z": 2, "code": head}]


def m_gun():
    code = ("union(){translate([2,8])square([60,16],center=true);"
            "translate([-18,-10])rotate(18)square([16,30],center=true);"
            "translate([28,8])circle(4);}")
    return [{"color": BLACK, "z": 1, "code": code}]


def m_droplet():
    code = "union(){translate([0,-8])circle(22);polygon([[-16,2],[16,2],[0,36]]);}"
    return [{"color": BLUE, "z": 1, "code": code}]


def m_wave():
    return [{"color": BLUE, "z": 1, "code":
             "union(){%s%s}" % (_wave_band(6, 7, 9), _wave_band(-16, 7, 9))}]


def m_mountain():
    code = ("union(){polygon([[-44,-26],[-6,34],[30,-26]]);"
            "polygon([[2,-26],[34,28],[46,-26]]);}")
    cap = "polygon([[-16,16],[-6,34],[4,16]]);"
    return [{"color": GREY, "z": 1, "code": code},
            {"color": WHITE, "z": 2, "code": cap}]


def m_pine():
    code = ("union(){translate([-4,-34])square([8,16],center=true);"
            "polygon([[-22,-22],[22,-22],[0,4]]);"
            "polygon([[-18,-2],[18,-2],[0,20]]);"
            "polygon([[-13,16],[13,16],[0,36]]);}")
    return [{"color": GREEN, "z": 1, "code": code}]


def m_tree():
    code = ("union(){translate([0,-26])square([10,28],center=true);"
            "translate([0,12])circle(26);}")
    return [{"color": GREEN, "z": 1, "code": code}]


def m_paw():
    toes = "".join("translate([%d,%d])circle(8);" % (x, y)
                   for x, y in [(-20, 16), (-7, 24), (7, 24), (20, 16)])
    return [{"color": BLACK, "z": 1, "code":
             "union(){translate([0,-12])scale([1.2,1])circle(20);%s}" % toes}]


def m_fox():
    code = ("union(){polygon([[-30,18],[30,18],[0,-34]]);"
            "polygon([[-30,18],[-14,40],[-6,20]]);"
            "polygon([[30,18],[14,40],[6,20]]);}")
    snout = "polygon([[-8,-16],[8,-16],[0,-36]]);"
    return [{"color": ORANGE, "z": 1, "code": code},
            {"color": WHITE, "z": 2, "code": snout}]


def m_antlers():
    head = "translate([0,-18])scale([1,1.1])circle(20);"
    antl = ("union(){translate([-18,16])rotate(20)scale([1.6,1])polygon("
            "[[-16,-4],[16,-4],[10,16],[-10,16]]);"
            "translate([18,16])rotate(-20)scale([1.6,1])polygon("
            "[[-16,-4],[16,-4],[10,16],[-10,16]]);}")
    return [{"color": BROWN, "z": 1, "code": head},
            {"color": BROWN, "z": 2, "code": antl}]


def m_horse():
    # stylised chess-knight horse head, facing right
    pts = [(-22, -36), (-22, 6), (-30, 16), (-24, 30), (-14, 26), (-12, 38),
           (-4, 30), (-2, 42), (6, 31), (14, 24), (10, 14), (22, 9),
           (27, -6), (22, -16), (29, -23), (14, -20), (12, -36)]
    return [{"color": BROWN, "z": 1, "code": _poly(pts)}]


def m_snake():
    body = _wave_band(0, 16, 12, span=40, steps=28)
    head = "translate([40,0])circle(9);"
    tongue = "translate([50,0])polygon([[0,-3],[10,0],[0,3]]);"
    return [{"color": GREEN, "z": 1, "code": "union(){%s%s}" % (body, head)},
            {"color": RED, "z": 2, "code": tongue}]


def m_spiral():
    rings = "".join("difference(){circle(%d);circle(%d);}" % (r, r - 4)
                    for r in (40, 31, 22, 13))
    return [{"color": RED, "z": 1, "code": "union(){%scircle(5);}" % rings}]


def m_trophy():
    code = ("union(){polygon([[-22,30],[22,30],[14,2],[-14,2]]);"
            "translate([0,-8])square([10,16],center=true);"
            "translate([0,-22])square([30,8],center=true);"
            "difference(){translate([-26,20])circle(12);translate([-26,20])circle(7);}"
            "difference(){translate([26,20])circle(12);translate([26,20])circle(7);}}")
    return [{"color": YELLOW, "z": 1, "code": code}]


def m_gradcap():
    cap = "rotate(45)square([40,40],center=true);"
    band = "translate([0,-12])square([26,16],center=true);"
    tassel = ("union(){translate([26,2])square([3,24],center=false);"
              "translate([27,26])circle(5);}")
    return [{"color": BLACK, "z": 1, "code": "union(){%s%s}" % (cap, band)},
            {"color": YELLOW, "z": 2, "code": tassel}]


def m_cowboyhat():
    code = ("union(){translate([0,-8])scale([1.6,0.5])circle(34);"
            "translate([0,6])scale([1,1.3])circle(20);}")
    return [{"color": BROWN, "z": 1, "code": code}]


def m_flame():
    code = ("polygon([[0,40],[16,8],[10,-6],[16,-22],[0,-30],[-16,-22],"
            "[-10,-6],[-16,8]]);")
    inner = "translate([0,-8])polygon([[0,18],[8,2],[0,-14],[-8,2]]);"
    return [{"color": ORANGE, "z": 1, "code": code},
            {"color": YELLOW, "z": 2, "code": inner}]


def m_clover():
    leaves = "".join("translate([%d,%d])circle(13);" % (x, y)
                     for x, y in [(0, 16), (16, 0), (0, -16), (-16, 0)])
    stem = "translate([0,-30])square([4,20],center=true);"
    return [{"color": GREEN, "z": 1, "code": "union(){%s%s}" % (leaves, stem)}]


def m_bridge():
    deck = "translate([0,6])square([84,8],center=true);"
    arch = "difference(){translate([0,2])scale([1.5,1])circle(28);translate([0,-10])scale([1.5,1])circle(24);translate([0,-30])square([90,40],center=true);}"
    return [{"color": GREY, "z": 1, "code": "union(){%s%s}" % (deck, arch)}]


def m_scooter():
    code = ("union(){difference(){translate([-22,-16])circle(13);translate([-22,-16])circle(7);}"
            "difference(){translate([22,-16])circle(13);translate([22,-16])circle(7);}"
            "polygon([[-22,-16],[18,18],[26,18],[24,12],[-18,-20]]);"
            "translate([22,22])square([20,6],center=true);}")
    return [{"color": BLACK, "z": 1, "code": code}]


def m_anchor_boat():
    hull = "polygon([[-40,4],[40,4],[28,-20],[-28,-20]]);"
    cabin = "translate([0,18])square([40,24],center=true);"
    wheel = "difference(){translate([34,-6])circle(16);translate([34,-6])circle(9);}"
    return [{"color": WHITE, "z": 1, "code": "union(){%s%s}" % (hull, cabin)},
            {"color": RED, "z": 2, "code": wheel}]


def m_birdhouse():
    box = "translate([0,-6])square([40,40],center=true);"
    roof = "polygon([[-28,14],[28,14],[0,40]]);"
    hole = "translate([0,0])circle(9);"
    perch = "translate([0,-18])square([4,16],center=true);"
    return [{"color": BROWN, "z": 1, "code": "union(){%s%s}" % (box, roof)},
            {"color": BLACK, "z": 2, "code": "union(){%s%s}" % (hole, perch)}]


def m_keyhole():
    code = ("union(){circle(16);translate([0,-22])polygon([[-7,22],[7,22],[11,-14],[-11,-14]]);}")
    return [{"color": BLACK, "z": 1, "code": code}]


def m_horseshoe():
    code = "difference(){circle(34);circle(22);translate([0,-30])square([60,30],center=true);}"
    return [{"color": GREY, "z": 1, "code": code}]


def m_sun_mountain():  # generic fallback
    sun = "translate([0,24])circle(14);"
    rays = "".join("rotate(%d)translate([0,42])square([3,10],center=true);" % a
                   for a in range(0, 360, 45))
    mts = "polygon([[-46,-30],[-10,18],[10,-6],[28,22],[46,-30]]);"
    return [{"color": GREEN, "z": 1, "code": mts},
            {"color": YELLOW, "z": 2, "code": "union(){%s%s}" % (sun, rays)}]


# --------------------------------------------------------------------------- #
MOTIFS = {
    "heart": m_heart, "crescent": m_crescent, "star": m_star, "burst": m_burst,
    "skull": m_skull, "tooth": m_tooth, "dice": m_dice, "bird": m_bird,
    "owl": m_owl, "blade": m_blade, "axe": m_axe, "gun": m_gun,
    "droplet": m_droplet, "wave": m_wave, "mountain": m_mountain, "pine": m_pine,
    "tree": m_tree, "paw": m_paw, "fox": m_fox, "antlers": m_antlers,
    "horse": m_horse, "snake": m_snake, "spiral": m_spiral, "trophy": m_trophy,
    "gradcap": m_gradcap, "cowboyhat": m_cowboyhat, "flame": m_flame,
    "clover": m_clover, "bridge": m_bridge, "scooter": m_scooter,
    "boat": m_anchor_boat, "birdhouse": m_birdhouse, "keyhole": m_keyhole,
    "horseshoe": m_horseshoe, "sun_mountain": m_sun_mountain,
}

# keyword -> motif, evaluated in order against "<en> <concept> <subject>".
# Matching is on whole words (so "wing" does NOT match inside "flowing").
KEYWORD_RULES = [
    (("heart", "love", "lov", "lovers", "lane"), "heart"),
    (("birdhouse",), "birdhouse"),
    (("crescent", "moon", "moonraker", "lunar"), "crescent"),
    (("owl", "hoot", "holler"), "owl"),
    (("raven", "crow", "bird", "orca", "whale", "willy"), "bird"),
    (("fox", "foxhole"), "fox"),
    (("moose", "antler", "elk", "mooseknuckle", "moosestang"), "antlers"),
    (("horse", "mustang", "stang", "pony"), "horseshoe"),
    (("giddy", "cowboy", "rodeo"), "cowboyhat"),
    (("snake", "rattle", "rattlesnake", "serpent", "dragon", "dragons"), "snake"),
    (("skull", "killer", "death", "rip", "memorial", "mcaloon", "deliverance"), "skull"),
    (("tooth", "canal"), "tooth"),
    (("dice", "risky", "gamble"), "dice"),
    (("machete", "scalpel", "switchblade", "blade", "slicer", "knife", "axe-no"), "blade"),
    (("axe",), "axe"),
    (("gun", "shooter", "raygun", "shot", "blaster", "revolver", "kessel", "falcon", "spaceship"), "gun"),
    (("flame", "fire", "fireman", "purgatory", "rocket"), "flame"),
    (("burst", "emp", "earthshaker", "blast", "shaker", "shockwave", "pulse"), "burst"),
    (("droplet", "dollar", "money"), "droplet"),
    (("flow", "wave", "creek", "river", "water", "riverside", "780-flow"), "wave"),
    (("trophy", "cup", "champion", "championship"), "trophy"),
    (("grad", "edukation", "uofa", "university", "graduation", "mortarboard"), "gradcap"),
    (("corkscrew", "spiral", "coil", "slinky", "hyperloop", "logarythmic"), "spiral"),
    (("clover", "cloverdale", "vegan", "leaf", "shamrock"), "clover"),
    (("bridge", "lrt"), "bridge"),
    (("scooter", "skoot", "bike", "imba", "jump", "bobsled", "biker"), "scooter"),
    (("boat", "queen", "riverboat", "ferry", "paddleboat", "paddlewheel"), "boat"),
    (("secret", "keyhole", "key", "trap", "shush"), "keyhole"),
    (("horseshoe",), "horseshoe"),
    (("paw", "monkey", "wolf", "camel", "turtle", "hulk", "wrestler"), "paw"),
    (("trophy-no",), "trophy"),
    (("gnome", "willow", "tree"), "tree"),
    (("pine", "forest", "trees", "meadow", "frolic", "loop"), "pine"),
    (("mountain", "hill", "steep", "rip", "descent", "downhill", "ravine",
      "skyline", "vista", "breathless", "coast", "coastline", "klondike",
      "valley", "powder", "humps", "dune"), "mountain"),
    (("star", "knight", "ren", "selkirk", "yoda", "jedi", "wonder", "hero",
      "messier", "gretzky", "hockey"), "star"),
]

_COMPILED = [(re.compile(r"\b(" + "|".join(re.escape(k) for k in keys) + r")\b"), m)
             for keys, m in KEYWORD_RULES]


def pick_motif(en, concept, subject):
    hay = (" ".join([en or "", concept or "", subject or ""])).lower()
    for rx, motif in _COMPILED:
        if rx.search(hay):
            return motif
    return "sun_mountain"


def render_motif(name):
    fn = MOTIFS.get(name, MOTIFS["sun_mountain"])
    return fn()
