# Power BI Setup and Data Import (Week 3)

## Goal
Build the CareFlow operations dashboard in Power BI Desktop from the tables produced by the dbt pipeline.

## Tool
Microsoft Power BI Desktop (free, Windows). Report file: `dashboard/careflow_dashboard.pbix`.

## Data sources (exported from DuckDB by `warehouse/export_tables.py`)
| Table (CSV in `exports/`) | Rows | Use in the dashboard |
|---|---|---|
| bottleneck_summary | 26 | average and total waiting time for every pair of steps |
| transitions | 25,802 | one row per hand-over, used for drill-down by doctor, severity and hour |
| wait_by_hour | 24 | average hand-over time by hour of day |
| event_log | 30,802 | the clean event log (cases, activities, timestamps) |
| dq_summary | 5 | data quality audit numbers |

`transitions` has 25,802 rows because each of the 5,000 visits with n events has n - 1 hand-overs: 30,802 events - 5,000 cases = 25,802.

## How the data was imported
1. Power BI Desktop, Home, Get data, Text/CSV.
2. Selected each CSV from the `exports` folder and clicked Load.
3. Checked column types in Transform data: timestamps as Date/Time, `wait_minutes` and `avg_minutes` as Decimal number, counts as Whole number, `is_rework` as True/False or Whole number.
4. Closed and applied.

## Data model
The summary tables (`bottleneck_summary`, `wait_by_hour`, `dq_summary`) are already aggregated, so they are used as separate tables without relationships. `transitions` and `event_log` hold the detail rows and will be used for filters (doctor, severity, hour of day).

## Verification
- `transitions`: 25,802 rows
- `bottleneck_summary`: 26 rows
- `wait_by_hour`: 24 rows
- `event_log`: 30,802 rows

These match the row counts printed by `export_tables.py` and the dbt tables.

## Evidence
Screenshots in `evidence/`: the imported tables and row counts in Power BI.

## Next
Dashboard page 1: KPI cards and a bar chart of total waiting time by hand-over.
