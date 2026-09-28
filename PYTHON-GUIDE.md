# Python guide — how the code works (for the CT + Bio presentation)

## 1. The idea in one paragraph

The **biology** is the content: four biomolecule classes, six mechanisms of toxic damage, six
cases, each with evidence and a dose–response dataset. The **computational thinking** is how that
content is turned into a program: the problem is decomposed into modules, each case is abstracted
into one data format, patterns in the data are detected with NumPy, and one algorithm marks every
answer the same way. **Python** does all of it: Streamlit turns the Python into web pages, Pandas
handles the tables, NumPy does the maths and Matplotlib draws the pictures.

## 2. How a click becomes a page

Streamlit runs a page's Python file **from top to bottom every time the user clicks something**.

1. You click *Evidence B*.
2. Streamlit re-runs `views/investigation.py`.
3. `st.button(...)` now returns `True`, so the code adds `"B"` to the list of opened cards.
4. The page is drawn again with card B open.

Anything that must survive a re-run (score, opened cards, hints) is stored in
`st.session_state`, a dictionary that belongs to one visitor's browser tab.

## 3. The four computational-thinking pillars in this project

| Pillar | Where to point in the code | What to say |
|---|---|---|
| **Decomposition** | the folders `data/`, `btd/`, `views/`, `tests/`; `btd/__init__.py` | One big problem split into small modules with one job each: load data, grade, keep score, analyse, draw, show. |
| **Pattern recognition** | `describe_trend()`, `percent_change()`, `dose_correlation()` in `btd/analysis.py` | Every case hides its answer in the direction the numbers move. NumPy measures the change from control, checks every step (`np.diff`) and computes the correlation with dose. |
| **Abstraction** | `data/cases.json`, `btd/data.py` | A case is one dictionary with the same keys every time. One set of code runs all six cases; a seventh case needs new data, not new code. |
| **Algorithm design** | `grade_case()` in `btd/scoring.py`; the flowchart on the Python Lab page | Fixed steps: compare answer 1, compare answer 2, add points, then explain (if right) or send back to the evidence (if wrong). |

## 4. Python concepts used, and where

| Concept | Example in the project |
|---|---|
| Variables, strings, f-strings | everywhere, e.g. `f"Case {case['number']}"` |
| Lists and list indexing | `board["opened"]`, `case["evidence"][0]` |
| Dictionaries | every case, the progress notebook, `SCORE_RULES` |
| Sets | `answer_mechanisms()` in `btd/data.py` removes duplicates |
| Tuples | `(words, arrow)` returned by `describe_trend()` |
| `if / elif / else` | `grade_case()`, the menus in `play_in_terminal.py` |
| `for` loops, `enumerate`, `zip` | drawing the evidence cards: `for column, evidence in zip(...)` |
| `while` loops | `choose()` keeps asking until the input is valid |
| Functions, parameters, default values, `return` | `grade_case(case, biomolecule, mechanism, hints_used=0, attempt=1)` |
| List / dictionary comprehensions | `BIOMOLECULE_BY_ID = {b["id"]: b for b in BIOMOLECULES}` |
| `lambda` | `format_func=lambda cid: ...` for button labels |
| Recursion | `tree_lines()` in `views/python_lab.py` draws the folder tree |
| Modules and `import` | `from btd.scoring import grade_case` |
| File handling | `open(...)` + `json.load` in `btd/data.py`; CSV / TXT downloads |
| Exceptions (`try / except`) | `ask()` in `play_in_terminal.py`, `run.py` |
| Testing | `tests/` — 41 checks with `unittest` |

## 5. The libraries, with one line each

```python
import numpy as np
change = (values / values[0] - 1) * 100          # % change for the whole array at once
steps = np.diff(values)                          # rise or fall between neighbouring doses
r = np.corrcoef(np.arange(len(values)), values)[0, 1]   # link with dose, -1 to +1

import pandas as pd
table = pd.DataFrame(rows)                       # the toxin library as a table
table[table["target_id"].isin(["lipid"])]        # filter with a boolean mask
table.groupby("Target").size()                   # how many toxins hit each class

from matplotlib.figure import Figure
fig = Figure(); ax = fig.subplots()
ax.plot(x, values, marker="o")                   # evidence charts
ax.errorbar(x, values, yerr=sd)                  # error bars from simulated replicates

import streamlit as st
if st.button("Submit conclusion"):               # a button is just an if-statement
    result = grade_case(case, bio, mech)
```

