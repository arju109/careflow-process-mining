# As-Is Process Map (discovered from the event log)

Cases: **5000**. Each arrow shows how many times one step directly followed another and the average waiting time between them. **Red arrows are rework**: a patient sent back to an earlier intake step.

```mermaid
flowchart LR
    START((Start))
    END((End))
    N_Registration["Registration<br/>4894 cases"]
    N_Triage["Triage<br/>4854 cases"]
    N_Doctor_Consultation["Doctor Consultation<br/>4921 cases"]
    N_Lab_Test["Lab Test<br/>566 cases"]
    N_X_Ray["X-Ray<br/>2965 cases"]
    N_Treatment["Treatment<br/>4899 cases"]
    N_Admission["Admission<br/>732 cases"]
    N_Discharge["Discharge<br/>4165 cases"]
    START -->|"4894"| N_Registration
    START -->|"97"| N_Triage
    START -->|"8"| N_Doctor_Consultation
    START -->|"1"| N_Treatment
    N_Triage -->|"n=5803, avg 22.1 min"| N_Doctor_Consultation
    N_Registration -->|"n=4709, avg 7.6 min"| N_Triage
    N_Treatment -->|"n=4087, avg 35.5 min"| N_Discharge
    N_Doctor_Consultation -->|"n=3045, avg 21.1 min"| N_Treatment
    N_Doctor_Consultation -->|"n=2902, avg 25.3 min"| N_X_Ray
    N_X_Ray -->|"n=1794, avg 30.7 min"| N_Treatment
    N_X_Ray -->|"n=1102, avg 30.3 min"| N_Triage
    N_Treatment -->|"n=713, avg 36.5 min"| N_Admission
    N_Lab_Test -->|"n=555, avg 44.1 min"| N_Doctor_Consultation
    N_Doctor_Consultation -->|"n=553, avg 25.2 min"| N_Lab_Test
    N_Registration -->|"n=180, avg 16.3 min"| N_Doctor_Consultation
    N_X_Ray -->|"n=72, avg 33.9 min"| N_X_Ray
    N_Triage -->|"n=61, avg 47.7 min"| N_X_Ray
    N_Doctor_Consultation -->|"n=47, avg 55.5 min"| N_Discharge
    N_Triage -->|"n=45, avg 46.5 min"| N_Treatment
    N_X_Ray -->|"n=30, avg 66.9 min"| N_Discharge
    N_X_Ray -->|"n=26, avg 67.9 min"| N_Doctor_Consultation
    N_Discharge -->|"4165"| END
    N_Admission -->|"732"| END
    N_Treatment -->|"99"| END
    N_Doctor_Consultation -->|"2"| END
    N_X_Ray -->|"2"| END
    linkStyle 10 stroke:#d62728,stroke-width:3px,color:#d62728
```

## Rework (loop-back) edges

| From | To | Times | % of all cases | % of cases reaching the From step | Avg minutes |
|---|---|---|---|---|---|
| X-Ray | Triage | 1102 | 22.0% | 37.2% | 30.3 |
| Doctor Consultation | Triage | 15 | 0.3% | 0.3% | 52.6 |

## Slowest hand-overs (average minutes)

| From | To | Avg minutes | Times |
|---|---|---|---|
| X-Ray | Admission | 69.5 | 11 |
| X-Ray | Doctor Consultation | 67.9 | 26 |
| X-Ray | Discharge | 66.9 | 30 |
| Lab Test | Treatment | 62.1 | 11 |
| Doctor Consultation | Doctor Consultation | 61.1 | 14 |
