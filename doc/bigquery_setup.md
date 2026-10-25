# BigQuery Setup Guide

## 1. Create a Google Cloud project
1. Sign in at https://console.cloud.google.com with a Google account.
2. Click the project picker at the top, then **New Project**.
3. Name it `careflow-internship` and click **Create**.
4. Note the **Project ID** (it can differ from the name, for example `careflow-internship-123456`). You need it in every command.

## 2. Open BigQuery (free sandbox)
Search for **BigQuery** in the console search bar and open it. No credit card is needed for the sandbox. Limits: loading from files is allowed, streaming inserts are not, and tables expire after 60 days.

## 3. Install the tools
```
pip install google-cloud-bigquery
```
Install the Google Cloud CLI from https://cloud.google.com/sdk/docs/install, then sign in:
```
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

## 4. Load the data
```
python bigquery/load_to_bigquery.py --project YOUR_PROJECT_ID --csv data/raw_ehr_events.csv
```
Expected output: `Loaded N rows into YOUR_PROJECT_ID.careflow.raw_ehr_events`

## 5. Verify
In the BigQuery console open the `careflow` dataset, then the `raw_ehr_events` table, then **Preview**. Or run the checks in `bigquery/schema.sql` in the query editor.

## Fallback: load through the web UI (no Python or CLI needed)
1. In BigQuery click the three dots next to your project, then **Create dataset**. ID: `careflow`.
2. Click the three dots next to `careflow`, then **Create table**.
3. Source: **Upload**, choose your CSV, format **CSV**.
4. Table name: `raw_ehr_events`. Schema: **Edit as text** and paste:
   `case_id:STRING,activity:STRING,timestamp:STRING,resource:STRING,patient_age:STRING,patient_gender:STRING,severity:STRING,doctor:STRING`
5. Under Advanced options set **Header rows to skip** to `1`, then **Create table**.

## Security
Never commit credential or key files (`*.json` keys) to GitHub. Add `*-key.json` and `credentials*.json` to `.gitignore`.
