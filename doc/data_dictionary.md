# Data Dictionary: CareFlow EHR Event Log

Source: `simulator/generate_ehr_logs.py` (mock Emergency Room data).
One row = one event (one step in one patient's visit).

## Columns

| Column | Type (BigQuery) | Description | Example |
|---|---|---|---|
| case_id | STRING | Unique ID of one patient visit. Process mining **Case ID**. | P000123 |
| activity | STRING | Name of the step performed. Process mining **Activity**. | Triage |
| timestamp | TIMESTAMP | When the step happened. Process mining **Timestamp**. | 2026-09-01 10:15:00 |
| resource | STRING | Staff member or desk who performed the step. | Nurse A |
| patient_age | INT64 | Patient age in years (1 to 95). | 42 |
| patient_gender | STRING | `M` or `F`. | F |
| severity | STRING | `Low`, `Medium` or `High`. | Medium |
| doctor | STRING | Doctor assigned to the visit. | Dr. Rao |

## Activities

| Activity | Meaning | Typical wait before next step |
|---|---|---|
| Registration | Patient is registered at the front desk | about 6 min |
| Triage | Nurse assesses urgency | about 15 min |
| Doctor Consultation | Doctor examines the patient | about 20 min |
| X-Ray | Imaging performed | about 25 min |
| Lab Test | Blood or lab test (only when no X-Ray) | about 35 min |
| Treatment | Treatment is given | about 30 min |
| Discharge | Patient leaves | end of case |
| Admission | Patient is admitted to a ward | end of case |

Waits are about 1.6x longer during peak hours (09:00 to 12:00 and 17:00 to 20:00).

## Ideal (mandated) journey, used for conformance checking in Week 4
Registration → Triage → Doctor Consultation → (X-Ray or Lab Test, optional) → Treatment → Discharge or Admission

## Deliberate inefficiencies in the simulated data

| Pattern | Rate | Why it exists |
|---|---|---|
| X-Ray → Triage loop-back (missing paperwork form) | about 40% of X-Ray cases | The main bottleneck to discover |
| Triage skipped | about 3% of cases | Non-compliant path |
| Repeated X-Ray | about 2% of X-Ray cases | Non-compliant path |
| Admission instead of Discharge | about 15% | Outcome variation |

## Data quality issues (only with the `--dirty` flag)

| Issue | Approx. rate | Expected dbt fix |
|---|---|---|
| Activity in wrong case or with spaces (`TRIAGE`, ` triage `) | about 4% | trim and standardize case |
| Missing timestamp | about 1% | drop row and count it |
| Missing case_id | about 1% | drop row and count it |
| Timestamp in `DD/MM/YYYY HH:MM` format | about 1% | parse both formats |
| Duplicate rows | about 2% | de-duplicate |
| Rows out of order | all | sort by case_id, timestamp |

## Standard event-log format (output of the dbt models)
Process mining algorithms (PM4Py) need three columns: `case_id`, `activity`, `timestamp`. The other columns are kept as attributes for filtering in the dashboard (doctor, severity, age, gender).
