-- Fails if the percentage shares of waiting time do not add up to about 100.
select total
from (
    select sum(pct_of_total_wait) as total
    from {{ ref('bottleneck_summary') }}
) as s
where abs(total - 100) > 1
