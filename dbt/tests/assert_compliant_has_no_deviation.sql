-- Fails if a compliant visit still has a deviation label.
select *
from {{ ref('conformance_cases') }}
where compliant and primary_deviation is not null
