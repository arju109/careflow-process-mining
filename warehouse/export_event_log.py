"""
CareFlow - export the clean dbt event_log table from DuckDB to a CSV file.

This connects the pipeline: raw CSV -> DuckDB -> dbt cleaning -> event_log -> CSV
-> process discovery (analysis/discover_process.py).

Usage:
    python warehouse/export_event_log.py
    python warehouse/export_event_log.py --out data/event_log.csv
    python analysis/discover_process.py data/event_log.csv --out results
"""
import argparse
import csv
import sys
from pathlib import Path

try:
    import duckdb
except ImportError:
    sys.exit("Missing package. Run: pip install duckdb")


def main():
    p = argparse.ArgumentParser(description="Export the dbt event_log table to CSV")
    p.add_argument("--db", default="careflow.duckdb", help="DuckDB file")
    p.add_argument("--table", default="event_log", help="table to export")
    p.add_argument("--out", default="data/event_log.csv", help="output CSV path")
    a = p.parse_args()

    if not a.table.isidentifier():
        sys.exit("Table name must be letters, digits and underscores only.")
    if not Path(a.db).exists():
        sys.exit(f"Database not found: {a.db}. Run load_to_duckdb.py and dbt run first.")

    con = duckdb.connect(a.db, read_only=True)
    try:
        cur = con.execute(f"SELECT * FROM {a.table} ORDER BY case_id, event_order")
    except duckdb.Error as err:
        sys.exit(f"Could not read table '{a.table}': {err}\nDid 'dbt run' finish successfully?")
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    con.close()

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(columns)
        w.writerows(rows)
    print(f"Exported {len(rows)} rows ({', '.join(columns)}) -> {out}")


if __name__ == "__main__":
    main()
