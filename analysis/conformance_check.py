from pathlib import Path
import pandas as pd

EVENT_LOG = Path("exports/event_log.csv")
OUT_DIR = Path("results")
OUT_DIR.mkdir(exist_ok=True)

# The ideal journey, in order
IDEAL = ["Registration", "Triage", "Doctor Consultation", "Treatment", "Discharge"]
# Diagnostic steps allowed between Doctor Consultation and Treatment
OPTIONAL = {"X-Ray"}

df = pd.read_csv(EVENT_LOG).sort_values(["case_id", "event_order"])
print("Activities found:", sorted(df["activity"].unique()))

paths = df.groupby("case_id")["activity"].apply(list)


def check(path):
    issues = []
    core = [a for a in path if a not in OPTIONAL]
    known = [a for a in core if a in IDEAL]

    if any(a not in IDEAL for a in core):
        issues.append("Unexpected activity")
    if len(known) != len(set(known)):
        issues.append("Repeated activity (rework)")
    if any(a not in known for a in IDEAL):
        issues.append("Missing step")

    first = []
    for a in known:
        if a not in first:
            first.append(a)
    if first != [a for a in IDEAL if a in first]:
        issues.append("Wrong order")

    if "Doctor Consultation" in path and "Treatment" in path:
        d, t = path.index("Doctor Consultation"), path.index("Treatment")
        if any(a in OPTIONAL and not (d < i < t) for i, a in enumerate(path)):
            issues.append("Diagnostic step out of position")
    return issues


rows = []
for case_id, path in paths.items():
    issues = check(path)
    rows.append({
        "case_id": case_id,
        "path": " > ".join(path),
        "conformant": len(issues) == 0,
        "deviations": "; ".join(issues),
    })
cases = pd.DataFrame(rows)
cases.to_csv(OUT_DIR / "conformance_cases.csv", index=False)

total = len(cases)
ok = int(cases["conformant"].sum())

summary = [("Total cases", total, 100.0),
           ("Conformant cases", ok, round(100 * ok / total, 2)),
           ("Non-conformant cases", total - ok, round(100 * (total - ok) / total, 2))]
dev_counts = (cases.loc[~cases["conformant"], "deviations"]
              .str.split("; ").explode().value_counts())
for name, n in dev_counts.items():
    summary.append((f"Deviation: {name}", int(n), round(100 * n / total, 2)))

summary_df = pd.DataFrame(summary, columns=["metric", "cases", "percent_of_cases"])
summary_df.to_csv(OUT_DIR / "conformance_summary.csv", index=False)

print("\n", summary_df.to_string(index=False))
print("\nTop 5 path variants:")
print(cases["path"].value_counts().head(5).to_string())