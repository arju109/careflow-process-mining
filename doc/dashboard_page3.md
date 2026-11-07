# Dashboard Page 3: Drill-down and Conformance

File: `dashboard/careflow_dashboard.pbix`, page "Drill-down and Conformance".
Data: simulated ER event log, 5,000 patient visits.

## Purpose
Let an administrator filter the whole picture by doctor, severity and age group, and see how many visits followed the mandated journey, what the deviations are, and which hand-overs they affect.

## Data model
`conformance_cases` (one row per visit, from the dbt model, loaded from BigQuery table `pbi_conformance_cases`) is the central table. It is connected to the detail tables by `case_id`:

| Relationship | Type | Filter direction |
|---|---|---|
| conformance_cases[case_id] to transitions[case_id] | one to many | single (from conformance_cases) |
| conformance_cases[case_id] to event_log[case_id] | one to many | single (from conformance_cases) |

A slicer on doctor, severity or age group therefore filters the visit table, the hand-overs and the event log together.
`bottleneck_summary` and `wait_by_hour` are pre-aggregated tables and are not filtered by the slicers.

## Slicers
Doctor, Severity, Age group (from `conformance_cases`).

## DAX measures (table `conformance_cases`)
```
Cases = COUNTROWS(conformance_cases)

Compliant Cases = CALCULATE(COUNTROWS(conformance_cases), conformance_cases[compliant] = TRUE())

Compliance % = DIVIDE([Compliant Cases], [Cases])

Avg Visit Min Filtered = AVERAGE(conformance_cases[duration_minutes])

Extra Minutes Non-compliant =
CALCULATE(AVERAGE(conformance_cases[duration_minutes]), conformance_cases[compliant] = FALSE())
- CALCULATE(AVERAGE(conformance_cases[duration_minutes]), conformance_cases[compliant] = TRUE())
```

## Visuals
1. Cards: Cases, Compliance %, Avg Visit Min Filtered, Extra Minutes Non-compliant.
2. Bar chart: number of visits by main deviation (`primary_deviation`, blanks removed).
3. Matrix: hand-over map. Rows `from_activity`, columns `to_activity`, values `Total Hand-overs`, colour gradient. Responds to the slicers.
4. Bar chart: Compliance % by doctor.

## Results (all visits)
- 5,000 visits, 67.1% compliant, non-compliant visits about 38 minutes longer.
- Main deviations: sent back to Triage after X-Ray (1,102), then other deviations (193), Triage skipped (146).
- Compliance is similar across doctors (about 66% to 69%) and severities. That is expected: the simulator does not make doctors or severity differ, so the filters show no real difference in this data.
- "Other deviation" mostly comes from steps lost while cleaning rows with bad timestamps.
