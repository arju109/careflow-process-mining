from pathlib import Path
import pandas as pd
import pm4py

df = pd.read_csv("exports/event_log.csv")
df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])
df["activity"] = df["activity"].str.strip().str.title()
df = pm4py.format_dataframe(
    df, case_id="case_id", activity_key="activity", timestamp_key="event_timestamp"
)

# Same mandated journey as conformance_check.py
tree = pm4py.parse_process_tree(
    "->('Registration','Triage','Doctor Consultation',"
    "X(tau,'X-Ray',->('Lab Test','Doctor Consultation')),"
    "'Treatment',X('Discharge','Admission'))"
)
net, im, fm = pm4py.convert_to_petri_net(tree)

diag = pm4py.conformance_diagnostics_token_based_replay(
    df, net, im, fm,
    activity_key="concept:name", case_id_key="case:concept:name",
    timestamp_key="time:timestamp",
)
fitness = pm4py.fitness_token_based_replay(
    df, net, im, fm,
    activity_key="concept:name", case_id_key="case:concept:name",
    timestamp_key="time:timestamp",
)

case_ids = df["case:concept:name"].drop_duplicates().tolist()
pm = pd.DataFrame({
    "case_id": case_ids,
    "pm4py_fit": [d["trace_is_fit"] for d in diag],
    "trace_fitness": [round(d["trace_fitness"], 4) for d in diag],
    "missing_tokens": [d["missing_tokens"] for d in diag],
    "remaining_tokens": [d["remaining_tokens"] for d in diag],
})

mine = pd.read_csv("results/conformance_cases.csv")
col = "compliant" if "compliant" in mine.columns else "conformant"
merged = pm.merge(mine[["case_id", col]], on="case_id")
merged["agree"] = merged["pm4py_fit"].astype(bool) == merged[col].astype(bool)

total = len(merged)
rows = [
    ("Total cases", total),
    ("PM4Py perfectly fitting cases", int(merged["pm4py_fit"].sum())),
    ("PM4Py fit %", round(100 * merged["pm4py_fit"].mean(), 2)),
    ("Custom check compliant cases", int(merged[col].sum())),
    ("Custom check compliant %", round(100 * merged[col].mean(), 2)),
    ("Cases where both methods agree", int(merged["agree"].sum())),
    ("Agreement %", round(100 * merged["agree"].mean(), 2)),
    ("Average log fitness", round(fitness["average_trace_fitness"], 4)),
]
Path("results").mkdir(exist_ok=True)
pd.DataFrame(rows, columns=["metric", "value"]).to_csv(
    "results/conformance_pm4py_summary.csv", index=False)
merged.to_csv("results/conformance_pm4py_cases.csv", index=False)

for k, v in rows:
    print(f"{k}: {v}")