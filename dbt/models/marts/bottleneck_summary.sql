-- Average time between every pair of steps, and how much of the total waiting
-- time each hand-over is responsible for. The biggest total_minutes is the
-- biggest bottleneck. Example: average time from Triage to Doctor Consultation.
with t as (

    select * from {{ ref('transitions') }}

),

totals as (

    select sum(wait_minutes) as grand_total from t

)

select
    from_activity,
    to_activity,
    count(*)                                            as transitions,
    count(distinct case_id)                             as cases,
    round(avg(wait_minutes), 1)                         as avg_minutes,
    round(max(wait_minutes), 1)                         as max_minutes,
    round(sum(wait_minutes), 0)                         as total_minutes,
    round(100.0 * sum(wait_minutes) / (select grand_total from totals), 1) as pct_of_total_wait,
    max(case when is_rework then 1 else 0 end)          as is_rework
from t
group by from_activity, to_activity
