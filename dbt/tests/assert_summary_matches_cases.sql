-- Fails if the headline numbers do not add up to the case-level table.
select s.cases, s.compliant_cases, c.total, c.ok
from {{ ref('conformance_summary') }} s
cross join (
    select count(*) as total,
           sum(case when compliant then 1 else 0 end) as ok
    from {{ ref('conformance_cases') }}
) c
where s.cases <> c.total
   or s.compliant_cases <> c.ok
   or s.compliant_cases + s.non_compliant_cases <> s.cases