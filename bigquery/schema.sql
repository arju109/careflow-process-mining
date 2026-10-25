-- CareFlow: raw layer. All STRING on purpose; dbt casts types in the staging model.
CREATE TABLE IF NOT EXISTS `careflow.raw_ehr_events` (
  case_id        STRING,
  activity       STRING,
  timestamp      STRING,
  resource       STRING,
  patient_age    STRING,
  patient_gender STRING,
  severity       STRING,
  doctor         STRING
);

-- Quick checks after loading
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT case_id) AS total_cases
FROM `careflow.raw_ehr_events`;

SELECT activity, COUNT(*) AS events
FROM `careflow.raw_ehr_events`
GROUP BY activity
ORDER BY events DESC;
