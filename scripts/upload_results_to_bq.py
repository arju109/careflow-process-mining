from pathlib import Path
from google.cloud import bigquery

PROJECT = "double-fusion-511703-i4"
DATASET = "careflow"
EXPORTS = Path("exports")
FILES = ["bottleneck_summary", "transitions", "wait_by_hour", "event_log", "dq_summary"]

client = bigquery.Client(project=PROJECT)
cfg = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    autodetect=True,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)

for name in FILES:
    table_id = f"{PROJECT}.{DATASET}.pbi_{name}"
    with open(EXPORTS / f"{name}.csv", "rb") as f:
        client.load_table_from_file(f, table_id, job_config=cfg).result()
    print(name, client.get_table(table_id).num_rows, "rows")