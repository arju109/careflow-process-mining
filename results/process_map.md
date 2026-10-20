# As-Is Process Map (discovered from the event log)

Cases: **100**. Each arrow shows how many times one step directly followed another and the average waiting time between them. **Red arrows are rework**: a patient sent back to an earlier intake step.

```mermaid
flowchart LR
    START((Start))
    END((End))
    N_Registration["Registration<br/>100 cases"]
    N_Triage["Triage<br/>98 cases"]
    N_Doctor_Consultation["Doctor Consultation<br/>100 cases"]
    N_Lab_Test["Lab Test<br/>11 cases"]
    N_X_Ray["X-Ray<br/>55 cases"]
    N_Treatment["Treatment<br/>100 cases"]
    N_Admission["Admission<br/>18 cases"]
    N_Discharge["Discharge<br/>82 cases"]
    START -->|"100"| N_Registration
    N_Triage -->|"n=112, avg 20.0 min"| N_Doctor_Consultation
    N_Registration -->|"n=97, avg 7.1 min"| N_Triage
    N_Treatment -->|"n=82, avg 36.4 min"| N_Discharge
    N_Doctor_Consultation -->|"n=60, avg 20.8 min"| N_Treatment
    N_Doctor_Consultation -->|"n=55, avg 25.4 min"| N_X_Ray
    N_X_Ray -->|"n=40, avg 30.8 min"| N_Treatment
    N_Treatment -->|"n=18, avg 32.3 min"| N_Admission
    N_X_Ray -->|"n=15, avg 34.2 min"| N_Triage
    N_Doctor_Consultation -->|"n=11, avg 23.2 min"| N_Lab_Test
    N_Lab_Test -->|"n=11, avg 36.8 min"| N_Doctor_Consultation
    N_Registration -->|"n=3, avg 7.4 min"| N_Doctor_Consultation
    N_Discharge -->|"82"| END
    N_Admission -->|"18"| END
    linkStyle 8 stroke:#d62728,stroke-width:3px,color:#d62728
```

## Rework (loop-back) edges

| From | To | Times | % of all cases | % of cases reaching the From step | Avg minutes |
|---|---|---|---|---|---|
| X-Ray | Triage | 15 | 15.0% | 27.3% | 34.2 |

## Slowest hand-overs (average minutes)

| From | To | Avg minutes | Times |
|---|---|---|---|
| Lab Test | Doctor Consultation | 36.8 | 11 |
| Treatment | Discharge | 36.4 | 82 |
| X-Ray | Triage | 34.2 | 15 |
| Treatment | Admission | 32.3 | 18 |
| X-Ray | Treatment | 30.8 | 40 |
