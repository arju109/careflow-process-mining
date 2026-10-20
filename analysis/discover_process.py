"""
CareFlow - process discovery: build the "as-is" patient process map.

Reads an event log CSV (case_id, activity, timestamp) and discovers the
directly-follows graph (DFG): which step follows which, how often, and how long
the hand-over takes. Outputs:
    results/dfg_edges.csv    every edge with counts and waiting times
    results/process_map.md   a Mermaid flowchart (renders on GitHub, no install)
    results/*.png            PM4Py pictures (only if PM4Py + Graphviz are installed)

The core uses only the Python standard library, so it runs anywhere.
If PM4Py is installed, it also runs PM4Py's discovery and cross-checks the result.

Usage:
    python analysis/discover_process.py data/sample_events.csv
    python analysis/discover_process.py data/raw_ehr_events_dirty.csv --out results
"""
import argparse
import csv
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S%z", "%d/%m/%Y %H:%M")

# Position of each step in the ideal journey. An edge that goes back to
# Registration/Triage from a later step is "rework" (e.g. X-Ray -> Triage).
RANK = {"Registration": 0, "Triage": 1, "Doctor Consultation": 2, "X-Ray": 3,
        "Lab Test": 3, "Treatment": 4, "Discharge": 5, "Admission": 5}


def parse_ts(value):
    value = (value or "").strip()
    for fmt in FORMATS:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=None)
        except ValueError:
            continue
    return None


def load_events(path):
    """Read the CSV. Accepts 'timestamp' or 'event_timestamp'. Skips unusable rows."""
    events, skipped = [], 0
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        ts_col = "event_timestamp" if "event_timestamp" in reader.fieldnames else "timestamp"
        seen = set()
        for row in reader:
            key = tuple(row.values())
            if key in seen:
                skipped += 1
                continue
            seen.add(key)
            case_id = (row.get("case_id") or "").strip()
            activity = (row.get("activity") or "").strip().title()
            ts = parse_ts(row.get(ts_col))
            if not case_id or not activity or ts is None:
                skipped += 1
                continue
            events.append((case_id, activity, ts))
    events.sort(key=lambda e: (e[0], e[2]))
    return events, skipped


def discover_dfg(events):
    """Return per-case traces, edge stats, start and end activity counts."""
    traces = defaultdict(list)
    for case_id, activity, ts in events:
        traces[case_id].append((activity, ts))

    edge_minutes = defaultdict(list)
    edge_cases = defaultdict(set)
    starts, ends = Counter(), Counter()
    for case_id, steps in traces.items():
        starts[steps[0][0]] += 1
        ends[steps[-1][0]] += 1
        for (a, t1), (b, t2) in zip(steps, steps[1:]):
            edge_minutes[(a, b)].append((t2 - t1).total_seconds() / 60)
            edge_cases[(a, b)].add(case_id)
    return traces, edge_minutes, edge_cases, starts, ends


def is_rework(a, b):
    return RANK.get(b, 99) <= 1 and RANK.get(a, 0) > RANK.get(b, 99)


def node_id(name):
    return "N_" + "".join(c if c.isalnum() else "_" for c in name)


