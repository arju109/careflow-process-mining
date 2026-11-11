-- Fails (returns a row) if the conformance table does not have one row per visit.
select *
from (
    select
        (select count(*) from {{ ref('conformance_cases') }})         as cases_checked,
        (select count(distinct case_id) from {{ ref('event_log') }})  as cases_in_log
) as s
where cases_checked <> cases_in_log
