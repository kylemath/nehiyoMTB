"""Figure: the project's history, read straight from `git log`.

Cumulative commits over time, with the milestones that the prose refers to
annotated where their commit subjects first appear.
"""
from __future__ import annotations

import datetime as dt

from common import BLUE, FIG, INK, INK2, MUTED, git_log, setup_matplotlib, write_macros

# (pattern in commit subject, label, label x-offset in days, label height as
#  a fraction of the commit count) — offsets only keep the labels apart.
MILESTONES = [
    ("added 3d qr code", "First printable signs\npushed to GitHub", 60, 0.45),
    ("update 2023", "Second season\nof signs", 0, 0.45),
    ("i see you trail", "OpenSCAD plaque generator\n+ first interpretive page", -200, 0.75),
    ("sign selector", "Sign factory and\ncatalogue editor", -330, 1.12),
    ("EdmontonTrailMaps", "Companion app\n(Expo + Supabase)", -90, 1.42),
    ("Shopify checkout", "Signs offered\nto other riders", 150, 0.6),
    ("KOM board", "Site and app merged;\nKOM free-sign board", 130, 1.12),
]


def main():
    plt = setup_matplotlib()
    log = git_log()
    dates = [dt.date.fromisoformat(d) for d, _, _ in log]
    n = list(range(1, len(dates) + 1))

    fig, ax = plt.subplots(figsize=(7.0, 2.5))
    ax.step(dates, n, where="post", color=BLUE, lw=1.8)
    ax.set_ylabel("Commits (cumulative)")
    ax.grid(axis="y", color="#ecebe7", lw=0.6)
    ax.set_ylim(0, len(dates) * 1.7)
    used = set()
    stats = {}
    for pat, label, dx, lev in MILESTONES:
        for i, (d, a, s) in enumerate(log):
            if pat.lower() in s.lower() and pat not in used:
                used.add(pat)
                x = dates[i]
                y = n[i]
                ty = len(dates) * lev
                ax.annotate(label, xy=(x, y), xytext=(x + dt.timedelta(days=dx), ty), fontsize=6.3, color=INK,
                            ha="center", va="bottom",
                            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6, shrinkA=0, shrinkB=2))
                ax.plot(x, y, "o", ms=3.5, color=BLUE, mec="white", mew=0.8, zorder=4)
                break
    ax.set_xlim(dates[0] - dt.timedelta(days=90), dates[-1] + dt.timedelta(days=260))
    fig.savefig(FIG / "timeline.pdf")
    plt.close(fig)

    authors = {a for _, a, _ in log}
    stats["gitCommits"] = len(log)
    stats["gitFirstYear"] = dates[0].year
    stats["gitLastDate"] = dates[-1].strftime("%B %Y")
    stats["gitHumanCommits"] = sum(1 for _, a, _ in log if a != "Claude")
    stats["gitAssistantCommits"] = sum(1 for _, a, _ in log if a == "Claude")
    write_macros("timeline", stats)
    print("timeline:", stats, authors)


if __name__ == "__main__":
    main()
