"""
CareFlow - conformance checking (Week 4 requirement, done early).

Compares what patients actually went through (the event log) with the hospital's
mandated journey and flags every non-compliant visit.

Mandated journey:
    Registration > Triage > Doctor Consultation
        > (X-Ray   OR   Lab Test > Doctor Consultation review)   [optional]
        > Treatment > Discharge or Admission

Outputs (default folder: results/):
    conformance_summary.csv     headline numbers
    conformance_deviations.csv  which deviations occur and what they cost
    conformance_cases.csv       one row per visit (useful for the dashboard)
    conformance_groups.csv      compliance by doctor and by severity
    conformance_variants.csv    the most common paths and whether they comply
    conformance_report.md       readable summary

Standard library only.

Usage:
    python analysis/conformance_check.py data/event_log.csv
    python analysis/conformance_check.py data/raw_ehr_events_dirty.csv --out results
"""
import argparse
import csv
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%d/%m/%Y %H:%M")

# The mandated journey as a pattern over the activity sequence (joined with '>').
IDEAL_PATTERN = re.compile(
    r"^Registration>Triage>Doctor Consultation>"
    r"(X-Ray>|Lab Test>Doctor Consultation>)?"
    r"Treatment>(Discharge|Admission)$"
)
IDEAL_TEXT = ("Registration > Triage > Doctor Consultation > "
              "(X-Ray | Lab Test > Doctor Consultation) > Treatment > Discharge or Admission")


def parse_ts(value):
    value = (value or "").strip()
    for fmt in FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def load_events(path):
    """Read the CSV, skipping duplicates and unusable rows. Returns events and counts."""
    events, skipped, seen = [], 0, set()
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        ts_col = "event_timestamp" if "event_timestamp" in reader.fieldnames else "timestamp"
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
            events.append((case_id, activity, ts,
                           (row.get("doctor") or "n/a").strip() or "n/a",
                           (row.get("severity") or "n/a").strip() or "n/a"))
    events.sort(key=lambda e: (e[0], e[2]))
    return events, skipped


def find_deviations(acts):
    """Return the list of deviations of one visit, most important first."""
    tags = []
    if "X-Ray" in acts and "Triage" in acts[acts.index("X-Ray") + 1:]:
        tags.append("Sent back to Triage after X-Ray")
    elif acts.count("Triage") > 1:
        tags.append("Triage repeated")
    if "Triage" not in acts:
        tags.append("Triage skipped")
    if acts.count("X-Ray") > 1:
        tags.append("X-Ray repeated")
    if acts[0] != "Registration":
        tags.append("Does not start with Registration")
    if acts[-1] not in ("Discharge", "Admission"):
        tags.append("Does not end with Discharge or Admission")
    if not tags:
        tags.append("Other deviation")
    return tags


def pct(part, whole):
    return round(100 * part / whole, 1) if whole else 0.0


def avg(values):
    return round(statistics.mean(values), 1) if values else 0.0


