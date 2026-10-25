-- Data quality audit: how many rows were read, removed and why.
-- Compare with: python analysis/explore_logs.py <csv>   (same cleaning rules)
with src as (

    select count(*) as n from {{ source('careflow_raw', 'raw_ehr_events') }}

),

stg as (

    select * from {{ ref('stg_ehr_events') }}

)

select 'rows_read' as metric, (select n from src) as value
union all
select 'duplicates_removed', (select n from src) - (select count(*) from stg)
union all
select
    case row_status when 'kept' then 'rows_kept' else row_status end,
    count(*)
from stg
group by row_status
