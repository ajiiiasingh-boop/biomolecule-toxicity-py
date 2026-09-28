"""
data.py — loads the biology knowledge from the JSON files in data/.

Computational thinking: ABSTRACTION.
Every case, biomolecule, mechanism, toxin and quiz question is stored as DATA
(a JSON file), not as code. A case is just a dictionary with the same keys
every time: title, brief, four evidence cards, datasets, questions, solution.
Because every case has the same shape, one piece of code can display and
grade all six of them. Adding a seventh case means adding data, not code.

Only the standard library is used (json + pathlib), so this file works on any
computer with Python installed, even without pip.
"""

import json
from pathlib import Path

# The data/ folder sits next to the btd/ folder.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load(name):
    """Read data/<name>.json and return it as Python lists and dictionaries."""
    path = DATA_DIR / f"{name}.json"
    with open(path, encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------------------------
# Load everything once, when the module is first imported.
# ---------------------------------------------------------------------------
PROJECT = load("project")                 # name, version, disclaimer, score rules
BIOMOLECULES = load("biomolecules")       # list of 4 biomolecule classes
MECHANISMS = load("mechanisms")           # list of 8 mechanisms (6 are case answers)
CASES = load("cases")                     # list of 6 investigation cases
TOXIN_CATEGORIES = load("toxins")         # list of 4 toxin categories
MECHANISM_MAP = load("mechanism_map")     # the 5-stage exposure-to-effect chain
CELL_MAP = load("cell_map")               # cell parts + the route each mechanism takes
QUIZ = load("quiz")                       # list of 10 quiz questions

DISCLAIMER = PROJECT["disclaimer"]

# ---------------------------------------------------------------------------
# Lookup dictionaries: id -> record.
# Searching a list means checking items one by one. Building a dictionary once
# means every later lookup is instant: BIOMOLECULE_BY_ID["protein"].
# ---------------------------------------------------------------------------
BIOMOLECULE_BY_ID = {b["id"]: b for b in BIOMOLECULES}
MECHANISM_BY_ID = {m["id"]: m for m in MECHANISMS}
CASE_BY_ID = {c["id"]: c for c in CASES}
CELL_PART_BY_ID = {p["id"]: p for p in CELL_MAP["parts"]}
CASE_IDS = [c["id"] for c in CASES]


def get_case(case_id):
    """Return the case dictionary for an id such as 'case-01' (None if unknown)."""
    return CASE_BY_ID.get(case_id)


def biomolecule_label(biomolecule_id):
    """'protein' -> 'Proteins & Enzymes'."""
    record = BIOMOLECULE_BY_ID.get(biomolecule_id)
    return record["label"] if record else biomolecule_id


def mechanism_label(mechanism_id):
    """'enzyme-inhibition' -> 'Enzyme inhibition'."""
    record = MECHANISM_BY_ID.get(mechanism_id)
    return record["label"] if record else mechanism_id


def option_label(field, option_id):
    """Label for an answer option. field is 'biomolecule' or 'mechanism'."""
    if field == "biomolecule":
        return biomolecule_label(option_id)
    return mechanism_label(option_id)


def get_dataset(case, dataset_id):
    """Find one dataset inside a case by its id (None if the id is missing)."""
    for dataset in case["datasets"]:
        if dataset["id"] == dataset_id:
            return dataset
    return None


def evidence_datasets(case, evidence):
    """All datasets attached to one evidence card (most cards have none or one)."""
    found = []
    for key in ("datasetId", "secondaryDatasetId"):
        dataset_id = evidence.get(key)
        if dataset_id:
            dataset = get_dataset(case, dataset_id)
            if dataset is not None:
                found.append(dataset)
    return found


def answer_mechanisms():
    """The mechanisms that are the correct answer to at least one case.

    A set removes duplicates automatically, and the list comprehension keeps
    the original order of MECHANISMS.
    """
    used = {case["solution"]["mechanism"] for case in CASES}
    return [m for m in MECHANISMS if m["id"] in used]


def toxin_entry_count():
    """How many individual toxins the library describes."""
    return sum(len(category["entries"]) for category in TOXIN_CATEGORIES)