def write_outputs(out_dir, traces, edge_minutes, edge_cases, starts, ends, min_count):
    out_dir.mkdir(parents=True, exist_ok=True)
    n_cases = len(traces)

    act_cases = Counter()
    for steps in traces.values():
        for act in {a for a, _ in steps}:
            act_cases[act] += 1

    rows = []
    for (a, b), mins in edge_minutes.items():
        rows.append({
            "source": a, "target": b, "count": len(mins),
            "cases": len(edge_cases[(a, b)]),
            "pct_of_cases": round(100 * len(edge_cases[(a, b)]) / n_cases, 1),
            "pct_of_source_cases": round(100 * len(edge_cases[(a, b)]) / act_cases[a], 1),
            "avg_minutes": round(statistics.mean(mins), 1),
            "median_minutes": round(statistics.median(mins), 1),
            "rework": is_rework(a, b),
        })
    rows.sort(key=lambda r: -r["count"])
    with open(out_dir / "dfg_edges.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    shown = [r for r in rows if r["count"] >= min_count]
    activities = sorted({r["source"] for r in shown} | {r["target"] for r in shown},
                        key=lambda x: (RANK.get(x, 99), x))
    lines = ["flowchart LR", "    START((Start))", "    END((End))"]
    for act in activities:
        lines.append(f'    {node_id(act)}["{act}<br/>{act_cases[act]} cases"]')
    link_count, rework_idx = 0, []
    for act, n in starts.items():
        if act in activities:
            lines.append(f'    START -->|"{n}"| {node_id(act)}')
            link_count += 1
    for r in shown:
        lines.append(f'    {node_id(r["source"])} -->|"n={r["count"]}, avg {r["avg_minutes"]} min"| {node_id(r["target"])}')
        if r["rework"]:
            rework_idx.append(link_count)
        link_count += 1
    for act, n in ends.items():
        if act in activities:
            lines.append(f'    {node_id(act)} -->|"{n}"| END')
            link_count += 1
    if rework_idx:
        idx = ",".join(map(str, rework_idx))
        lines.append(f"    linkStyle {idx} stroke:#d62728,stroke-width:3px,color:#d62728")

    rework_rows = [r for r in rows if r["rework"]]
    slowest = sorted(rows, key=lambda r: -r["avg_minutes"])[:5]
    md = ["# As-Is Process Map (discovered from the event log)", "",
          f"Cases: **{n_cases}**. Each arrow shows how many times one step directly followed another "
          "and the average waiting time between them. **Red arrows are rework**: a patient sent back "
          "to an earlier intake step.", "",
          "```mermaid", *lines, "```", "",
          "## Rework (loop-back) edges", ""]
    if rework_rows:
        md += ["| From | To | Times | % of all cases | % of cases reaching the From step | Avg minutes |", "|---|---|---|---|---|---|"]
        md += [f'| {r["source"]} | {r["target"]} | {r["count"]} | {r["pct_of_cases"]}% | {r["pct_of_source_cases"]}% | {r["avg_minutes"]} |'
               for r in rework_rows]
    else:
        md.append("None found.")
    md += ["", "## Slowest hand-overs (average minutes)", "",
           "| From | To | Avg minutes | Times |", "|---|---|---|---|"]
    md += [f'| {r["source"]} | {r["target"]} | {r["avg_minutes"]} | {r["count"]} |' for r in slowest]
    (out_dir / "process_map.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return rows


def run_pm4py(events, rows, out_dir):
    """Optional: PM4Py discovery, cross-checked against the stdlib result."""
    try:
        import pandas as pd
        import pm4py
    except ImportError:
        print("\n[PM4Py] not installed - skipped (see docs/process_discovery.md).")
        return
    try:
        df = pd.DataFrame(events, columns=["case_id", "activity", "timestamp"])
        df = pm4py.format_dataframe(df, case_id="case_id", activity_key="activity",
                                    timestamp_key="timestamp")
        dfg, starts, ends = pm4py.discover_dfg(df)
        mine = {(r["source"], r["target"]): r["count"] for r in rows}
        same = {k: int(v) for k, v in dfg.items()} == mine
        print(f"\n[PM4Py] discovered {len(dfg)} edges; "
              f"{'MATCHES' if same else 'DIFFERS FROM'} the standard-library result.")
        variants = pm4py.get_variants(df)
        print(f"[PM4Py] process variants: {len(variants)}")
        perf, p_starts, p_ends = pm4py.discover_performance_dfg(df)
        try:
            pm4py.save_vis_dfg(dfg, starts, ends, str(out_dir / "dfg_frequency.png"))
            pm4py.save_vis_performance_dfg(perf, p_starts, p_ends, str(out_dir / "dfg_performance.png"))
            print(f"[PM4Py] pictures saved in {out_dir}/")
        except Exception as err:  # usually Graphviz is not installed
            print(f"[PM4Py] could not draw pictures ({err}). Install Graphviz and add it to PATH.")
    except Exception as err:
        print(f"\n[PM4Py] error: {err}")


def main():
    p = argparse.ArgumentParser(description="CareFlow process discovery")
    p.add_argument("csv_path")
    p.add_argument("--out", default="results", help="output folder")
    p.add_argument("--min-count", type=int, default=1, help="hide edges seen fewer times")
    a = p.parse_args()

    events, skipped = load_events(a.csv_path)
    if not events:
        raise SystemExit("No usable events found in the file.")
    traces, edge_minutes, edge_cases, starts, ends = discover_dfg(events)
    out_dir = Path(a.out)
    rows = write_outputs(out_dir, traces, edge_minutes, edge_cases, starts, ends, a.min_count)

    print(f"Events used: {len(events)} (skipped {skipped}), cases: {len(traces)}")
    print(f"Distinct edges: {len(rows)}")
    print("\nTop edges by frequency:")
    for r in rows[:8]:
        flag = "  <-- REWORK" if r["rework"] else ""
        print(f'  {r["source"]:20s} -> {r["target"]:20s} {r["count"]:6d}  avg {r["avg_minutes"]:6.1f} min{flag}')
    for r in rows:
        if r["rework"]:
            print(f'\nRework: {r["pct_of_source_cases"]}% of patients who reached {r["source"]} '
                  f'were sent on to {r["target"]} ({r["pct_of_cases"]}% of all cases)')
    print(f"\nWrote {out_dir / 'dfg_edges.csv'} and {out_dir / 'process_map.md'}")
    run_pm4py(events, rows, out_dir)


if __name__ == "__main__":
    main()
