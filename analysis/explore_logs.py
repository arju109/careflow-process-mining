"""
CareFlow - exploratory analysis of an EHR event log (standard library only).

Reports: data quality, case/event counts, activity frequency, top process
variants, loop-back rate (X-Ray -> Triage), average case duration, and average
transition times between consecutive activities.

Usage:
    python analysis/explore_logs.py data/sample_events.csv
    python analysis/explore_logs.py data/raw_ehr_events_dirty.csv --top 10
"""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime

FORMATS = ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M")


def parse_ts(value):
    for fmt in FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def load(path):
    """Read the CSV and clean the basics. Returns events and a quality report."""
    quality = Counter()
    seen = set()
    events = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            quality["rows_read"] += 1
            key = tuple(row.values())
            if key in seen:
                quality["duplicates_removed"] += 1
                continue
            seen.add(key)
            case_id = (row.get("case_id") or "").strip()
            if not case_id:
                quality["missing_case_id"] += 1
                continue
            ts = parse_ts(row.get("timestamp") or "")
            if ts is None:
                quality["missing_or_bad_timestamp"] += 1
                continue
            activity = (row.get("activity") or "").strip().title()
            if not activity:
                quality["missing_activity"] += 1
                continue
            events.append((case_id, activity, ts))
    quality["rows_kept"] = len(events)
    return events, quality


def main():
    p = argparse.ArgumentParser(description="CareFlow event log exploration")
    p.add_argument("csv_path")
    p.add_argument("--top", type=int, default=8, help="number of variants to show")
    a = p.parse_args()

    events, quality = load(a.csv_path)
    events.sort(key=lambda e: (e[0], e[2]))

    cases = defaultdict(list)
    for case_id, activity, ts in events:
        cases[case_id].append((activity, ts))

    print("=== DATA QUALITY ===")
    for k, v in quality.items():
        print(f"{k:28s} {v}")

    print("\n=== OVERVIEW ===")
    print(f"Cases : {len(cases)}")
    print(f"Events: {len(events)}")
    print(f"Avg events per case: {len(events) / len(cases):.1f}")

    print("\n=== ACTIVITY FREQUENCY ===")
    for act, n in Counter(e[1] for e in events).most_common():
        print(f"{act:22s} {n}")

    variants = Counter(" > ".join(act for act, _ in steps) for steps in cases.values())
    print(f"\n=== TOP {a.top} PROCESS VARIANTS (of {len(variants)}) ===")
    for variant, n in variants.most_common(a.top):
        print(f"{n:5d} ({100 * n / len(cases):4.1f}%)  {variant}")

    xray_cases = [s for s in cases.values() if any(act == "X-Ray" for act, _ in s)]
    loop = 0
    for steps in xray_cases:
        names = [act for act, _ in steps]
        first_xray = names.index("X-Ray")
        if "Triage" in names[first_xray + 1:]:
            loop += 1
    rate = 100 * loop / len(xray_cases) if xray_cases else 0
    print("\n=== LOOP-BACK (X-Ray -> Triage) ===")
    print(f"X-Ray cases: {len(xray_cases)}, sent back to Triage: {loop} ({rate:.1f}%)")

    def minutes(steps):
        return (steps[-1][1] - steps[0][1]).total_seconds() / 60

    all_durs = [minutes(s) for s in cases.values()]
    loop_durs = [minutes(s) for s in xray_cases
                 if "Triage" in [act for act, _ in s][[act for act, _ in s].index("X-Ray") + 1:]]
    clean_durs = [minutes(s) for s in xray_cases
                  if "Triage" not in [act for act, _ in s][[act for act, _ in s].index("X-Ray") + 1:]]
    print("\n=== CASE DURATION (minutes) ===")
    print(f"All cases average        : {sum(all_durs) / len(all_durs):.1f}")
    if loop_durs and clean_durs:
        l, c = sum(loop_durs) / len(loop_durs), sum(clean_durs) / len(clean_durs)
        print(f"X-Ray with loop-back     : {l:.1f}")
        print(f"X-Ray without loop-back  : {c:.1f}")
        print(f"Extra time from loop-back: {l - c:.1f}")

    trans = defaultdict(list)
    for steps in cases.values():
        for (a1, t1), (a2, t2) in zip(steps, steps[1:]):
            trans[(a1, a2)].append((t2 - t1).total_seconds() / 60)
    print("\n=== AVG TRANSITION TIME (minutes, top 10 slowest) ===")
    ranked = sorted(trans.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))[:10]
    for (a1, a2), vals in ranked:
        print(f"{a1:20s} -> {a2:20s} {sum(vals) / len(vals):6.1f}  (n={len(vals)})")


if __name__ == "__main__":
    main()
