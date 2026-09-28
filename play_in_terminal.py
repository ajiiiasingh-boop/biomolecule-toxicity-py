"""
BIOMOLECULE TOXICITY DETECTIVE — terminal edition
=================================================

The same game as the website, using nothing but plain Python:
print(), input(), loops, if/else, lists, dictionaries and functions.
No libraries to install. Run it with:

    python play_in_terminal.py

It reads the SAME data files and uses the SAME grading code as the website
(btd/data.py, btd/scoring.py, btd/progress.py). Only the screen is different.
That is decomposition and abstraction at work: the logic does not care
whether it is shown in a browser or in a terminal.
"""

import sys
import textwrap

from btd import progress as prog
from btd.data import (BIOMOLECULES, CASES, DISCLAIMER, QUIZ, evidence_datasets, option_label)
from btd.scoring import RULE_TEXT, get_hint, grade_case, grade_quiz

WIDTH = 78
BAR_WIDTH = 40

# Some consoles cannot print symbols like µ or ²⁺; replace them instead of crashing.
try:
    sys.stdout.reconfigure(errors="replace")
except (AttributeError, ValueError):
    pass


# ---------------------------------------------------------------------------
# Printing helpers
# ---------------------------------------------------------------------------
def say(text="", indent=0):
    """Print text wrapped to the screen width, keeping blank lines between paragraphs."""
    if not text:
        print()
        return
    for paragraph in text.split("\n\n"):
        print(textwrap.fill(paragraph, WIDTH, initial_indent=" " * indent,
                            subsequent_indent=" " * indent))
        if "\n\n" in text:
            print()


def rule(character="-"):
    print(character * WIDTH)


def heading(text):
    print()
    rule("=")
    print(text.upper())
    rule("=")


