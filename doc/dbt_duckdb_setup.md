# dbt + DuckDB Setup (free, runs on your laptop)

The dbt models in `dbt/` run on **DuckDB** (local file, no account, no cost) and also on
**BigQuery** by switching the target. Models are written once and use small macros
(`dbt/macros/portable_sql.sql`) for the few functions that differ.

> Confirm with your mentor that a local DuckDB warehouse is acceptable. The project
> document names BigQuery, so keep BigQuery as the target you can demo if it is available.

## 0. Python version
dbt often lags behind the newest Python. If installs fail on Python 3.15, install
**Python 3.12 or 3.13** from python.org (tick "Add python.exe to PATH") and use it just
for this project:
```
cd "C:\Users\Laptop Solution\Projects\careflow-process-mining"
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```
Your prompt should start with `(.venv)`. If PowerShell blocks the script, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.
Add `.venv/` and `*.duckdb` to `.gitignore`.

## 1. Install
```
pip install -r requirements-dbt.txt
```

## 2. Create messy data and load it
```
python simulator/generate_ehr_logs.py --cases 5000 --dirty --out data/raw_ehr_events_dirty.csv
python warehouse/load_to_duckdb.py --csv data/raw_ehr_events_dirty.csv
```
This creates `careflow.duckdb` in the repo root (do not commit it).

## 3. Run dbt (from inside the dbt folder)
```
cd dbt
dbt debug --profiles-dir .
dbt run   --profiles-dir .
dbt test  --profiles-dir .
cd ..
```
- `dbt debug` should end with "All checks passed".
- `dbt run` builds `stg_ehr_events` (view), `event_log` and `dq_summary` (tables).
- `dbt test` checks no nulls and only valid activity names in `event_log`.

## 4. Look at the results
```
python warehouse/show_table.py dq_summary
python warehouse/show_table.py event_log --limit 20
```

## 5. Audit: prove the pipeline is correct (use this in the Mid Review)
```
python analysis/explore_logs.py data/raw_ehr_events_dirty.csv
```
The numbers `rows_read`, `duplicates_removed`, `missing_case_id`,
`missing_or_bad_timestamp` and `rows_kept` must equal the rows in `dq_summary`.
Two independent implementations (Python and SQL) agreeing is your pipeline audit.

## Using BigQuery instead
1. Load the CSV into BigQuery as `careflow.raw_ehr_events` (see `docs/bigquery_setup.md`).
2. Edit `dbt/profiles.yml`: set `project: YOUR_PROJECT_ID`.
3. `pip install dbt-bigquery`, run `gcloud auth application-default login`, then:
```
cd dbt
dbt run  --profiles-dir . --target bigquery --vars "{raw_schema: careflow}"
dbt test --profiles-dir . --target bigquery --vars "{raw_schema: careflow}"
```
In the free BigQuery sandbox keep models as views and tables (no incremental models or
snapshots, which need DML).

## Model overview
| Model | Type | Purpose |
|---|---|---|
| stg_ehr_events | view | de-duplicate, trim, standardise activity names, parse both timestamp formats, tag each row with a status |
| event_log | table | clean event log (case_id, activity, event_timestamp, attributes, event_order) for PM4Py and the dashboard |
| dq_summary | table | counts of rows read, duplicates removed, rejected rows by reason, rows kept |
