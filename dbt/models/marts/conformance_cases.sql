-- One row per patient visit: did it follow the mandated journey, and if not, why?
-- Mandated journey:
--   Registration > Triage > Doctor Consultation
--   > (X-Ray | Lab Test > Doctor Consultation) > Treatment > Discharge or Admission
-- Same rules as analysis/conformance_check.py, so the two can be compared.
with per_case as (

    select
        case_id,
        string_agg(activity, '>' order by event_order)                 as trace,
        count(*)                                                       as events,
        min(case when activity = 'X-Ray'  then event_order end)        as first_xray,
        max(case when activity = 'Triage' then event_order end)        as last_triage,
        sum(case when activity = 'Triage' then 1 else 0 end)           as triage_count,
        sum(case when activity = 'X-Ray'  then 1 else 0 end)           as xray_count,
        min(event_timestamp)                                           as start_ts,
        max(event_timestamp)                                           as end_ts,
        max(doctor)                                                    as doctor,
        max(severity)                                                  as severity,
        max(patient_age)                                               as patient_age
    from {{ ref('event_log') }}
    group by case_id

),

flagged as (

    select
        *,
        {{ regex_match('trace', '^Registration>Triage>Doctor Consultation>(X-Ray>|Lab Test>Doctor Consultation>)?Treatment>(Discharge|Admission)$') }} as compliant,
        (first_xray is not null and last_triage > first_xray)           as sent_back_after_xray
    from per_case

)

select
    case_id,
    compliant,
    case
        when compliant                                              then null
        when sent_back_after_xray                                   then 'Sent back to Triage after X-Ray'
        when triage_count > 1                                       then 'Triage repeated'
        when triage_count = 0                                       then 'Triage skipped'
        when xray_count > 1                                         then 'X-Ray repeated'
        when left(trace, 12) <> 'Registration'                      then 'Does not start with Registration'
        when right(trace, 9) not in ('Discharge', 'Admission')      then 'Does not end with Discharge or Admission'
        else 'Other deviation'
    end                                                             as primary_deviation,
    events,
    round({{ minutes_between('start_ts', 'end_ts') }}, 1)           as duration_minutes,
    doctor,
    severity,
    patient_age,
    case
        when patient_age is null then 'Unknown'
        when patient_age < 18    then 'Under 18'
        when patient_age < 40    then '18-39'
        when patient_age < 65    then '40-64'
        else '65+'
    end                                                             as age_group,
    replace(trace, '>', ' > ')                                      as trace
from flagged
