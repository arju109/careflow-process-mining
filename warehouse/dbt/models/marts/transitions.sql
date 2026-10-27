-- One row per hand-over: patient moves from one step to the next.
-- Feeds the bottleneck summary and the dashboard (filter by doctor, severity, hour).
with ordered as (

    select
        case_id,
        activity,
        event_timestamp,
        event_order,
        doctor,
        severity,
        patient_age,
        lead(activity) over (partition by case_id order by event_order)        as next_activity,
        lead(event_timestamp) over (partition by case_id order by event_order) as next_timestamp
    from {{ ref('event_log') }}

)

select
    case_id,
    event_order                                                as step_number,
    activity                                                   as from_activity,
    next_activity                                              as to_activity,
    event_timestamp                                            as from_timestamp,
    next_timestamp                                             as to_timestamp,
    {{ minutes_between('event_timestamp', 'next_timestamp') }} as wait_minutes,
    extract(hour from event_timestamp)                         as hour_of_day,
    case
        when next_activity = 'Triage'
             and activity in ('Doctor Consultation', 'X-Ray', 'Lab Test',
                              'Treatment', 'Discharge', 'Admission') then true
        when next_activity = 'Registration' and activity <> 'Registration' then true
        else false
    end                                                        as is_rework,
    doctor,
    severity,
    patient_age
from ordered
where next_activity is not null
