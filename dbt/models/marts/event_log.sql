-- Clean event log in the format process mining needs:
-- case_id, activity, event_timestamp (+ attributes for dashboard filters).
select
    case_id,
    activity,
    event_timestamp,
    resource,
    {{ safe_int('patient_age') }} as patient_age,
    patient_gender,
    severity,
    doctor,
    row_number() over (
        partition by case_id
        order by event_timestamp, activity
    ) as event_order
from {{ ref('stg_ehr_events') }}
where row_status = 'kept'
