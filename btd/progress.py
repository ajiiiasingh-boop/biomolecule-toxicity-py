"""
progress.py — the detective's notebook: score, solved cases, hints, quiz.

The progress is one plain dictionary:

    {
        "score": 170,
        "cases": {"case-01": {"solved": True, "attempts": 1, "hints_used": 0, "points": 120}},
        "quiz": {"score": 7, "total": 10, "points": 70},
    }

Every function here takes that dictionary and updates or reads it. None of
them knows anything about Streamlit or the terminal, which is why both
versions of the game can share them (and why they are easy to test).
"""

from datetime import datetime

from btd.data import CASES, CASE_IDS, mechanism_label


def new_progress():
    """A fresh, empty notebook."""
    return {"score": 0, "cases": {}, "quiz": None}


def case_entry(progress, case_id):
    """The record for one case, created the first time it is needed."""
    if case_id not in progress["cases"]:
        progress["cases"][case_id] = {"solved": False, "attempts": 0, "hints_used": 0, "points": 0}
    return progress["cases"][case_id]


def record_hint(progress, case_id):
    """Count one hint against a case."""
    case_entry(progress, case_id)["hints_used"] += 1


def record_attempt(progress, case_id, result):
    """Store the result of one submission.

    Points are banked only the first time a case is solved, so replaying a
    solved case cannot farm extra score.
    """
    entry = case_entry(progress, case_id)
    entry["attempts"] += 1
    if result["solved"] and not entry["solved"]:
        entry["solved"] = True
        entry["points"] = result["points"]
        progress["score"] += result["points"]
        return True       # newly solved
    return False


def record_quiz(progress, result):
    """Store a quiz result. A retake replaces the previous quiz points."""
    old_points = progress["quiz"]["points"] if progress["quiz"] else 0
    progress["score"] = progress["score"] - old_points + result["points"]
    progress["quiz"] = {"score": result["score"], "total": result["total"], "points": result["points"]}


def summary(progress):
    """Totals for the scoreboard, all computed from the case records."""
    records = progress["cases"].values()
    solved_ids = [cid for cid in CASE_IDS if progress["cases"].get(cid, {}).get("solved")]
    attempts = sum(r["attempts"] for r in records)
    return {
        "score": progress["score"],
        "cases_solved": len(solved_ids),
        "cases_total": len(CASES),
        "solved_ids": solved_ids,
        "hints_used": sum(r["hints_used"] for r in records),
        "attempts": attempts,
        "accuracy": round(len(solved_ids) / attempts * 100) if attempts else None,
        "all_solved": len(solved_ids) == len(CASES),
        "quiz": progress["quiz"],
    }


def is_solved(progress, case_id):
    return progress["cases"].get(case_id, {}).get("solved", False)


def next_unsolved(progress):
    """The first case not yet solved, or None when every case is closed."""
    for case_id in CASE_IDS:
        if not is_solved(progress, case_id):
            return case_id
    return None


def make_report(progress, name=""):
    """A plain-text case report the player can download and keep."""
    s = summary(progress)
    lines = [
        "BIOMOLECULE TOXICITY DETECTIVE — CASE REPORT",
        "Educational simulation. All cases and data are simulated.",
        f"Generated: {datetime.now():%d %b %Y, %H:%M}",
    ]
    if name:
        lines.append(f"Detective: {name}")
    lines += [
        "",
        f"Detective score : {s['score']}",
        f"Cases solved    : {s['cases_solved']} / {s['cases_total']}",
        f"Hints used      : {s['hints_used']}",
        f"Attempts        : {s['attempts']}",
    ]
    if s["quiz"]:
        lines.append(f"Quiz            : {s['quiz']['score']} / {s['quiz']['total']}")
    lines += ["", "CASE RECORD"]
    for case in CASES:
        record = progress["cases"].get(case["id"])
        if record and record["solved"]:
            status = f"SOLVED  +{record['points']} pts  ({mechanism_label(case['solution']['mechanism'])})"
        elif record:
            status = f"open    {record['attempts']} attempt(s)"
        else:
            status = "not started"
        lines.append(f"  Case {case['number']}  {case['title']:<28} {status}")
    return "\n".join(lines) + "\n"
