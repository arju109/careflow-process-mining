-- Staging: remove exact duplicate rows, trim text, standardise activity names,
-- parse timestamps (two formats) and tag every row with a status so that bad
-- rows are counted, not silently lost.
with raw as (

    select distinct * from {{ source('careflow_raw', 'raw_ehr_events') }}

),

parsed as (

    select
        nullif(trim(case_id), '') as case_id,

        case lower(trim(activity))
            when 'registration'        then 'Registration'
            when 'triage'              then 'Triage'
            when 'doctor consultation' then 'Doctor Consultation'
            when 'x-ray'               then 'X-Ray'
            when 'lab test'            then 'Lab Test'
            when 'treatment'           then 'Treatment'
            when 'discharge'           then 'Discharge'
            when 'admission'           then 'Admission'
        end as activity,

        {{ parse_event_ts(adapter.quote('timestamp')) }} as event_timestamp,

        nullif(trim(resource), '')      as resource,
        nullif(trim(patient_age), '')   as patient_age,
        upper(nullif(trim(patient_gender), '')) as patient_gender,
        nullif(trim(severity), '')      as severity,
        nullif(trim(doctor), '')        as doctor

    from raw

)

select
    *,
    case
        when case_id is null         then 'missing_case_id'
        when event_timestamp is null then 'missing_or_bad_timestamp'
        when activity is null        then 'unknown_activity'
        else 'kept'
    end as row_status
from parsed
