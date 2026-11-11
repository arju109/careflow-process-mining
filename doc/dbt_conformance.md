# dbt Conformance Models (Week 4)

## Goal
Move the conformance check into the dbt pipeline, so every run of the pipeline produces a table that says which patient visits followed the mandated journey and which did not.

## Mandated journey
Registration > Triage > Doctor Consultation > (X-Ray | Lab Test > Doctor Consultation) > Treatment > Discharge or Admission

## Models
| Model | Type | Content |
|---|---|---|
| `conformance_cases` | table | one row per visit: `compliant` (true or false), `primary_deviation`, number of events, duration in minutes, doctor, severity, the full path |
| `conformance_summary` | table | one row: visits, compliant and non-compliant counts, compliance %, average duration of compliant and non-compliant visits, extra minutes |

## How it works (`conformance_cases.sql`)
1. For every visit, `string_agg(activity, '>' order by event_order)` joins the steps into one path string, for example `Registration>Triage>Doctor Consultation>X-Ray>Treatment>Discharge`.
2. A regular expression (macro `regex_match`) checks whether the path matches the mandated journey. A match means `compliant`.
3. For non-compliant visits, a CASE expression assigns the main deviation in priority order: sent back to Triage after X-Ray, Triage repeated, Triage skipped, X-Ray repeated, does not start with Registration, does not end with Discharge or Admission, other.
4. Duration comes from the first and last timestamp (macro `minutes_between`).

## Tests
- `conformance_cases`: `case_id` is not null and unique, `compliant` is not null, `primary_deviation` only has allowed values.
- `conformance_summary`: `compliance_pct` is not null.
- `tests/assert_conformance_covers_all_cases.sql`: one conformance row per visit in the event log.
- `tests/assert_compliant_has_no_deviation.sql`: compliant visits have no deviation label.
- `tests/assert_noncompliant_has_deviation.sql`: non-compliant visits always have one.

## Audit
The same rules exist in Python (`analysis/conformance_check.py`) and in SQL (dbt). Comparing the two on the same 5,000 visits, every visit gets the same compliant flag and the same main deviation: 3,354 compliant (67.1%), 1,646 non-compliant. PM4Py token-based replay (`analysis/conformance_pm4py.py`) flags the same visits. Three independent methods agree.

## Result
Non-compliant visits last about 38 minutes longer than compliant ones (about 150 against 111 minutes). The largest deviation is being sent back to Triage after an X-Ray (22.0% of all visits).