**Simulated replicates (NumPy).** Real experiments are repeated three times and never give the
same number twice. `simulate_replicates()` draws random noise with `np.random.default_rng`,
then subtracts the average noise of each group, so the three replicates always average to
exactly the value in the case file. The error bars therefore add realism without changing the
biology.

## 6. Walking through the grading algorithm

```text
grade_case(case, "protein", "enzyme-inhibition", hints_used=1, attempt=1)

1. biomolecule_correct = "protein" == "protein"                     -> True   (+50)
2. mechanism_correct   = "enzyme-inhibition" == "enzyme-inhibition" -> True   (+50)
3. solved on attempt 1 with no hints?  no, 1 hint used               -> no bonus
4. hint penalty 1 x -10                                              -> -10
5. points = max(90, 0)                                               -> 90
6. solved -> return the explanation, the causal pathway and key terms
```

If an answer is wrong, step 6 instead looks up the message for *that specific wrong option*
(`wrongBiomolecule` / `wrongMechanism` in the case file), for example: "Check the direction of the
substrate curve in Evidence B. It rises to 240% of control. Depletion would send it down, not up."

## 7. Likely viva questions

**Why Streamlit and not HTML/CSS/JS?**
So the whole project is in one language we have learned. Streamlit turns Python calls like
`st.button()` and `st.dataframe()` into a web page, so we could spend our time on the logic and the
biology.

**Where is the data stored?**
In JSON files in `data/`. `btd/data.py` reads them once with `json.load` and builds dictionaries
for instant lookup by id.

**Can a player cheat by looking at the answers in the browser?**
No. Streamlit runs the Python on the server and sends only the finished page. The answer key is
read only by `grade_case()`, which runs on the server.

**Are the numbers real?**
No. They are simulated, but built to behave like real dose–response data (the right markers moving
in the right direction), and every chart is labelled SIMULATED EDUCATIONAL DATA.

**What does NumPy do that a loop could not?**
A loop could do the same, but NumPy works on the whole array at once (`values / values[0]`), which
is shorter, faster and closer to the maths.

**What is a DataFrame?**
A table with named columns. We use it to show datasets, to filter the toxin library with
conditions, to count toxins per biomolecule with `groupby`, and to export the case record as CSV.

**Why are the error bars there?**
To show that real measurements vary. They come from three simulated replicates whose mean equals
the case value exactly.

**What does the terminal version prove?**
That the logic is separate from the screen. The terminal game uses the same `btd` engine with only
`print()` and `input()`, and needs no libraries at all.

**How do you know it works?**
41 automated tests (`python -m unittest`) check the data, the grading, the score rules, the
analysis, the real-data results (Tox21 counts, LD50 comparison), that every chart draws, that
every page loads, and a full play-through of Case 01.

**How is the score protected from farming?**
`record_attempt()` banks a case's points only the first time it is solved, and a quiz retake
replaces the earlier quiz points instead of adding to them.

**Where did the real data come from? (Data Lab)**
Tox21 from Kaggle (`epicskills/tox21-dataset`, downloaded with `kagglehub` or the Download button),
originally from the Tox21 Data Challenge run by NIH, EPA and FDA. The LD50 values come from
LDToxDB (rat oral LD50, compiled from NIH CATMoS, EPA TEST and NTP). `scripts/get_data.py`
downloads both.

**Tox21 has no LD50. How could you compare the averages?**
We matched every Tox21 compound to the LD50 dataset by chemical structure: RDKit turns each SMILES
into an InChIKey, and compounds with the same key are the same chemical. 3,831 compounds matched.

**How many are toxic, and is there a difference?**
2,872 of 7,831 (36.7%) are active in at least one assay; 4,959 are not. The toxic group's average
−log(LD50) is 2.39 against 2.09, so about 2 times more toxic. Yes, there is a visible difference,
but the two groups overlap a lot (Cohen's d ≈ 0.39).

**How do you know it is not luck?**
A permutation test with NumPy: shuffle the toxic / non-toxic labels 10,000 times and count how
often chance gives a gap as big as the real one. It never did, so p ≈ 0.0001. A Welch t-test in
the notebook agrees.

**Why is the difference only modest?**
Tox21 tests single effects on cells in a dish; LD50 is death of a whole animal, which also depends
on absorption, metabolism and excretion. Estrogen and androgen receptor hits barely change LD50,
while aromatase, p53 and PPAR-gamma hits are about 3 times more lethal.
