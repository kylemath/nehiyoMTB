"""Figures built from the project's own images.

signs_wall.jpg       the photograph of the finished signs (allSigns.jpg), resized.
generator_stages.pdf three trails followed through the sign factory: the
                     generated icon, the composed sign preview, and the 3D
                     assembly render, one row per sign style.
drafts_grid.pdf      a sample of composed previews for trails that do not have
                     a physical sign yet.
Also writes generator statistics used in the prose.
"""
from __future__ import annotations

from collections import Counter

from PIL import Image, ImageChops

from common import FIG, INK2, REPO, DOCS, drafts_manifest, models, setup_matplotlib, write_macros


def trim(im: Image.Image, pad: int = 8) -> Image.Image:
    rgb = im.convert("RGB")
    bg = Image.new("RGB", rgb.size, rgb.getpixel((2, 2)))
    diff = ImageChops.difference(rgb, bg).convert("L").point(lambda v: 255 if v > 18 else 0)
    box = diff.getbbox()
    if not box:
        return rgb
    l, t, r, b = box
    return rgb.crop((max(0, l - pad), max(0, t - pad), min(rgb.width, r + pad), min(rgb.height, b + pad)))


def main():
    plt = setup_matplotlib()

    # ------------------------------------------------------------ wall photo
    im = Image.open(REPO / "allSigns.jpg").convert("RGB")
    im.thumbnail((2400, 2400))
    im.save(FIG / "signs_wall.jpg", quality=86)

    man = drafts_manifest()

    # ------------------------------------------------------- generator stages
    examples = [("Cowboy", "Screenprint style"), ("West Coast Trail", "HueForge (tonal) style"),
                ("Battle Axe", "Object style")]
    fig, axes = plt.subplots(3, 3, figsize=(7.0, 6.6),
                             gridspec_kw={"wspace": 0.05, "hspace": 0.18})
    for r, (name, style) in enumerate(examples):
        e = man[name]
        paths = [DOCS / e["icon"], DOCS / e["png"], REPO / e["assembly_png"]]
        for c, p in enumerate(paths):
            ax = axes[r][c]
            ax.axis("off")
            if p.exists():
                ax.imshow(trim(Image.open(p)))
            if r == 0:
                ax.set_title(["1. Generated icon", "2. Composed sign preview",
                              "3. Assembled print model"][c], fontsize=8, loc="center")
        axes[r][0].text(-0.06, 0.5, f"{name}\n({style})", transform=axes[r][0].transAxes,
                        rotation=90, ha="right", va="center", fontsize=7.5, color=INK2)
    fig.savefig(FIG / "generator_stages.pdf", dpi=200)
    plt.close(fig)

    # ------------------------------------------------------------ drafts grid
    draft_names = [m["englishName"] for m in models() if m.get("status") == "draft"]
    def portrait(n):
        p = DOCS / man[n]["png"]
        if not p.exists():
            return False
        w, h = Image.open(p).size
        return h > w
    pick = [n for n in draft_names if n in man and portrait(n)][:12]
    if len(pick) < 12:
        pick += [k for k in sorted(man) if k not in pick and portrait(k)][: 12 - len(pick)]
    fig, axes = plt.subplots(2, 6, figsize=(7.0, 3.3), gridspec_kw={"wspace": 0.04, "hspace": 0.02})
    for ax, name in zip(axes.flat, pick):
        ax.axis("off")
        p = DOCS / man[name]["png"]
        if p.exists():
            ax.imshow(Image.open(p).convert("RGB"))
    fig.savefig(FIG / "drafts_grid.pdf", dpi=220)
    plt.close(fig)

    # ------------------------------------------------------------ statistics
    types = Counter(v.get("type") for v in man.values())
    ncol = Counter(len((v.get("components") or {}).get("colors") or []) for v in man.values())
    total = sum(ncol.values())
    median = sorted(n for n, k in ncol.items() for _ in range(k))[total // 2]
    write_macros("generator", {
        "genDrafts": len(man),
        "genScreenprint": types.get("screenprint", 0),
        "genHueforge": types.get("hueforge", 0),
        "genObject": types.get("object", 0),
        "genMedianColours": median,
        "genMaxColours": max(ncol),
        "genIcons": len(list((DOCS / "sign-drafts" / "icons").glob("*.png"))),
    })
    print("gallery:", types, ncol)


if __name__ == "__main__":
    main()