def ask(prompt):
    """input() that exits politely if the player presses Ctrl+C or Ctrl+D."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye, detective.")
        sys.exit(0)


def choose(prompt, count, letters=""):
    """Keep asking until the player types a number from 1 to count (or one of the letters).

    Returns an index (0, 1, 2 ...) for a number, or the letter itself.
    """
    while True:
        answer = ask(prompt).lower()
        if answer and answer in letters.lower():
            return answer
        if answer.isdigit() and 1 <= int(answer) <= count:
            return int(answer) - 1
        print(f"  Please type a number from 1 to {count}"
              + (f" or one of: {', '.join(letters)}" if letters else "") + ".")


# ---------------------------------------------------------------------------
# Showing the evidence
# ---------------------------------------------------------------------------
def ascii_chart(dataset):
    """Draw a dataset as text bars:   High      ███████████▌ 240"""
    print()
    say(dataset["title"].upper())
    print(f"  ({dataset['yLabel']}, SIMULATED EDUCATIONAL DATA)")
    top = dataset["yMax"]
    for series in dataset["series"]:
        print(f"\n  {series['key']}")
        for row in dataset["rows"]:
            value = row[series["key"]]
            length = round(value / top * BAR_WIDTH)
            print(f"    {row[dataset['xKey']]:<8} {'█' * length} {value:g}")


def show_evidence(case, evidence):
    heading(f"Evidence {evidence['id']} · {evidence['kind']}")
    say(evidence["title"].upper())
    print()
    say(evidence["body"])
    print()
    symbols = {"alert": "!!", "normal": "ok", "info": "--"}
    for readout in evidence["readouts"]:
        print(f"  [{symbols[readout['state']]}] {readout['label']}: {readout['value']}")
    for dataset in evidence_datasets(case, evidence):
        ascii_chart(dataset)
    print()
    ask("Press Enter to go back to the evidence board... ")


# ---------------------------------------------------------------------------
# One investigation
# ---------------------------------------------------------------------------
def ask_question(case, field, number, hints, notebook):
    """Ask Q1 or Q2. Typing h buys the hint (−10 points)."""
    question = case["questions"][field]
    options = question["options"]
    print()
    print(f"Q{number}. {question['prompt']}")
    for i, option in enumerate(options, start=1):
        print(f"   {i}. {option_label(field, option)}")
    if field not in hints:
        print("   h. Use a hint (-10 points)")
    while True:
        picked = choose("Your answer: ", len(options), "" if field in hints else "h")
        if picked == "h":
            hints[field] = get_hint(case, field)
            prog.record_hint(notebook, case["id"])
            print()
            say("HINT: " + hints[field], indent=2)
            print()
        else:
            return options[picked]


def show_result(case, result):
    if result["solved"]:
        heading(f"Case solved · +{result['points']} points")
        say(result["verdict"])
        print()
        say(result["explanation"])
        print("CAUSAL PATHWAY")
        for number, step in enumerate(result["pathway"], start=1):
            print(f"  {number}. {step}")
            if number < len(result["pathway"]):
                print("     ↓")
        print("\nKEY TERMS")
        for term in result["key_terms"]:
            say(f"{term['term']}: {term['def']}", indent=2)
    else:
        heading("Not quite")
        say("Part of your conclusion does not fit the evidence. Nothing is lost — "
            "go back and look again.")
        for field in ("biomolecule", "mechanism"):
            mark = "CORRECT" if result[f"{field}_correct"] else "WRONG"
            print(f"\n  {field.capitalize()}: {option_label(field, result['submitted'][field])} [{mark}]")
            say(result["feedback"][field], indent=4)
    print()
    for label, _, points in result["breakdown"]:
        print(f"  {label:<28} {points:+d}")


def investigate(case, notebook):
    heading(f"Case {case['number']} · {case['title']}")
    print(f"Specimen: {case['specimen']}")
    print(f"Exposure: {case['exposure']}")
    print(f"Duration: {case['duration']}")
    print()
    say(case["brief"])

    opened = []
    hints = {}
    attempt = 1
    letters = [e["id"] for e in case["evidence"]]

    while True:
        print()
        rule()
        print(f"EVIDENCE BOARD   discovered {len(opened)}/{len(letters)}")
        for evidence in case["evidence"]:
            status = evidence["title"] if evidence["id"] in opened else "sealed"
            print(f"  {evidence['id']}. {evidence['kind']:<22} {status}")
        can_answer = len(opened) == len(letters)
        print("  S. Submit a conclusion" if can_answer else "  (open all four cards to submit)")
        print("  Q. Back to the main menu")
        choice = ask("Open which card? ").upper()

        if choice == "Q":
            return
        if choice in letters:
            if choice not in opened:
                opened.append(choice)
            show_evidence(case, case["evidence"][letters.index(choice)])
        elif choice == "S" and can_answer:
            biomolecule = ask_question(case, "biomolecule", 1, hints, notebook)
            mechanism = ask_question(case, "mechanism", 2, hints, notebook)
            result = grade_case(case, biomolecule, mechanism, hints_used=len(hints), attempt=attempt)
            prog.record_attempt(notebook, case["id"], result)
            show_result(case, result)
            if result["solved"]:
                ask("\nPress Enter to return to the main menu... ")
                return
            attempt += 1
            ask("\nPress Enter to try again... ")
        else:
            print("  Type a card letter (A–D), S or Q.")


# ---------------------------------------------------------------------------
# Quiz, database and score
# ---------------------------------------------------------------------------
def play_quiz(notebook):
    heading("Quiz")
    answers = {}
    for number, question in enumerate(QUIZ, start=1):
        print(f"\n{number}. [{question['topic']}]")
        say(question["question"])
        for i, option in enumerate(question["options"], start=1):
            print(f"   {i}. {option}")
        answers[question["id"]] = choose("Your answer: ", len(question["options"]))
    result = grade_quiz(QUIZ, answers)
    prog.record_quiz(notebook, result)
    heading(f"Quiz score: {result['score']}/{result['total']} (+{result['points']} points)")
    for number, r in enumerate(result["results"], start=1):
        if not r["correct"]:
            print(f"\n{number}. Correct answer: {r['options'][r['answer']]}")
            say(r["explanation"], indent=3)
    ask("\nPress Enter to return to the main menu... ")


def show_database():
    heading("Biomolecule database")
    for i, b in enumerate(BIOMOLECULES, start=1):
        print(f"  {i}. {b['label']}")
    b = BIOMOLECULES[choose("Which one? ", len(BIOMOLECULES))]
    heading(b["label"])
    say(b["tagline"])
    print()
    print(f"Built from: {b['builtFrom']}")
    print(f"Key job:    {b['keyJob']}")
    print()
    say(b["summary"])
    print("\nHOW TOXICITY HITS IT")
    for hit in b["howToxicityHits"]:
        say(f"- {hit['title']}: {hit['body']}", indent=2)
    print("\nMARKERS: " + ", ".join(b["markers"]))
    ask("\nPress Enter to return to the main menu... ")


def show_score(notebook):
    heading("Case report")
    print(prog.make_report(notebook))
    print("SCORING RULES")
    for label, value in RULE_TEXT:
        print(f"  {label:<30} {value}")
    ask("\nPress Enter to return to the main menu... ")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------
def main():
    notebook = prog.new_progress()
    heading("Biomolecule Toxicity Detective · terminal edition")
    say("Something has gone wrong inside the cell. Follow the evidence. Identify the "
        "biomolecule. Solve the toxicity case.")
    print()
    say(DISCLAIMER)

    while True:
        summary = prog.summary(notebook)
        print()
        rule("=")
        print(f"MAIN MENU    score {summary['score']}    solved "
              f"{summary['cases_solved']}/{summary['cases_total']}")
        rule("=")
        for i, case in enumerate(CASES, start=1):
            done = "  [solved]" if prog.is_solved(notebook, case["id"]) else ""
            print(f"  {i}. Case {case['number']} · {case['title']} ({case['difficulty']}){done}")
        print("  7. Take the quiz")
        print("  8. Biomolecule database")
        print("  9. Case report and score")
        print("  0. Quit")
        choice = ask("Choose: ")

        if choice in ("1", "2", "3", "4", "5", "6"):
            investigate(CASES[int(choice) - 1], notebook)
        elif choice == "7":
            play_quiz(notebook)
        elif choice == "8":
            show_database()
        elif choice == "9":
            show_score(notebook)
        elif choice == "0":
            print(f"\nFinal score: {notebook['score']}. Goodbye, detective.")
            break
        else:
            print("  Please type a number from 0 to 9.")


if __name__ == "__main__":
    main()
