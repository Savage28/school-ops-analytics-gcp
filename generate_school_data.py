"""
generate_school_data.py
Phase 1 of the School Operations Analytics Pipeline (BigQuery portfolio project).

Generates FAKE, realistic middle-school data with deliberate messiness so the
BigQuery cleaning step has real problems to solve. No real student data.

Output (./data/):
  students.csv            - roster (1 row per student, with some duplicates)
  attendance.csv          - daily attendance for one school year
  behavior.csv            - merit / demerit incidents
  assessments.csv         - one row per student per assessment (total score)
  assessment_responses.csv- item-level responses (one row per student per question)

Run:  python generate_school_data.py
Only uses the Python standard library.
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)  # same data every run, so results are reproducible

OUT_DIR = "data"
NUM_STUDENTS = 500
GRADES = [5, 6, 7, 8]
HOMEROOM_LETTERS = ["A", "B", "C", "D"]
SCHOOL_START = date(2025, 9, 4)
SCHOOL_END = date(2026, 6, 25)
QUESTIONS_PER_TEST = 20

FIRST_NAMES = ["Aaliyah", "Amir", "Ava", "Brandon", "Camila", "Carlos", "Chloe",
               "Daniel", "Destiny", "Elijah", "Emily", "Fatima", "Gabriel", "Grace",
               "Isaiah", "Jada", "Jayden", "Kevin", "Layla", "Liam", "Malik", "Maria",
               "Mason", "Mia", "Nia", "Noah", "Olivia", "Omar", "Priya", "Sofia",
               "Tyler", "Valentina", "Xavier", "Yasmin", "Zion"]
LAST_NAMES = ["Adams", "Ali", "Brown", "Chen", "Diaz", "Edwards", "Garcia", "Johnson",
              "Kim", "Lopez", "Martinez", "Nguyen", "Okafor", "Patel", "Robinson",
              "Rodriguez", "Smith", "Thomas", "Walker", "Williams", "Wilson", "Young"]

BEHAVIOR_TYPES = {
    "merit": ["On-task participation", "Helping a peer", "Leadership", "Homework complete"],
    "demerit": ["Late to class", "Off-task", "Uniform violation", "Disruption", "Missing homework"],
}

ASSESSMENTS = [
    ("ELA Interim 1", "ELA", date(2025, 10, 15)),
    ("Math Interim 1", "Math", date(2025, 12, 10)),
    ("ELA Interim 2", "ELA", date(2026, 3, 18)),
]


# ---------- "Mess" helpers: make the data look like real exports ----------

def messy_id(student_id: int) -> str:
    """Return the ID in one of several inconsistent formats."""
    r = random.random()
    if r < 0.80:
        return str(student_id)            # clean: 100234
    if r < 0.88:
        return f"S{student_id}"           # prefixed: S100234
    if r < 0.94:
        return f" {student_id} "          # stray spaces
    return f"{student_id}.0"              # float-ified by a spreadsheet


def messy_status(status: str) -> str:
    """Attendance codes with inconsistent casing / wording."""
    variants = {
        "Present": ["Present", "present", "P", "PRESENT"],
        "Absent": ["Absent", "absent", "A", "ABS"],
        "Tardy": ["Tardy", "tardy", "T", "Late"],
    }
    return random.choice(variants[status]) if random.random() < 0.15 else status


def messy_date(d: date) -> str:
    """Most dates ISO, some in US format like many SIS exports."""
    return d.isoformat() if random.random() < 0.9 else d.strftime("%m/%d/%Y")


def school_days(start: date, end: date):
    """Weekdays only, skipping a winter and spring break."""
    breaks = [(date(2025, 12, 22), date(2026, 1, 2)),
              (date(2026, 4, 3), date(2026, 4, 10))]
    d = start
    while d <= end:
        on_break = any(b0 <= d <= b1 for b0, b1 in breaks)
        if d.weekday() < 5 and not on_break:
            yield d
        d += timedelta(days=1)


def write_csv(name, header, rows):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name:<26} {len(rows):>7,} rows")


# ---------- Generators ----------

def make_students():
    students = []
    for i in range(NUM_STUDENTS):
        sid = 100000 + i
        grade = random.choice(GRADES)
        students.append({
            "id": sid,
            "first": random.choice(FIRST_NAMES),
            "last": random.choice(LAST_NAMES),
            "grade": grade,
            "homeroom": f"{grade}{random.choice(HOMEROOM_LETTERS)}",
            "ell": random.random() < 0.15,
            # hidden traits that drive patterns (so analysis finds real insights)
            "absence_rate": random.betavariate(1.5, 18),   # most ~5-10%, a few high
            "ability": random.gauss(0, 1),
        })
    return students


def students_rows(students):
    rows = []
    for s in students:
        grade = s["grade"]
        r = random.random()
        if r < 0.03:
            grade = ""                     # missing grade
        elif r < 0.10:
            grade = f"Grade {grade}"       # text instead of number
        rows.append([messy_id(s["id"]), s["first"], s["last"], grade,
                     s["homeroom"], "Y" if s["ell"] else "N"])
    # duplicate ~2% of roster rows (re-exports, double enrollment entries)
    rows += random.sample(rows, k=int(len(rows) * 0.02))
    random.shuffle(rows)
    return rows


def attendance_rows(students):
    rows = []
    for d in school_days(SCHOOL_START, SCHOOL_END):
        for s in students:
            r = random.random()
            if r < s["absence_rate"]:
                status = "Absent"
            elif r < s["absence_rate"] + 0.04:
                status = "Tardy"
            else:
                status = "Present"
            rows.append([messy_id(s["id"]), messy_date(d), messy_status(status)])
    # some duplicate scans
    rows += random.sample(rows, k=int(len(rows) * 0.005))
    return rows


def behavior_rows(students, days):
    rows = []
    incident_id = 1
    for s in students:
        # students who miss more school tend to get more demerits
        n_merits = max(0, int(random.gauss(12 + 4 * s["ability"], 4)))
        n_demerits = max(0, int(random.gauss(6 + 60 * s["absence_rate"], 3)))
        for kind, n in (("merit", n_merits), ("demerit", n_demerits)):
            for _ in range(n):
                points = 1 if kind == "merit" else -1
                # some points stored as text, like "1 pt"
                pts_value = f"{points} pt" if random.random() < 0.05 else points
                rows.append([incident_id, messy_id(s["id"]), messy_date(random.choice(days)),
                             kind, random.choice(BEHAVIOR_TYPES[kind]), pts_value])
                incident_id += 1
    return rows


def assessment_rows(students):
    totals, responses = [], []
    answer_choices = ["A", "B", "C", "D"]
    for name, subject, test_date in ASSESSMENTS:
        answer_key = [random.choice(answer_choices) for _ in range(QUESTIONS_PER_TEST)]
        difficulty = [random.gauss(0, 0.8) for _ in range(QUESTIONS_PER_TEST)]
        for s in students:
            if random.random() < 0.04:
                continue                   # absent on test day, no record
            # chronic absence lowers performance -> a real, findable insight
            skill = s["ability"] - 6 * s["absence_rate"]
            correct = 0
            for q in range(QUESTIONS_PER_TEST):
                p = 1 / (1 + 2.718 ** -(skill - difficulty[q] + 0.6))
                if random.random() < p:
                    ans, is_right = answer_key[q], 1
                else:
                    ans = random.choice([c for c in answer_choices if c != answer_key[q]])
                    is_right = 0
                if random.random() < 0.01:
                    ans = ""               # blank / skipped
                    is_right = 0
                correct += is_right
                responses.append([messy_id(s["id"]), name, f"Q{q + 1}", ans,
                                  answer_key[q], is_right])
            pct = round(100 * correct / QUESTIONS_PER_TEST, 1)
            score = f"{pct}%" if random.random() < 0.08 else pct   # some as "85.0%"
            totals.append([messy_id(s["id"]), name, subject, messy_date(test_date),
                           correct, QUESTIONS_PER_TEST, score])
    return totals, responses


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    students = make_students()
    days = list(school_days(SCHOOL_START, SCHOOL_END))
    print(f"Generating fake data for {NUM_STUDENTS} students, {len(days)} school days...")

    write_csv("students.csv",
              ["student_id", "first_name", "last_name", "grade", "homeroom", "ell_status"],
              students_rows(students))
    write_csv("attendance.csv",
              ["student_id", "date", "status"],
              attendance_rows(students))
    write_csv("behavior.csv",
              ["incident_id", "student_id", "date", "type", "description", "points"],
              behavior_rows(students, days))
    totals, responses = assessment_rows(students)
    write_csv("assessments.csv",
              ["student_id", "assessment", "subject", "test_date",
               "num_correct", "num_questions", "score_pct"],
              totals)
    write_csv("assessment_responses.csv",
              ["student_id", "assessment", "question", "student_answer",
               "correct_answer", "is_correct"],
              responses)
    print(f"Done. Files saved in ./{OUT_DIR}/")


if __name__ == "__main__":
    main()
