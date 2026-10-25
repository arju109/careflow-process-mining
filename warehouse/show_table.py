"""
Print a DuckDB table or view.

Usage:
    python warehouse/show_table.py dq_summary
    python warehouse/show_table.py event_log --limit 20
"""
import argparse
import sys

try:
    import duckdb
except ImportError:
    sys.exit("Missing package. Run: pip install duckdb")


def main():
    p = argparse.ArgumentParser(description="Show rows from a DuckDB table")
    p.add_argument("table")
    p.add_argument("--db", default="careflow.duckdb")
    p.add_argument("--limit", type=int, default=50)
    a = p.parse_args()

    if not a.table.isidentifier():
        sys.exit("Table name must be letters, digits and underscores only.")
    con = duckdb.connect(a.db, read_only=True)
    con.sql(f"SELECT * FROM {a.table} LIMIT {int(a.limit)}").show()
    con.close()


if __name__ == "__main__":
    main()
