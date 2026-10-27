{# Small helpers so the same models run on DuckDB (local) and BigQuery. #}

{% macro parse_event_ts(col) %}
  {%- if target.type == 'bigquery' -%}
    coalesce(
      safe.parse_timestamp('%Y-%m-%d %H:%M:%S', trim({{ col }})),
      safe.parse_timestamp('%d/%m/%Y %H:%M', trim({{ col }}))
    )
  {%- else -%}
    coalesce(
      try_strptime(trim({{ col }}), '%Y-%m-%d %H:%M:%S'),
      try_strptime(trim({{ col }}), '%d/%m/%Y %H:%M')
    )
  {%- endif -%}
{% endmacro %}

{% macro safe_int(col) %}
  {%- if target.type == 'bigquery' -%}
    safe_cast({{ col }} as int64)
  {%- else -%}
    try_cast({{ col }} as integer)
  {%- endif -%}
{% endmacro %}

{# Minutes between two timestamps (end minus start). #}
{% macro minutes_between(start_ts, end_ts) %}
  {%- if target.type == 'bigquery' -%}
    timestamp_diff({{ end_ts }}, {{ start_ts }}, second) / 60.0
  {%- else -%}
    date_diff('second', {{ start_ts }}, {{ end_ts }}) / 60.0
  {%- endif -%}
{% endmacro %}
