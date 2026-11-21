"""
CareFlow - draw the as-is process map as a picture (PNG), without Graphviz.

Reads results/dfg_edges.csv (made by analysis/discover_process.py) and draws the
activities as boxes in the order of the patient journey. Arrow thickness shows how
often a hand-over happens, labels show the count and the average waiting time, and
red dashed arrows are rework (patients sent back to Registration or Triage).

Needs matplotlib (installed together with PM4Py).

Usage:
    python analysis/draw_process_map.py
    python analysis/draw_process_map.py --edges results/dfg_edges.csv --out results/process_map.png --min-count 100
"""
import argparse
import csv
import math
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
except ImportError:
    raise SystemExit("Missing package. Run: pip install matplotlib")

# (column, row) position of each activity: left to right in journey order
POS = {
    "Registration": (0, 0), "Triage": (1, 0), "Doctor Consultation": (2, 0),
    "X-Ray": (3, 1.1), "Lab Test": (3, -1.1), "Treatment": (4, 0),
    "Discharge": (5, 0.9), "Admission": (5, -0.9),
}
BOX_W, BOX_H = 0.95, 0.38
XS = 1.8   # horizontal stretch so labels fit


def main():
    p = argparse.ArgumentParser(description="Draw the process map as a PNG")
    p.add_argument("--edges", default="results/dfg_edges.csv")
    p.add_argument("--out", default="results/process_map.png")
    p.add_argument("--min-count", type=int, default=100, help="hide edges seen fewer times")
    p.add_argument("--title", default="CareFlow: as-is ER process map (simulated data, 5,000 visits)")
    a = p.parse_args()

    edges = []
    with open(a.edges, newline="") as f:
        for r in csv.DictReader(f):
            if int(r["count"]) >= a.min_count and r["source"] in POS and r["target"] in POS:
                edges.append({"s": r["source"], "t": r["target"], "n": int(r["count"]),
                              "avg": float(r["avg_minutes"]),
                              "rework": str(r["rework"]).lower() == "true"})
    if not edges:
        raise SystemExit("No edges to draw. Lower --min-count or check the file.")

    max_n = max(e["n"] for e in edges)
    fig, ax = plt.subplots(figsize=(17, 7.6))
    ax.set_xlim(-0.7, 5.7 * XS)
    ax.set_ylim(-2.2, 2.4)
    ax.axis("off")
    ax.set_title(a.title, fontsize=15, fontweight="bold", pad=12)

    def pt(name):
        x, y = POS[name]
        return (x * XS, y)

    def side_point(name, toward):
        """Point on the left or right side of a box, facing the other box."""
        x, y = pt(name)
        tx, _ = pt(toward)
        return (x + (BOX_W / 2 if tx > x else -BOX_W / 2), y)

    def top_point(name):
        x, y = pt(name)
        return (x, y + BOX_H / 2)

    for e in edges:
        s, t = e["s"], e["t"]
        (x1, y1), (x2, y2) = pt(s), pt(t)
        rad = 0.0
        if e["rework"]:
            start, end = top_point(s), top_point(t)
            options = (0.45, -0.45)
        elif x2 < x1:                                  # other backward hand-over
            if y2 > y1:                                # leave from the top, enter at the bottom
                start, end = (x1, y1 + BOX_H / 2), (x2, y2 - BOX_H / 2)
            else:
                start, end = (x1, y1 - BOX_H / 2), (x2, y2 + BOX_H / 2)
            options = (0.3, -0.3)
        elif y1 == y2 and any(POS[n][1] == POS[s][1] and POS[s][0] < POS[n][0] < POS[t][0]
                              for n in POS):          # skips a box on the same row
            start, end = side_point(s, t), side_point(t, s)
            options = (0.35,)
            rad = 0.35
        else:                                          # normal forward hand-over
            start, end = side_point(s, t), side_point(t, s)
            options = (0.0,)
        if len(options) == 2:                          # bow away from the middle row
            dx, dy = end[0] - start[0], end[1] - start[1]
            midy = (start[1] + end[1]) / 2

            def control_y(f):
                return midy - f * dx

            rad = max(options, key=lambda f: abs(control_y(f)))
        width = 1.0 + 6.0 * math.sqrt(e["n"] / max_n)
        color = "#d62728" if e["rework"] else "#4c78a8"
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=16,
                                     linewidth=width, color=color, alpha=0.85,
                                     linestyle="--" if e["rework"] else "-",
                                     connectionstyle=f"arc3,rad={rad}", zorder=1))
        dx, dy = end[0] - start[0], end[1] - start[1]
        lx = (start[0] + end[0]) / 2 + 0.5 * rad * dy
        ly = (start[1] + end[1]) / 2 - 0.5 * rad * dx
        offset = 0.0 if rad else 0.14
        ax.text(lx, ly + offset, f"{e['n']:,} | {e['avg']:.0f} min", ha="center",
                va="bottom" if not rad else "center", fontsize=9, color=color,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9), zorder=3)

    for name in POS:
        x, y = pt(name)
        ax.add_patch(FancyBboxPatch((x - BOX_W / 2, y - BOX_H / 2), BOX_W, BOX_H,
                                    boxstyle="round,pad=0.02,rounding_size=0.08",
                                    fc="#f2f2f2", ec="#333333", linewidth=1.4, zorder=4))
        ax.text(x, y, name.replace(" ", "\n", 1) if len(name) > 12 else name, ha="center",
                va="center", fontsize=10, fontweight="bold", zorder=5)

    ax.text(-0.65, -2.15, "Arrow label: number of hand-overs | average waiting minutes.  "
            "Thicker arrow = more frequent.  Red dashed = rework (sent back).",
            fontsize=9, color="#444444", ha="left")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
    print(f"Saved {out}  ({len(edges)} edges drawn, min count {a.min_count})")


if __name__ == "__main__":
    main()