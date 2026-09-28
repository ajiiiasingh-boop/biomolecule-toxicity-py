"""
scoring.py — how an investigation and the quiz are marked.

Computational thinking: ALGORITHM DESIGN.
grade_case() is the algorithm at the heart of the game. Given a case, the
player's two answers, how many hints they used and which attempt this is, it
follows the same fixed steps every time:

    1. compare the chosen biomolecule with the answer key
    2. compare the chosen mechanism with the answer key
    3. add up the points using SCORE_RULES
    4. if the case is solved, return the explanation and the causal pathway
       if not, return targeted feedback that points back to the evidence

The website and the terminal game both call this one function, so a case can
never be marked differently in the two versions.

Where the answer key lives: this code runs on the server (Streamlit runs your
Python on the server and only sends the finished page to the browser), so the
answer key in data/cases.json is never sent to the player's browser.
"""

from btd.data import PROJECT

# +50 / +50 / -10, exactly as in the project brief, plus two extras.
SCORE_RULES = {
    "correct_biomolecule": PROJECT["score_rules"]["correctBiomolecule"],   # +50
    "correct_mechanism": PROJECT["score_rules"]["correctMechanism"],       # +50
    "hint_penalty": PROJECT["score_rules"]["hintPenalty"],                 # -10
    "first_attempt_bonus": PROJECT["score_rules"]["firstAttemptBonus"],    # +20
    "quiz_correct": PROJECT["score_rules"]["quizCorrect"],                 # +10
}

RULE_TEXT = [
    ("Correct biomolecule", "+50"),
    ("Correct mechanism", "+50"),
    ("Solved on the first attempt", "+20"),
    ("Each hint used", "−10"),
    ("Each correct quiz answer", "+10"),
]

# Used when the answer key has no specific message for a wrong option.
DEFAULT_WRONG = {
    "biomolecule": "That class does not fit the evidence. Re-read the Biomolecule Clue card.",
    "mechanism": "That mechanism does not fit the evidence. Re-read the Experimental Data card.",
}
RIGHT_PART = "Correct — this part of your conclusion stands."


def grade_case(case, biomolecule, mechanism, hints_used=0, attempt=1):
    """Mark one submission for one case and return a result dictionary."""
    solution = case["solution"]

    # Steps 1 and 2: compare each answer with the key (True or False).
    biomolecule_correct = biomolecule == solution["biomolecule"]
    mechanism_correct = mechanism == solution["mechanism"]
    solved = biomolecule_correct and mechanism_correct
    bonus = solved and attempt == 1 and hints_used == 0

    # Step 3: add up the points.
    points = 0
    if biomolecule_correct:
        points += SCORE_RULES["correct_biomolecule"]
    if mechanism_correct:
        points += SCORE_RULES["correct_mechanism"]
    if bonus:
        points += SCORE_RULES["first_attempt_bonus"]
    points += hints_used * SCORE_RULES["hint_penalty"]
    points = max(points, 0)  # the score for a case never goes below zero

    breakdown = [
        ("Biomolecule identified", biomolecule_correct,
         SCORE_RULES["correct_biomolecule"] if biomolecule_correct else 0),
        ("Mechanism identified", mechanism_correct,
         SCORE_RULES["correct_mechanism"] if mechanism_correct else 0),
    ]
    if bonus:
        breakdown.append(("First-attempt bonus", True, SCORE_RULES["first_attempt_bonus"]))
    if hints_used > 0:
        breakdown.append((f"Hints used ({hints_used})", False, hints_used * SCORE_RULES["hint_penalty"]))

    # Step 4: explanation if solved, targeted feedback if not.
    if solved:
        feedback = None
    else:
        feedback = {
            "biomolecule": RIGHT_PART if biomolecule_correct else
            solution["wrongBiomolecule"].get(biomolecule, DEFAULT_WRONG["biomolecule"]),
            "mechanism": RIGHT_PART if mechanism_correct else
            solution["wrongMechanism"].get(mechanism, DEFAULT_WRONG["mechanism"]),
        }

    return {
        "case_id": case["id"],
        "solved": solved,
        "biomolecule_correct": biomolecule_correct,
        "mechanism_correct": mechanism_correct,
        "points": points,
        "breakdown": breakdown,
        "submitted": {"biomolecule": biomolecule, "mechanism": mechanism},
        "verdict": solution["verdict"],
        "explanation": solution["explanation"] if solved else None,
        "pathway": solution["pathway"] if solved else None,
        "key_terms": solution["keyTerms"] if solved else None,
        "feedback": feedback,
    }


def get_hint(case, field):
    """The hint for one question. field is 'biomolecule' or 'mechanism'."""
    return case["solution"]["hints"][field]


def grade_quiz(questions, answers):
    """Mark the quiz. answers maps question id -> chosen option index (or None)."""
    results = []
    for question in questions:
        chosen = answers.get(question["id"])
        results.append({
            "id": question["id"],
            "topic": question["topic"],
            "question": question["question"],
            "options": question["options"],
            "chosen": chosen,
            "answer": question["answer"],
            "correct": chosen == question["answer"],
            "explanation": question["explanation"],
        })

    score = sum(1 for r in results if r["correct"])
    total = len(questions)
    return {
        "score": score,
        "total": total,
        "points": score * SCORE_RULES["quiz_correct"],
        "percentage": round(score / total * 100) if total else 0,
        "results": results,
    }