def main():
    p = argparse.ArgumentParser(description="CareFlow conformance checking")
    p.add_argument("csv_path")
    p.add_argument("--out", default="results")
    a = p.parse_args()

    events, skipped = load_events(a.csv_path)
    if not events:
        raise SystemExit("No usable events found in the file.")

    visits = defaultdict(list)
    for case_id, act, ts, doctor, severity in events:
        visits[case_id].append((act, ts, doctor, severity))

    cases = []
    for case_id, steps in visits.items():
        acts = [s[0] for s in steps]
        trace = ">".join(acts)
        compliant = bool(IDEAL_PATTERN.match(trace))
        tags = [] if compliant else find_deviations(acts)
        duration = (steps[-1][1] - steps[0][1]).total_seconds() / 60
        cases.append({
            "case_id": case_id, "compliant": compliant,
            "primary_deviation": tags[0] if tags else "",
            "all_deviations": "; ".join(tags), "events": len(acts),
            "duration_minutes": round(duration, 1),
            "doctor": steps[0][2], "severity": steps[0][3], "trace": " > ".join(acts),
        })
    cases.sort(key=lambda c: c["case_id"])

    n = len(cases)
    ok = [c for c in cases if c["compliant"]]
    bad = [c for c in cases if not c["compliant"]]
    avg_ok = avg([c["duration_minutes"] for c in ok])
    avg_bad = avg([c["duration_minutes"] for c in bad])

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    def write_csv(name, rows, fields):
        with open(out / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    # summary
    summary = [
        ("cases", n), ("compliant_cases", len(ok)), ("non_compliant_cases", len(bad)),
        ("compliance_pct", pct(len(ok), n)),
        ("avg_minutes_compliant", avg_ok), ("avg_minutes_non_compliant", avg_bad),
        ("extra_minutes_non_compliant", round(avg_bad - avg_ok, 1)),
        ("events_skipped_in_loading", skipped),
    ]
    write_csv("conformance_summary.csv", [{"metric": k, "value": v} for k, v in summary],
              ["metric", "value"])

    # deviations (a visit can have several, so shares can add up to more than 100%)
    dev_cases = defaultdict(list)
    for c in bad:
        for tag in c["all_deviations"].split("; "):
            dev_cases[tag].append(c)
    dev_rows = []
    for tag, items in sorted(dev_cases.items(), key=lambda kv: -len(kv[1])):
        dev_rows.append({
            "deviation": tag, "cases": len(items),
            "pct_of_all_cases": pct(len(items), n),
            "pct_of_non_compliant": pct(len(items), len(bad)),
            "avg_minutes": avg([c["duration_minutes"] for c in items]),
            "extra_minutes_vs_compliant": round(avg([c["duration_minutes"] for c in items]) - avg_ok, 1),
        })
    write_csv("conformance_deviations.csv", dev_rows,
              ["deviation", "cases", "pct_of_all_cases", "pct_of_non_compliant",
               "avg_minutes", "extra_minutes_vs_compliant"])

    # cases
    write_csv("conformance_cases.csv", cases,
              ["case_id", "compliant", "primary_deviation", "all_deviations", "events",
               "duration_minutes", "doctor", "severity", "trace"])

    # groups
    groups = []
    for kind in ("doctor", "severity"):
        by = defaultdict(list)
        for c in cases:
            by[c[kind]].append(c)
        for name, items in sorted(by.items()):
            good = sum(1 for c in items if c["compliant"])
            groups.append({"group_type": kind, "group": name, "cases": len(items),
                           "compliant_cases": good, "compliance_pct": pct(good, len(items))})
    write_csv("conformance_groups.csv", groups,
              ["group_type", "group", "cases", "compliant_cases", "compliance_pct"])

    # variants
    variants = Counter(c["trace"] for c in cases)
    compliant_traces = {c["trace"] for c in ok}
    var_rows = [{"trace": t, "cases": k, "pct_of_cases": pct(k, n),
                 "compliant": t in compliant_traces} for t, k in variants.most_common()]
    write_csv("conformance_variants.csv", var_rows, ["trace", "cases", "pct_of_cases", "compliant"])

    # markdown report
    md = ["# Conformance Report", "",
          f"Mandated journey: {IDEAL_TEXT}", "",
          f"- Visits checked: **{n}**",
          f"- Compliant: **{len(ok)}** ({pct(len(ok), n)}%)",
          f"- Non-compliant: **{len(bad)}** ({pct(len(bad), n)}%)",
          f"- Average visit: compliant {avg_ok} min, non-compliant {avg_bad} min "
          f"(**{round(avg_bad - avg_ok, 1)} min longer**)", "",
          "## Deviations (a visit can have more than one)", "",
          "| Deviation | Visits | % of all visits | Avg minutes | Extra minutes |",
          "|---|---|---|---|---|"]
    md += [f"| {r['deviation']} | {r['cases']} | {r['pct_of_all_cases']}% | {r['avg_minutes']} | "
           f"{r['extra_minutes_vs_compliant']} |" for r in dev_rows]
    md += ["", "## Most common paths", "", "| Path | Visits | Compliant |", "|---|---|---|"]
    md += [f"| {r['trace']} | {r['cases']} | {'yes' if r['compliant'] else 'no'} |" for r in var_rows[:8]]
    (out / "conformance_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # console
    print(f"Mandated journey: {IDEAL_TEXT}\n")
    print(f"Visits checked : {n}  (events skipped while loading: {skipped})")
    print(f"Compliant      : {len(ok)} ({pct(len(ok), n)}%)")
    print(f"Non-compliant  : {len(bad)} ({pct(len(bad), n)}%)")
    print(f"Average visit  : compliant {avg_ok} min, non-compliant {avg_bad} min "
          f"({round(avg_bad - avg_ok, 1)} min longer)\n")
    print("Deviations (a visit can have more than one):")
    for r in dev_rows:
        print(f"  {r['deviation']:42s} {r['cases']:5d} visits  {r['pct_of_all_cases']:5.1f}%  "
              f"+{r['extra_minutes_vs_compliant']} min")
    print(f"\nWrote 6 files to {out}/")


if __name__ == "__main__":
    main()
