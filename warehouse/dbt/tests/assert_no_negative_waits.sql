-- Fails (returns rows) if any hand-over has a negative waiting time.
select *
from {{ ref('transitions') }}
where wait_minutes < 0
