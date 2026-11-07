-- Headline conformance numbers (one row).
select
    count(*)                                                              as cases,
    sum(case when compliant then 1 else 0 end)                            as compliant_cases,
    sum(case when compliant then 0 else 1 end)                            as non_compliant_cases,
    round(100.0 * sum(case when compliant then 1 else 0 end) / count(*), 1) as compliance_pct,
    round(avg(case when compliant then duration_minutes end), 1)          as avg_minutes_compliant,
    round(avg(case when not compliant then duration_minutes end), 1)      as avg_minutes_non_compliant,
    round(avg(case when not compliant then duration_minutes end)
          - avg(case when compliant then duration_minutes end), 1)        as extra_minutes_non_compliant
from {{ ref('conformance_cases') }}
