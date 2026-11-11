# Dashboard Page 1: ER Bottleneck Overview

File: `dashboard/careflow_dashboard.pbix`, page "Overview".
Data: simulated ER event log, 5,000 patient visits, cleaned with dbt.

## Purpose
Show an administrator, in one screen, how big the problem is and where the waiting time goes.

## KPI cards
| Card | Measure | Value |
|---|---|---|
| Total cases | `Total Cases` | 5,000 |
| Average visit duration (minutes) | `Avg Visit Minutes` | about 124 |
| X-Ray patients sent back to Triage | `XRay Sent Back %` | 37.2% |
| Total hand-overs | `Total Hand-overs` | 25,802 |

## DAX measures
```
Total Cases = DISTINCTCOUNT(event_log[case_id])

Avg Visit Minutes =
AVERAGEX(
    VALUES(event_log[case_id]),
    CALCULATE(DATEDIFF(MIN(event_log[event_timestamp]), MAX(event_log[event_timestamp]), MINUTE))
)

XRay Cases = CALCULATE(DISTINCTCOUNT(event_log[case_id]), event_log[activity] = "X-Ray")

XRay Sent Back Cases =
CALCULATE(
    DISTINCTCOUNT(transitions[case_id]),
    transitions[from_activity] = "X-Ray",
    transitions[to_activity] = "Triage"
)

XRay Sent Back % = DIVIDE([XRay Sent Back Cases], [XRay Cases])

Total Hand-overs = COUNTROWS(transitions)
```
Calculated column in `bottleneck_summary`:
```
Hand-over = bottleneck_summary[from_activity] & " -> " & bottleneck_summary[to_activity]
```

## Visuals
1. **Bar chart: total waiting time by hand-over** (top 10). Axis: Hand-over. Values: sum of `total_minutes`. Sorted largest first.
   The largest bars: Treatment to Discharge (145,028 minutes, 23.4%), Triage to Doctor Consultation (128,236 minutes, 20.7%), Doctor Consultation to X-Ray (73,287 minutes, 11.8%).
2. **Table: slowest hand-overs by average time.** Columns: Hand-over, avg_minutes, transitions.

## What it shows
- Most waiting time sits in the hand-overs that nearly every patient goes through (Treatment to Discharge, Triage to Doctor).
- The rework hand-over (X-Ray to Triage) affects 37.2% of X-Ray patients and adds about 5% of all waiting time, and these visits are about 49 minutes longer on average.

## Note
`event_log` and `transitions` are not connected by a relationship yet, so the two percentage inputs are measures on separate tables. A cases table and filters by doctor and severity are added in the drill-down step.
