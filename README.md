# Biomolecule Toxicity Detective — Python edition

An investigation game about how toxic substances damage biomolecules, rebuilt entirely in
**Python**. You open four pieces of evidence, read a simulated dose–response dataset, and name
the damaged biomolecule and the mechanism. The biology is identical to the original website.
The website part is now Python (Streamlit) instead of HTML, CSS and JavaScript.

> **Educational simulation.** Every case, compound and number in the game is simulated. The
> **Data Lab** page is the one exception: it analyses real public datasets (Tox21 and rat LD50
> values). Nothing here is a clinical, diagnostic or real-world toxicology assessment, and
> nothing describes how to obtain, prepare or handle any substance.

## What is inside

| Page | What you can do |
|---|---|
| Home | Briefing, the four biomolecule classes, scoring rules, case preview |
| Case Files | All six cases with difficulty and your progress |
| Investigation | Open evidence A–D, read the charts (Matplotlib, interactive, table, pattern detector), answer, use hints, get targeted feedback or the full explanation + causal pathway |
| Case Report | Score, case record table, mechanisms identified, download report (.txt / .csv) |
| Biomolecules | Database of DNA/RNA, proteins, lipids, carbohydrates |
| Toxin Library | 17 toxins, filter by category / target / text (Pandas), chart by target |
| Quiz | 10 questions, +10 points each |
| Data Lab | Real data: how many Tox21 compounds are toxic, and do they have a lower LD50? Charts, permutation test, per-assay results, upload your own dataset |
| Mechanism Map | The 5 stages from exposure to effect |
| Cell Lab | Matplotlib drawing of the cell; trace the route of each mechanism |
| Python Lab (CT) | The four computational-thinking pillars shown with the project's real code |
| About | What the project is and is not |

Scoring: correct biomolecule **+50**, correct mechanism **+50**, solved first try with no hints
**+20**, each hint **−10**, each correct quiz answer **+10**.

## Run it on your computer

You need **Python 3.10 or newer** (python.org → Downloads; on Windows tick
*"Add python.exe to PATH"* during install).

**Easiest:** double-click `run.py`. The first time it installs the libraries, then it opens the site
in your browser at http://localhost:8501.

**Or with commands**, from inside this folder:

```bash
pip install -r requirements.txt
streamlit run app.py
```

(If `pip` or `streamlit` is "not recognised", use `python -m pip ...` and `python -m streamlit run app.py`.
On a Mac, type `python3` instead of `python`.)

**Terminal version (no installs at all):**

```bash
python play_in_terminal.py
```

**Run the automated tests:**

```bash
python -m unittest
```

## The Data Lab: real data from Kaggle

Problem statement: *take a chemical toxicity dataset (Tox21), count the toxic and non-toxic
compounds, and compare the average LD50 of the two groups. Is there a visible difference?*

The two CSV files the page needs are already in `data/real/`, so the website works straight
away. To download them yourself:

**1. Tox21 from Kaggle.** Any one of these:

* **Website:** kaggle.com → search *Tox21* → open `epicskills/tox21-dataset` → **Download** →
  unzip → save the CSV as `data/real/tox21.csv`.
* **Python (`kagglehub`):**
  ```python
  import kagglehub
  folder = kagglehub.dataset_download("epicskills/tox21-dataset")
  print(folder)          # the CSV is inside this folder
  ```
  Public datasets usually download without logging in. If Kaggle asks you to log in:
  kaggle.com → your picture → **Settings** → **API** → **Generate New Token**, then run
  `kagglehub.login()` and paste the token.
* **Command line:** `pip install kaggle`, `kaggle auth login` (or put the token in
  `~/.kaggle/`), then `kaggle datasets download -d epicskills/tox21-dataset --unzip -p data/real`.
* **No Kaggle account:** the same data is at
  `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz` (MoleculeNet), and
  `pandas.read_csv()` can read that link directly.

**2. LD50 values.** Tox21 only says toxic yes/no per assay; it has **no LD50**. So the LD50 comes
from a second dataset: **LDToxDB** (13,329 rat oral LD50 values, MIT licence,
`https://raw.githubusercontent.com/AI4PFAS/AI4PFAS/main/data/ldtoxdb-raw.csv`). A Kaggle
alternative is `iapetus509/therapeutics-data-commons-acute-toxicity-ld50` (TDC, 7,385 compounds).

