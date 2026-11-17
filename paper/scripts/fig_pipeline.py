"""Figure: how a trail name becomes a sign, a web page and an app entry.

A schematic of the repository's tools, drawn from a small hand-written graph so
it stays in step with the prose. Box text names the actual files.
"""
from __future__ import annotations

from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from common import BLUE, FIG, INK, INK2, ORANGE, AQUA, setup_matplotlib

NODES = {
    # key: (x, y, title, detail, kind)
    "trails": (0.6, 3.0, "Trail list", "Trailforks names,\nlength, area", "data"),
    "wb": (2.35, 3.0, "Translation\nWorkbench", "three Cree\ncandidates per trail", "tool"),
    "review1": (4.1, 3.0, "Speaker &\nElder review", "choose, correct,\nor decline a name", "human"),
    "style": (5.85, 3.0, "Style guide +\nicon", "screenprint, HueForge\nor object icon", "tool"),
    "plaque": (7.6, 3.0, "Plaque\ngenerator", "OpenSCAD plaque;\nSTL and 3MF out", "tool"),
    "print": (9.35, 3.0, "Print &\nmount", "colour swaps by layer;\nmounted trailside", "data"),
    "cat": (2.35, 0.9, "catalogue.json", "one record per sign,\nread by everything", "data"),
    "editor": (4.1, 0.9, "Catalogue\neditor", "pages move from draft\nto reviewed to published", "tool"),
    "site": (5.85, 0.9, "Website", "sign pages, map,\nword breakdowns", "out"),
    "app": (7.6, 0.9, "Companion app", "map, routes,\nsign hunt, rides", "out"),
    "db": (9.35, 0.9, "Supabase", "captures, rides,\nKOM board", "data"),
}
EDGES = [("trails", "wb"), ("wb", "review1"), ("review1", "style"), ("style", "plaque"),
         ("plaque", "print"), ("wb", "cat"), ("plaque", "cat"), ("cat", "editor"),
         ("editor", "site"), ("site", "app"), ("app", "db")]
KIND = {"data": ("#f3f2ee", "#b9b8b2"), "tool": ("#e8f0fb", BLUE),
        "human": ("#fdeee7", ORANGE), "out": ("#e5f6ef", AQUA)}
W, H = 1.62, 1.25


def main():
    plt = setup_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    for k, (x, y, t, d, kind) in NODES.items():
        fc, ec = KIND[kind]
        ax.add_patch(FancyBboxPatch((x - W / 2, y - H / 2), W, H,
                                    boxstyle="round,pad=0.02,rounding_size=0.08",
                                    fc=fc, ec=ec, lw=1.1))
        ax.text(x, y + 0.2, t, ha="center", va="center", fontsize=7, weight="bold", color=INK)
        ax.text(x, y - 0.36, d, ha="center", va="center", fontsize=5.1, color=INK2)
    for a, b in EDGES:
        xa, ya = NODES[a][:2]
        xb, yb = NODES[b][:2]
        if ya == yb:
            p, q = (xa + W / 2, ya), (xb - W / 2, yb)
        else:
            p, q = (xa, ya - H / 2) if ya > yb else (xa, ya + H / 2), \
                   (xb, yb + H / 2) if ya > yb else (xb, yb - H / 2)
            if xa != xb:
                p, q = (xa - 0.25, ya - H / 2), (xb + 0.35, yb + H / 2)
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8,
                                     color=INK2, lw=0.8, shrinkA=1, shrinkB=1))
    ax.text(0.0, 3.95, "Making a sign", fontsize=8, weight="bold", color=INK)
    ax.text(0.0, 1.85, "Publishing it", fontsize=8, weight="bold", color=INK)
    for i, (kind, lab) in enumerate([("human", "people decide"), ("tool", "repository tool"),
                                     ("out", "what riders use"), ("data", "data or object")]):
        fc, ec = KIND[kind]
        ax.add_patch(FancyBboxPatch((0.0 + i * 1.55, -0.45), 0.25, 0.18,
                                    boxstyle="round,pad=0.01", fc=fc, ec=ec, lw=1))
        ax.text(0.33 + i * 1.55, -0.36, lab, fontsize=6, va="center", color=INK2)
    ax.set_xlim(-0.2, 10.2)
    ax.set_ylim(-0.6, 4.1)
    ax.axis("off")
    fig.savefig(FIG / "pipeline.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
