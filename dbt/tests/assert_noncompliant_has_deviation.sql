-- Fails if a non-compliant visit has no deviation label.
select *
from {{ ref('conformance_cases') }}
where not compliant and primary_deviation is null