**3. Match them.** The two tables write the same chemical differently, so they are matched by
structure with RDKit (InChIKey). One script does all three steps:

```bash
pip install -r requirements-data.txt      # pandas, numpy, rdkit, kagglehub
python scripts/get_data.py                # Tox21 from Kaggle + LDToxDB
python scripts/get_data.py --direct       # no Kaggle: direct links only
python scripts/get_data.py --ld50 tdc     # use the Kaggle TDC LD50 set instead
```

**Result:** 2,872 of 7,831 Tox21 compounds (36.7%) are toxic in at least one assay and 4,959
are not. For the 3,831 that also have an LD50, the toxic group is about **2 times more toxic**
on average (mean −log LD50 2.39 vs 2.09; median LD50 ≈ 1,610 vs 2,250 mg/kg). A permutation
test says this is not chance (p ≈ 0.0001), but the effect is small-to-medium (Cohen's d ≈ 0.39)
and the two groups overlap a lot.

The same analysis as a step-by-step Jupyter notebook: `notebooks/Tox21_LD50_Analysis.ipynb`.

## Put it online for free (Streamlit Community Cloud)

1. Create a new **public** repository on github.com (for example `btd-python`).
2. Click **Add file → Upload files** and drag in *everything inside this folder*, including the
   folders `btd`, `views`, `data`, `tests` and `.streamlit`. Click **Commit changes**.
   (On a Mac, press **Cmd + Shift + .** in Finder to show the hidden `.streamlit` folder so you can
   drag it. Without it the site still works, just with default colours.)
3. Go to **share.streamlit.io** and sign in with GitHub.
4. Click **Create app** → **"Yup, I have an app"**.
5. Fill in: **Repository** = your repo, **Branch** = `main`, **Main file path** = `app.py`.
   Optionally choose a custom **App URL**.
6. Click **Deploy**. After a few minutes you get a link like `https://your-name.streamlit.app`.

Free apps go to sleep after a while with no visitors; the first visitor clicks
"Yes, get this app back up" and it wakes in under a minute.

## How the project is organised

```
app.py                 front door: page setup, navigation bar, sidebar score
run.py                 one-click launcher
play_in_terminal.py    the same game with print() and input() only
requirements.txt       the four libraries
requirements-data.txt  extra libraries for scripts/get_data.py only (rdkit, kagglehub)
.streamlit/config.toml the pink theme (settings, not code)
data/                  the biology: cases, biomolecules, mechanisms, toxins, quiz (JSON)
    real/              the real datasets: tox21.csv, tox21_ld50.csv (Data Lab)
btd/                   the engine — all the logic, no screens
    data.py            loads the JSON files                     (standard library)
    scoring.py         grade_case(), get_hint(), grade_quiz()   (standard library)
    progress.py        score, solved cases, text report         (standard library)
    analysis.py        trends, correlation, replicates, tables  (NumPy + Pandas)
    drawing.py         charts, cell diagram, flowcharts         (Matplotlib)
    realdata.py        Tox21 counts, LD50 comparison, permutation test  (NumPy + Pandas)
    ui.py              Streamlit helpers shared by the pages
views/                 one file per page of the website
scripts/get_data.py    downloads Tox21 (Kaggle) + LD50 and matches them (RDKit)
notebooks/             the Tox21 vs LD50 analysis as a Jupyter notebook
tests/                 41 automated tests (unittest)
```

The website and the terminal game import the **same** `btd` engine, so a case can never be marked
differently in the two versions.

## Compared with the original website

| | Original website | Python edition |
|---|---|---|
| Languages written | JavaScript, HTML, CSS | Python only |
| Screens | React | Streamlit |
| Charts | hand-drawn SVG | Matplotlib (+ interactive Streamlit charts) |
| Server / API | Express REST API | Streamlit runs the Python on the server |
| Where the answer key lives | server (API mode) | server, always — never sent to the browser |
| Score saving | browser storage + API | this browser tab's session; download the report to keep it |
| Background animation | CSS + canvas | not included (Streamlit has no animation without CSS/JS) |
| Extra in this version | — | pattern detector, simulated replicates with error bars, Python Lab page, Data Lab with real Tox21 + LD50 data, terminal edition |

See **PYTHON-GUIDE.md** for a walk-through of the code, the computational-thinking map and
likely viva questions.
