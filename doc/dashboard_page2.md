# Dashboard Page 2: Peak Hours and Rework

File: `dashboard/careflow_dashboard.pbix`, page "Peak Hours and Rework".
Data: simulated ER event log, 5,000 patient visits, cleaned with dbt.

## Purpose
Answer two questions for the administrator: when are hand-overs slowest, and what does the X-Ray to Triage loop-back cost?

## Visuals
1. **Line chart: average hand-over time by hour of day.** Table `wait_by_hour`: X-axis `hour_of_day` (do not summarize), Y-axis `avg_minutes`. Shows the peak-hour effect: hand-overs that start at 09:00 to 12:00 and 17:00 to 20:00 take longer.
2. **Cards: rework cost.**
   - X-Ray patients sent back to Triage (`XRay Sent Back Cases`, 1,102)
   - Share of all waiting time caused by rework hand-overs (`Rework Wait Share`, about 5.5%)
   - Visit length with loop-back and without loop-back (X-Ray patients), and the difference (`Extra Minutes From Loopback`, about 49)
3. **Matrix: hand-over map.** Rows `from_activity`, columns `to_activity`, values `transitions`, with a colour gradient. Dark cells are the busiest hand-overs; the X-Ray to Triage cell is the loop-back. This is a standard-visual version of the process map.

## DAX measures
```
Rework Wait Share =
DIVIDE(
    CALCULATE(SUM(bottleneck_summary[total_minutes]), bottleneck_summary[is_rework] = 1),
    SUM(bottleneck_summary[total_minutes])
)

Visit Min With Loopback =
AVERAGEX(
    FILTER(
        VALUES(transitions[case_id]),
        CALCULATE(COUNTROWS(transitions), transitions[from_activity] = "X-Ray", transitions[to_activity] = "Triage") > 0
    ),
    CALCULATE(SUM(transitions[wait_minutes]))
)

Visit Min XRay No Loopback =
AVERAGEX(
    FILTER(
        VALUES(transitions[case_id]),
        CALCULATE(COUNTROWS(transitions), transitions[from_activity] = "X-Ray") > 0
        && CALCULATE(COUNTROWS(transitions), transitions[from_activity] = "X-Ray", transitions[to_activity] = "Triage") = 0
    ),
    CALCULATE(SUM(transitions[wait_minutes]))
)

Extra Minutes From Loopback = [Visit Min With Loopback] - [Visit Min XRay No Loopback]
```
The length of a visit equals the sum of its hand-over times, so the measures use `transitions`.

## What it shows
- Hand-overs are slower in the busy hours, so staffing at peak times matters.
- The loop-back affects 37% of X-Ray patients and makes their visit about 49 minutes longer, even though the single X-Ray to Triage hand-over is only about 5% of all waiting time. The cost is the repeated Triage and doctor consultation.
