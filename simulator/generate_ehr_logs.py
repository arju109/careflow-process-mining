"""
CareFlow - Week 1: EHR event log simulator.

Generates mock Emergency Room event logs with deliberate inefficiencies:
  * ~40% of X-Ray patients are sent BACK to Triage (missing paperwork form)
  * Longer waits during peak hours (09:00-12:00, 17:00-20:00)
  * A few non-compliant paths (skipped Triage, double X-Ray)
  * Optional --dirty flag adds messy data for the dbt cleaning phase

Usage:
    python generate_ehr_logs.py --cases 5000 --days 30 --out raw_ehr_events.csv
    python generate_ehr_logs.py --cases 5000 --dirty --out raw_ehr_events_dirty.csv
"""
import argparse
import csv
import random
from datetime import datetime, timedelta

DOCTORS = ["Dr. Rao", "Dr. Mehta", "Dr. Iyer", "Dr. Khan", "Dr. Singh"]
TRIAGE_NURSES = ["Nurse A", "Nurse B", "Nurse C"]
RADIOLOGISTS = ["Rad Tech 1", "Rad Tech 2"]
LAB_STAFF = ["Lab Tech 1", "Lab Tech 2"]
FRONT_DESK = ["Desk 1", "Desk 2"]

LOOPBACK_PROB = 0.40      # X-Ray -> Triage (missing form)
XRAY_PROB = 0.60
LAB_PROB = 0.30
SKIP_TRIAGE_PROB = 0.03   # non-compliant path
DOUBLE_XRAY_PROB = 0.02   # non-compliant path
ADMIT_PROB = 0.15


def is_peak(ts):
    return 9 <= ts.hour < 12 or 17 <= ts.hour < 20


def wait(mean_min, ts, sd_ratio=0.4):
    """Random wait in minutes, longer at peak hours."""
    factor = 1.6 if is_peak(ts) else 1.0
    m = max(1.0, random.gauss(mean_min * factor, mean_min * sd_ratio))
    return timedelta(minutes=m)


def random_arrival(start, days):
    day = start + timedelta(days=random.randrange(days))
    # arrivals weighted toward peak hours
    hour = random.choices(range(24), weights=[
        1, 1, 1, 1, 1, 2, 3, 5, 7, 9, 9, 8, 6, 5, 5, 6, 7, 9, 9, 8, 6, 4, 3, 2])[0]
    return day.replace(hour=hour, minute=random.randrange(60), second=random.randrange(60))


def build_case(case_id, start, days):
    age = int(min(95, max(1, random.gauss(42, 22))))
    gender = random.choice(["M", "F"])
    severity = random.choices(["Low", "Medium", "High"], weights=[50, 35, 15])[0]
    doctor = random.choice(DOCTORS)

    t = random_arrival(start, days)
    events = []

    def add(activity, resource):
        events.append({
            "case_id": case_id, "activity": activity,
            "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
            "resource": resource, "patient_age": age,
            "patient_gender": gender, "severity": severity,
            "doctor": doctor,
        })

    add("Registration", random.choice(FRONT_DESK))
    t += wait(6, t)

    if random.random() > SKIP_TRIAGE_PROB:
        add("Triage", random.choice(TRIAGE_NURSES))
        t += wait(15, t)

    add("Doctor Consultation", doctor)
    t += wait(20, t)

    if random.random() < XRAY_PROB:
        add("X-Ray", random.choice(RADIOLOGISTS))
        t += wait(25, t)
        if random.random() < DOUBLE_XRAY_PROB:
            add("X-Ray", random.choice(RADIOLOGISTS))
            t += wait(25, t)
        if random.random() < LOOPBACK_PROB:
            # bottleneck: missing paperwork form sends patient back
            add("Triage", random.choice(TRIAGE_NURSES))
            t += wait(30, t, sd_ratio=0.5)
            add("Doctor Consultation", doctor)
            t += wait(15, t)
    elif random.random() < LAB_PROB:
        add("Lab Test", random.choice(LAB_STAFF))
        t += wait(35, t)
        add("Doctor Consultation", doctor)
        t += wait(15, t)

    add("Treatment", doctor)
    t += wait(30, t)
    add("Admission" if random.random() < ADMIT_PROB else "Discharge",
        random.choice(FRONT_DESK))
    return events


def make_dirty(rows):
    """Inject realistic mess so the dbt cleaning phase has real work."""
    out = []
    for r in rows:
        r = dict(r)
        x = random.random()
        if x < 0.02:
            r["activity"] = r["activity"].upper()
        elif x < 0.04:
            r["activity"] = " " + r["activity"].lower() + " "
        elif x < 0.05:
            r["timestamp"] = ""            # missing timestamp
        elif x < 0.06:
            r["case_id"] = ""              # missing case id
        elif x < 0.07:
            r["timestamp"] = datetime.strptime(
                r["timestamp"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        out.append(r)
        if random.random() < 0.02:         # duplicate row
            out.append(dict(r))
    random.shuffle(out)
    return out


def main():
    p = argparse.ArgumentParser(description="CareFlow EHR event log simulator")
    p.add_argument("--cases", type=int, default=5000)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--start", default="2026-09-01", help="YYYY-MM-DD")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--dirty", action="store_true", help="add messy data")
    p.add_argument("--out", default="raw_ehr_events.csv")
    a = p.parse_args()

    random.seed(a.seed)
    start = datetime.strptime(a.start, "%Y-%m-%d")
    rows = []
    for i in range(1, a.cases + 1):
        rows.extend(build_case(f"P{i:06d}", start, a.days))

    rows.sort(key=lambda r: (r["timestamp"], r["case_id"]))
    if a.dirty:
        rows = make_dirty(rows)

    fields = ["case_id", "activity", "timestamp", "resource",
              "patient_age", "patient_gender", "severity", "doctor"]
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} events for {a.cases} cases -> {a.out}")


if __name__ == "__main__":
    main()
