"""
CareFlow - load the raw EHR event log CSV into a local DuckDB file.

Everything is loaded as text (all_varchar) so bad values never break the load;
dbt cleans and converts types afterwards. Safe to re-run (table is replaced).

Setup:   pip install duckdb
Usage:   python warehouse/load_to_duckdb.py --csv data/raw_ehr_events_dirty.csv
"""
import argparse
import sys
from pathlib import Path

try:
    import duckdb
except ImportError:
    sys.exit("Missing package. Run: pip install duckdb")


def main():
    p = argparse.ArgumentParser(description="Load EHR event log CSV into DuckDB")
    p.add_argument("--csv", required=True, help="path to the CSV file")
    p.add_argument("--db", default="careflow.duckdb", help="DuckDB file to create/update")
    p.add_argument("--table", default="raw_ehr_events", help="table name")
    a = p.parse_args()

    if not a.table.isidentifier():
        sys.exit("Table name must be letters, digits and underscores only.")
    csv_path = Path(a.csv)
    if not csv_path.exists():
        sys.exit(f"CSV not found: {csv_path}")

    path_sql = csv_path.resolve().as_posix().replace("'", "''")
    con = duckdb.connect(a.db)
    con.execute(
        f"CREATE OR REPLACE TABLE {a.table} AS "
        f"SELECT * FROM read_csv('{path_sql}', header=true, all_varchar=true)"
    )
    rows = con.execute(f"SELECT COUNT(*) FROM {a.table}").fetchone()[0]
    print(f"Loaded {rows} rows into {a.db} -> table {a.table}")
    con.close()


if __name__ == "__main__":
    main()
