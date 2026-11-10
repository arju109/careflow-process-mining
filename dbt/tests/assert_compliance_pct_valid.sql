-- Fails if the compliance percentage is outside 0-100.
select compliance_pct
from {{ ref('conformance_summary') }}
where compliance_pct < 0 or compliance_pct > 100