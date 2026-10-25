# Process Discovery Guide (Week 2)

`analysis/discover_process.py` rebuilds the **as-is process map** of the Emergency Room from the
event log. It answers: what path do patients really take, how often, and where does time go?

## Run it
```
python analysis/discover_process.py data/sample_events.csv
python analysis/discover_process.py data/raw_ehr_events_dirty.csv --out results_dirty
```
Input: any CSV with `case_id`, `activity` and `timestamp` (or `event_timestamp`) columns. The dbt
`event_log` export works too. Bad rows (missing IDs, unreadable timestamps, duplicates) are skipped and counted.

## Output
| File | Content |
|---|---|
| `results/dfg_edges.csv` | one row per edge: source, target, count, cases, % of cases, average and median minutes, rework flag |
| `results/process_map.md` | Mermaid flowchart (GitHub draws it automatically), rework table, slowest hand-overs |
| `results/dfg_frequency.png`, `results/dfg_performance.png` | PM4Py pictures (only if PM4Py and Graphviz are installed) |

Open `results/process_map.md` on GitHub to see the diagram. Red arrows are rework: patients sent back
to Registration or Triage from a later step (for example X-Ray to Triage).

## Key ideas
- **Directly-follows graph (DFG):** a node for every activity and an arrow A to B whenever B happens right after A in a case. The arrow carries how many times, and the average waiting time.
- **As-is process:** what actually happened, discovered from data, not what the hospital's manual says.
- **Rework / loop-back:** a patient returns to an earlier step. It adds waiting time and is the bottleneck this project is about.
- **Two measures per arrow:** frequency (how common) and performance (how slow). A rare slow arrow and a common fast arrow need different fixes.

## Optional: use PM4Py
The script uses only standard Python, so it works today. If PM4Py is installed it also runs PM4Py's own
discovery (`discover_dfg`, `discover_performance_dfg`, `get_variants`) and prints whether PM4Py's graph
**matches** the script's result. Two independent methods agreeing is useful proof for the Mid Review.

PM4Py may not support Python 3.15 yet. Use Python 3.12 or 3.13 in a virtual environment:
```
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install pm4py pandas
python analysis/discover_process.py data/sample_events.csv
```
To draw the PNG pictures, also install Graphviz from graphviz.org and tick the option to add it to PATH,
then restart the terminal. Without Graphviz the script still works and says why it could not draw pictures.

## Questions you may be asked
1. **What is a DFG and how do you build it?** Sort each case's events by time, then count every pair of consecutive activities and record the time between them.
2. **How do you detect rework?** An edge that leads back to Registration or Triage from a later step.
3. **Why is X-Ray to Triage a problem?** The patient repeats an intake step and waits again. Using your own run's numbers, say how many patients it affects and how many minutes it adds.
4. **Why two measures (count and time)?** Frequency shows how widespread a path is, time shows how costly it is.
5. **How do you know it is correct?** The edge counts match PM4Py's DFG, and the case and event counts match the dbt `dq_summary` and `explore_logs.py`.
