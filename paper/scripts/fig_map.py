"""Figure: where the signs are, and what the app's route builder does with them.

map.pdf      every trail in docs/catalogue.json drawn from its GPX track
             (finished signs vs. draft sign pages), numbered by sign number.
routing.pdf  the companion app's cheapest-insertion route builder
             (mobile/src/lib/routing.ts), re-implemented here line for line,
             run on the same trails for three detour budgets.

No basemap tiles are fetched, so the figure is reproducible offline.
"""
from __future__ import annotations

import math

from common import (BLUE, FIG, INK, INK2, MUTED, ORANGE, AQUA, is_built, models,
                    setup_matplotlib, write_macros)

R = 6371000.0


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def path_len(pts):
    return sum(hav(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def trails():
    out = []
    for m in models():
        tf = m.get("pageContent", {}).get("trailforks", {}) or {}
        tr = tf.get("track") or []
        if len(tr) > 1:
            out.append({"id": m["id"], "n": m.get("signNumber"), "en": m["englishName"],
                        "built": is_built(m), "pts": [tuple(p) for p in tr]})
    return out


def project(lat0):
    k = math.cos(math.radians(lat0))
    return lambda p: ((p[1]) * 111.320 * k, p[0] * 110.574)   # km


def build_route(start, end, budget_m, cands):
    """Python port of buildBikeRoute() in mobile/src/lib/routing.ts."""
    direct = hav(start, end)
    segs_all = []
    for t in cands:
        L = path_len(t["pts"])
        segs_all.append([(t, t["pts"], L), (t, list(reversed(t["pts"])), L)])
    chosen = []
    remaining = list(range(len(cands)))

    def rlen(segs):
        tot, cur = 0.0, start
        for _, pts, L in segs:
            tot += hav(cur, pts[0]) + L
            cur = pts[-1]
        return tot + hav(cur, end)

    while True:
        best = None
        for ti in remaining:
            for seg in segs_all[ti]:
                for i in range(len(chosen) + 1):
                    trial = chosen[:i] + [seg] + chosen[i:]
                    L = rlen(trial)
                    if L <= direct + budget_m and (best is None or L < best[1]):
                        best = (trial, L, ti)
        if best is None:
            break
        chosen = best[0]
        remaining.remove(best[2])
    return chosen, direct, rlen(chosen)


def main():
    plt = setup_matplotlib()
    T = trails()
    lat0 = sum(p[0] for t in T for p in t["pts"]) / sum(len(t["pts"]) for t in T)
    P = project(lat0)

    # ----------------------------------------------------------------- map
    def in_core(p):
        return p[0] > 53.512 and -113.572 < p[1] < -113.53

    fig, (ax, axz) = plt.subplots(1, 2, figsize=(7.0, 3.9),
                                  gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.04})
    for a, zoom in ((ax, False), (axz, True)):
        for t in sorted(T, key=lambda t: t["built"]):
            if zoom and not any(in_core(p) for p in t["pts"]):
                continue
            xs, ys = zip(*[P(p) for p in t["pts"]])
            c = BLUE if t["built"] else ORANGE
            a.plot(xs, ys, color=c, lw=(2.0 if zoom else 1.5) if t["built"] else 1.1,
                   solid_capstyle="round", zorder=3 if t["built"] else 2)
            a.plot(xs[0], ys[0], "o", ms=3.4 if zoom else 2.8, color="white", mec=c, mew=1.0, zorder=4)
        a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])
        for s_ in a.spines.values():
            s_.set_visible(False)
    # zoom window
    core = [P(p) for t in T if t["built"] for p in t["pts"] if in_core(p)]
    cx0, cx1 = min(x for x, _ in core) - 0.15, max(x for x, _ in core) + 0.15
    cy0, cy1 = min(y for _, y in core) - 0.15, max(y for _, y in core) + 0.15
    axz.set_xlim(cx0, cx1); axz.set_ylim(cy0, cy1)
    ax.add_patch(plt.Rectangle((cx0, cy0), cx1 - cx0, cy1 - cy0, fill=False, ec=INK2, lw=0.7, ls="--"))
    for s_ in axz.spines.values():
        s_.set_visible(True); s_.set_color(INK2); s_.set_linestyle("--"); s_.set_linewidth(0.7)
    # number labels in the zoom, with a small repulsion pass
    labs = []
    for t in [t for t in T if t["built"]]:
        x, y = P(t["pts"][0])
        if cx0 <= x <= cx1 and cy0 <= y <= cy1:
            labs.append([x, y, x + 0.06, y + 0.04, t["n"]])
    for _ in range(200):
        for i, a_ in enumerate(labs):
            for b_ in labs[i + 1:]:
                dx, dy = a_[2] - b_[2], a_[3] - b_[3]
                if abs(dx) < 0.13 and abs(dy) < 0.09:
                    push = 0.006
                    a_[3] += push if dy >= 0 else -push; b_[3] -= push if dy >= 0 else -push
                    a_[2] += push if dx >= 0 else -push; b_[2] -= push if dx >= 0 else -push
    for x, y, lx, ly, n in labs:
        axz.plot([x, lx], [y, ly], color=MUTED, lw=0.4, zorder=4)
        axz.text(lx, ly, str(n), fontsize=6.5, color=INK, zorder=6, ha="center", va="center",
                 bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    sx, sy = x0 + 0.03 * (x1 - x0), y0 + 0.04 * (y1 - y0)
    ax.plot([sx, sx + 2.0], [sy, sy], color=INK, lw=2, solid_capstyle="butt")
    ax.text(sx + 1.0, sy - 0.55, "2 km", ha="center", fontsize=7, color=INK)
    ax.annotate("N", xy=(x0 + 0.04 * (x1 - x0), y1 - 0.12 * (y1 - y0)),
                xytext=(x0 + 0.04 * (x1 - x0), y1 - 0.24 * (y1 - y0)),
                ha="center", fontsize=8, color=INK, arrowprops=dict(arrowstyle="-|>", color=INK, lw=1))
    zx, zy = cx0 + 0.04 * (cx1 - cx0), cy0 + 0.04 * (cy1 - cy0)
    axz.plot([zx, zx + 0.5], [zy, zy], color=INK, lw=2, solid_capstyle="butt")
    axz.text(zx + 0.25, zy + 0.05, "500 m", ha="center", fontsize=7, color=INK)
    ax.set_title("A. All signed and drafted trails")
    axz.set_title("B. Central river valley, finished signs numbered")
    ax.plot([], [], color=BLUE, lw=1.6, label=f"Finished sign ({sum(t['built'] for t in T)} trails)")
    ax.plot([], [], color=ORANGE, lw=1.1, label=f"Draft sign page ({sum(not t['built'] for t in T)} trails)")
    ax.legend(loc="lower right", fontsize=7)
    fig.savefig(FIG / "map.pdf")
    plt.close(fig)

    # ------------------------------------------------------------- routing
    # A ride from the west end of the signed network to its east end,
    # restricted to the finished signs (the ones a rider can actually find).
    built = [t for t in T if t["built"]]
    allpts = [p for t in built for p in t["pts"] if in_core(p)]
    start = min(allpts, key=lambda p: p[0])   # southern end of the central valley
    end = max(allpts, key=lambda p: p[0])     # northern end
    budgets = [500, 1000, 3000]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.2), sharex=True, sharey=True)
    stats = {}
    for ax, b in zip(axes, budgets):
        chosen, direct, total = build_route(start, end, b, built)
        for t in built:
            if not any(in_core(p) for p in t["pts"]):
                continue
            xs, ys = zip(*[P(p) for p in t["pts"]])
            ax.plot(xs, ys, color="#d9d8d3", lw=1.0, zorder=1)
        cur = start
        for _, pts, _ in chosen:
            (ax_, ay_), (bx_, by_) = P(cur), P(pts[0])
            ax.plot([ax_, bx_], [ay_, by_], color=MUTED, lw=0.9, ls=(0, (2, 2)), zorder=2)
            xs, ys = zip(*[P(p) for p in pts])
            ax.plot(xs, ys, color=AQUA, lw=2.0, zorder=3, solid_capstyle="round")
            cur = pts[-1]
        (ax_, ay_), (bx_, by_) = P(cur), P(end)
        ax.plot([ax_, bx_], [ay_, by_], color=MUTED, lw=0.9, ls=(0, (2, 2)), zorder=2)
        for p, lab in ((start, "A"), (end, "B")):
            x, y = P(p)
            ax.plot(x, y, "o", ms=6, color=INK, zorder=5)
            ax.text(x + 0.12, y, lab, ha="center", fontsize=7, weight="bold")
        ax.set_title(f"Detour budget {b / 1000:g} km", fontsize=8)
        ax.text(0.02, 0.02, f"{len(chosen)} trails, {total / 1000:.1f} km\n(direct {direct / 1000:.1f} km)",
                transform=ax.transAxes, fontsize=6.5, color=INK2, va="bottom")
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        stats[f"route{['Half','One','Three'][budgets.index(b)]}Trails"] = len(chosen)
        stats[f"route{['Half','One','Three'][budgets.index(b)]}Total"] = f"{total / 1000:.1f}"
        stats["routeDirect"] = f"{direct / 1000:.1f}"
    fig.savefig(FIG / "routing.pdf")
    plt.close(fig)

    xs = [P(p)[0] for t in T for p in t["pts"]]
    ys = [P(p)[1] for t in T for p in t["pts"]]
    stats.update({
        "mapTrails": len(T),
        "mapBuilt": sum(t["built"] for t in T),
        "mapExtentEW": f"{max(xs) - min(xs):.0f}",
        "mapExtentNS": f"{max(ys) - min(ys):.0f}",
        "mapTotalKm": f"{sum(path_len(t['pts']) for t in T) / 1000:.0f}",
        "mapBuiltKm": f"{sum(path_len(t['pts']) for t in T if t['built']) / 1000:.1f}",
    })
    write_macros("map", stats)
    print("map:", stats)


if __name__ == "__main__":
    main()
