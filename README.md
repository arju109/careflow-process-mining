# CareFlow: Clinical Pathway Process Mining

Infotact Solutions internship project (Data Analytics, Project 3).

## Problem
Hospital administrators see the *average* ER wait time but not the real sequence of
events a patient goes through. Hidden loop-backs (for example, patients sent back to
Triage after an X-Ray because of a missing form) cause the delays.

## Goal
Build a pipeline that turns raw EHR event logs into a discovered "as-is" process map,
finds bottlenecks, checks conformance against the ideal patient journey, and shows
everything in a dashboard that supports an operational decision.

## Tech Stack
| Layer | Tool |
|---|---|
| Data simulation | Python |
| Warehouse | Google BigQuery |
| Transformation | dbt |
| Process mining | PM4Py |
| Dashboard | Power BI / Looker Studio |

## Repository Structure
```
careflow-process-mining/
├── simulator/        # Week 1: mock EHR event log generator
├── data/             # small sample outputs (large files are not committed)
├── requirements.txt
└── README.md
```
Further folders (`dbt/`, `mining/`, `dashboard/`, `docs/`) are added in later weeks.

## Event Log Schema
| Column | Description |
|---|---|
| case_id | Unique patient visit ID (Case_ID) |
| activity | Step performed, e.g. Triage, X-Ray (Activity_Name) |
| timestamp | When the step happened (Timestamp) |
| resource | Staff member or desk who performed it |
| patient_age, patient_gender | Patient demographics |
| severity | Low / Medium / High |
| doctor | Doctor assigned to the patient |

## Quick Start
```bash
# clean data
python simulator/generate_ehr_logs.py --cases 5000 --out data/raw_ehr_events.csv

# messy data for the dbt cleaning phase
python simulator/generate_ehr_logs.py --cases 5000 --dirty --out data/raw_ehr_events_dirty.csv
```
The simulator deliberately includes operational problems: about 40% of X-Ray patients
are sent back to Triage, waits are longer at peak hours, and a few paths skip Triage or
repeat the X-Ray (used later for conformance checking).

## Weekly Plan
| Week | Event Log Engineering | Process Mining and BI | Status |
|---|---|---|---|
| 1 | EHR simulator | Load to BigQuery, dbt setup | In progress |
| 2 | dbt event-log models | PM4Py process discovery | Planned |
| 3 | Transition-time calculations | Power BI dashboard | Planned |
| 4 | Conformance checking | Dashboard polish and drill-downs | Planned |

## Team
| Member | Branch | Responsibility |
|---|---|---|
| Arju (Team Lead) | `arju` | Simulator, BigQuery, dbt |
| TBD | TBD | TBD |
| TBD | TBD | TBD |
| TBD | TBD | TBD |
