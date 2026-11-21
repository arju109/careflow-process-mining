# CareFlow: Clinical Pathway Process Mining

Infotact Solutions internship project (Data Analytics). Author: Arju.

## Problem

Hospital administrators see the average Emergency Room wait time, but not the real sequence of steps each patient goes through, so hidden bottlenecks stay hidden.

## What this project does

It rebuilds the real patient journeys from an event log (case, activity, timestamp), finds where time is lost, checks every visit against the mandated journey, and shows the result in a dashboard.

The data is **simulated** (real hospital data is private). The simulator plants a known problem, a loop-back from X-Ray to Triage, so the analysis can be checked against it.

## Main results (5,000 simulated visits)

* 37.2% of patients who had an X-Ray were sent back to Triage; those visits took about 49 minutes longer.
* Most waiting time sits in Treatment to Discharge (23.4%) and Triage to Doctor Consultation (20.7%).
* 67.1% of visits followed the mandated journey; non-compliant visits took about 38 minutes longer.
* Three independent conformance methods (Python, dbt SQL, PM4Py token-based replay) flag the same visits.

## Architecture

```
simulator (Python) -> CSV -> BigQuery raw table
                          -> DuckDB raw table -> dbt (staging, event\_log, dq\_summary,
                             transitions, bottleneck\_summary, wait\_by\_hour,
                             conformance\_cases, conformance\_summary)
                          -> exported tables -> BigQuery -> Power BI dashboard
event\_log -> process discovery (own script + PM4Py) -> process map, conformance checks
```

## Tech stack

Python, Google BigQuery (sandbox), dbt (DuckDB locally, models also written for BigQuery), PM4Py, Power BI Desktop.

## Repository structure

```
simulator/    mock EHR event log generator
data/         small sample CSV (large files are not committed)
analysis/     exploration, process discovery, process map drawing, conformance checks
bigquery/     BigQuery load script and table definition
warehouse/    DuckDB load, show and export scripts
dbt/          cleaning, bottleneck and conformance models, macros, tests
dashboard/    Power BI report (careflow\_dashboard.pbix)
results/      process map, edge table, conformance reports
doc/          data dictionary, setup guides, dashboard page notes
evidence/     screenshots proving each step ran
```

## How to run

```
python simulator/generate\_ehr\_logs.py --cases 5000 --dirty --out data/raw\_ehr\_events\_dirty.csv
python warehouse/load\_to\_duckdb.py --csv data/raw\_ehr\_events\_dirty.csv
cd dbt
dbt run --profiles-dir .
dbt test --profiles-dir .
cd ..
python warehouse/export\_event\_log.py
python analysis/discover\_process.py data/event\_log.csv --out results
python analysis/draw\_process\_map.py
python analysis/conformance\_check.py data/event\_log.csv
```

Use Python 3.12 in a virtual environment (`pip install -r requirements-dbt.txt pm4py pandas matplotlib`).

## Dashboard pages

1. Overview: KPI cards, waiting time by hand-over, slowest hand-overs.
2. Peak Hours and Rework: waiting time by hour, rework cost, hand-over matrix.
3. Drill-down and Conformance: slicers for doctor, severity and age group, compliance, deviations.
4. Process Map: picture of the as-is process.

## Weekly plan and status

|Week|Work|Status|
|-|-|-|
|1|EHR simulator, load into BigQuery, dbt setup|Done|
|2|dbt event log models, process discovery with PM4Py|Done|
|3|Bottleneck calculations, Power BI dashboard|Done|
|4|Conformance checking, drill-downs, polish|Done|

## Limitations

* The data is simulated, so findings show the method works, not real hospital performance.
* dbt was run on DuckDB; the models are written to run on BigQuery too but were not run there.
* Doctors and severity do not differ in the simulator, so the drill-down filters show similar results.

## Team

|Member|Branch|Role|
|-|-|-|
|Arju|`arju`|Team Lead, all components|



