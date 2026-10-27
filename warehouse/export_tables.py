"""
CareFlow - export the dbt result tables from DuckDB to CSV files, for Power BI
or for loading into BigQuery.

Usage:
    python warehouse/export_tables.py
    python warehouse/export_tables.py --out-dir exports --tables event_log transitions
"""
import argparse
import csv
import sys
from pathlib import Path

try:
    import duckdb
except ImportError:
    sys.exit("Missing package. Run: pip install duckdb")

DEFAULT_TABLES = ["event_log", "transitions", "bottleneck_summary", "wait_by_hour", "dq_summary"]
ORDER = {"event_log": "case_id, event_order", "transitions": "case_id, step_number"}


def main():
    p = argparse.ArgumentParser(description="Export dbt tables to CSV")
    p.add_argument("--db", default="careflow.duckdb")
    p.add_argument("--out-dir", default="exports")
    p.add_argument("--tables", nargs="+", default=DEFAULT_TABLES)
    a = p.parse_args()

    if not Path(a.db).exists():
        sys.exit(f"Database not found: {a.db}. Run load_to_duckdb.py and dbt run first.")
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(a.db, read_only=True)
    for table in a.tables:
        if not table.isidentifier():
            sys.exit(f"Invalid table name: {table}")
        order = f" ORDER BY {ORDER[table]}" if table in ORDER else ""
        try:
            cur = con.execute(f"SELECT * FROM {table}{order}")
        except duckdb.Error as err:
            print(f"Skipped {table}: {err}")
            continue
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
        path = out_dir / f"{table}.csv"
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(columns)
            w.writerows(rows)
        print(f"Exported {len(rows):6d} rows -> {path}")
    con.close()


if __name__ == "__main__":
    main()
