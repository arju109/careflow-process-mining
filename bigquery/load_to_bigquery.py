"""
CareFlow - Week 1: load the raw EHR event log CSV into Google BigQuery.

The raw table keeps every column as STRING on purpose. Raw data can contain
bad timestamps, blanks and odd formats, and a typed load would fail on them.
Type casting and cleaning happen later in the dbt staging model.

Setup (once):
    pip install google-cloud-bigquery
    gcloud auth application-default login

Usage:
    python bigquery/load_to_bigquery.py --project YOUR_PROJECT_ID --csv data/raw_ehr_events.csv
    python bigquery/load_to_bigquery.py --project YOUR_PROJECT_ID --csv data/raw_ehr_events_dirty.csv --table raw_ehr_events_dirty
"""
import argparse
import sys

try:
    from google.cloud import bigquery
    from google.api_core.exceptions import GoogleAPIError
except ImportError:
    sys.exit("Missing package. Run: pip install google-cloud-bigquery")

COLUMNS = ["case_id", "activity", "timestamp", "resource",
           "patient_age", "patient_gender", "severity", "doctor"]


def main():
    p = argparse.ArgumentParser(description="Load EHR event log CSV into BigQuery")
    p.add_argument("--project", required=True, help="Google Cloud project ID")
    p.add_argument("--dataset", default="careflow", help="BigQuery dataset name")
    p.add_argument("--table", default="raw_ehr_events", help="BigQuery table name")
    p.add_argument("--csv", required=True, help="path to the CSV file")
    p.add_argument("--location", default="US", help="dataset location")
    a = p.parse_args()

    client = bigquery.Client(project=a.project)

    dataset = bigquery.Dataset(f"{a.project}.{a.dataset}")
    dataset.location = a.location
    client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset ready : {a.project}.{a.dataset}")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=[bigquery.SchemaField(c, "STRING") for c in COLUMNS],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # safe to re-run
    )

    table_id = f"{a.project}.{a.dataset}.{a.table}"
    try:
        with open(a.csv, "rb") as f:
            job = client.load_table_from_file(f, table_id, job_config=job_config)
        job.result()  # wait for the load to finish
    except (GoogleAPIError, OSError) as err:
        sys.exit(f"Load failed: {err}")

    table = client.get_table(table_id)
    print(f"Loaded {table.num_rows} rows into {table_id}")


if __name__ == "__main__":
    main()
