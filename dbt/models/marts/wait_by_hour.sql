-- Average hand-over time by the hour of day when the step started.
-- Shows the peak-hour effect (9-12 and 17-20 are the busy hours).
select
    hour_of_day,
    count(*)                    as transitions,
    round(avg(wait_minutes), 1) as avg_minutes
from {{ ref('transitions') }}
group by hour_of_day
