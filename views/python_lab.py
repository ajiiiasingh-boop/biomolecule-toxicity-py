"""Python Lab: the computational-thinking side of the project, shown with the real code.

This page reads the project's own source files (with pathlib, ast and inspect)
so the numbers and code on screen are always the live ones.
"""

import ast
import inspect
from pathlib import Path

import pandas as pd
import streamlit as st

from btd import analysis, drawing, scoring, ui
from btd.data import CASE_BY_ID, CASES, option_label

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"__pycache__", ".git", ".streamlit", ".venv", "venv"}

ROLES = {
    "app.py": "Front door: page setup, navigation bar, sidebar",
    "run.py": "One-click launcher: installs the libraries and starts the site",
    "play_in_terminal.py": "The same game in the terminal, plain Python only",
    "btd/data.py": "Loads the biology from the JSON files (abstraction)",
    "btd/scoring.py": "Grades answers, hints and the quiz (the algorithm)",
    "btd/progress.py": "Score, solved cases and the downloadable report",
    "btd/analysis.py": "NumPy + Pandas: trends, correlation, replicates, tables",
    "btd/drawing.py": "Matplotlib: charts and the cell; Graphviz text for flowcharts",
    "btd/ui.py": "Streamlit helpers shared by every page",
    "btd/realdata.py": "Real data: Tox21 counts, LD50 comparison, permutation test",
    "scripts/get_data.py": "Downloads Tox21 (Kaggle) and LD50 data, matches them with RDKit",
}


def python_files():
    files = []
    for path in sorted(ROOT.rglob("*.py")):
        if not SKIP.intersection(path.relative_to(ROOT).parts):
            files.append(path)
    return files


def file_stats(path):
    """Lines and functions in one file. ast reads Python code as a tree of parts."""
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    functions = sum(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    return len(text.splitlines()), functions


def tree_lines(folder, prefix=""):
    """Draw the folder structure. The function calls itself for each sub-folder:
    that is recursion."""
    entries = sorted(p for p in folder.iterdir() if p.name not in SKIP and not p.name.startswith("."))
    lines = []
    for i, entry in enumerate(entries):
        last = i == len(entries) - 1
        lines.append(prefix + ("└── " if last else "├── ") + entry.name + ("/" if entry.is_dir() else ""))
        if entry.is_dir():
            lines += tree_lines(entry, prefix + ("    " if last else "│   "))
    return lines


ui.page_header("Computational thinking", "Python Lab",
               "How the biology problem was broken down and solved in Python — shown with the "
               "project's real code, read live from its own files.")

stats = pd.DataFrame(
    [{"File": p.relative_to(ROOT).as_posix(), "Lines": file_stats(p)[0], "Functions": file_stats(p)[1]}
     for p in python_files()]
)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Python files", len(stats), border=True)
m2.metric("Lines of Python", int(stats["Lines"].sum()), border=True)
m3.metric("Functions", int(stats["Functions"].sum()), border=True)
m4.metric("Lines of HTML / CSS / JS", 0, border=True,
          help="None were written. Streamlit turns the Python into the web page. The only "
               "non-Python files are the JSON data, requirements.txt and the theme settings.")

t1, t2, t3, t4, t5 = st.tabs(["1 · Decomposition", "2 · Pattern recognition", "3 · Abstraction",
                              "4 · Algorithm", "Libraries used"])

# ------------------------------------------------------------ decomposition
with t1:
    st.markdown("**Break one big problem into small parts that can be built and tested alone.** "
                "The game became a data layer, an engine and a set of screens:")
    left, right = st.columns([1.15, 1.8], gap="large")
    with left:
        st.code("\n".join([ROOT.name + "/"] + tree_lines(ROOT)), language=None)
    with right:
        stats["Job"] = stats["File"].map(ROLES).fillna("")
        stats.loc[stats["File"].str.startswith("views/"), "Job"] = "One page of the website"
        stats.loc[stats["File"].str.startswith("tests/"), "Job"] = "Automated tests"
        stats.loc[stats["File"] == "btd/__init__.py", "Job"] = "Marks btd/ as a package; explains the split"
        st.dataframe(stats, hide_index=True, height=36 * (len(stats) + 1) + 4,
                     column_config={"Job": st.column_config.TextColumn("Job", width="large")})

# ------------------------------------------------------- pattern recognition
with t2:
    st.markdown("**Spot the pattern in the data.** Every case hides its answer in the direction "
                "the numbers move as the dose rises. Python measures that for any dataset:")
    options = [(c["id"], d["id"]) for c in CASES for d in c["datasets"]]
    pick = st.selectbox("Dataset", options, format_func=lambda o: f"Case {CASE_BY_ID[o[0]]['number']} · "
                        + next(d["title"] for d in CASE_BY_ID[o[0]]["datasets"] if d["id"] == o[1]))
    dataset = next(d for d in CASE_BY_ID[pick[0]]["datasets"] if d["id"] == pick[1])
    st.dataframe(analysis.pattern_report(dataset), hide_index=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.caption("THE PATTERN RULE (NumPy)")
        st.code(inspect.getsource(analysis.describe_trend))
    with c2:
        st.caption("SIMULATED REPLICATES (NumPy random numbers)")
        st.write("Real labs repeat each measurement three times. NumPy adds that scatter, then "
                 "centres it so the average is exactly the case value:")
        st.dataframe(analysis.replicate_table(dataset), hide_index=True, height=260)
    with st.expander("Show simulate_replicates()"):
        st.code(inspect.getsource(analysis.simulate_replicates))

# --------------------------------------------------------------- abstraction
with t3:
    st.markdown("**Keep what matters, hide the rest.** A case is not a web page — it is one "
                "dictionary with the same keys every time. That is why one set of code can run "
                "all six cases, and a seventh case would need new data, not new code.")
    case = CASES[0]
    shown = {k: v for k, v in case.items() if k not in ("solution",)}
    shown["solution"] = "(hidden from the player — only grade_case() reads it)"
    st.json(shown, expanded=1)
    st.caption("Every case has exactly these keys:")
    st.dataframe(pd.DataFrame([{
        "Case": c["number"], "Title": c["title"], "Evidence cards": len(c["evidence"]),
        "Datasets": len(c["datasets"]), "Answer options": len(c["questions"]["biomolecule"]["options"])
        + len(c["questions"]["mechanism"]["options"]), "Keys": len(c)} for c in CASES]), hide_index=True)

# ------------------------------------------------------------------ algorithm
with t4:
    st.markdown("**Write the steps so a computer can follow them the same way every time.**")
    left, right = st.columns([1, 1.3], gap="large")
    with left:
        st.caption("THE INVESTIGATION ALGORITHM")
        st.graphviz_chart(drawing.investigation_flowchart_dot(), width="stretch")
    with right:
        st.caption("TRY THE GRADER YOURSELF")
        case_id = st.selectbox("Case", [c["id"] for c in CASES],
                               format_func=lambda cid: f"Case {CASE_BY_ID[cid]['number']} · {CASE_BY_ID[cid]['title']}")
        case = CASE_BY_ID[case_id]
        g1, g2 = st.columns(2)
        bio = g1.selectbox("Biomolecule", case["questions"]["biomolecule"]["options"],
                           format_func=lambda o: option_label("biomolecule", o))
        mech = g2.selectbox("Mechanism", case["questions"]["mechanism"]["options"],
                            format_func=lambda o: option_label("mechanism", o))
        g3, g4 = st.columns(2)
        hints = g3.number_input("Hints used", 0, 2, 0)
        attempt = g4.number_input("Attempt number", 1, 9, 1)
        graded = scoring.grade_case(case, bio, mech, hints_used=hints, attempt=attempt)
        st.code(f"grade_case(case, {bio!r}, {mech!r}, hints_used={hints}, attempt={attempt})",
                language="python")
        st.json({k: graded[k] for k in ("solved", "biomolecule_correct", "mechanism_correct",
                                        "points", "breakdown", "feedback")})
    with st.expander("Show grade_case()"):
        st.code(inspect.getsource(scoring.grade_case), line_numbers=True)

# ------------------------------------------------------------------ libraries
with t5:
    st.dataframe(pd.DataFrame([
        {"Library": "Streamlit", "Where": "app.py, views/, btd/ui.py",
         "What it does here": "Turns Python into the web pages: buttons, tabs, forms, the sidebar score"},
        {"Library": "Pandas", "Where": "btd/analysis.py, btd/realdata.py",
         "What it does here": "DataFrames for every dataset; boolean-mask filters and groupby in the "
                              "toxin library; reading the 7,831-compound Tox21 CSV; CSV downloads"},
        {"Library": "NumPy", "Where": "btd/analysis.py, btd/realdata.py, btd/drawing.py",
         "What it does here": "% change, trend detection (np.diff), correlation (np.corrcoef), "
                              "simulated replicates, the permutation test on real LD50 data, cell geometry"},
        {"Library": "Matplotlib", "Where": "btd/drawing.py",
         "What it does here": "Evidence charts with error bars, the cell diagram, the toxin chart"},
        {"Library": "json, pathlib", "Where": "btd/data.py",
         "What it does here": "Reading the biology from the data files (standard library)"},
        {"Library": "inspect, ast", "Where": "views/python_lab.py",
         "What it does here": "Showing real code on this page and counting its functions"},
        {"Library": "unittest", "Where": "tests/",
         "What it does here": "Automated checks of the data, the grader and the pages"},
        {"Library": "kagglehub, RDKit", "Where": "scripts/get_data.py (not needed by the website)",
         "What it does here": "Downloading Tox21 from Kaggle; matching compounds across datasets by "
                              "chemical structure (InChIKey)"},
    ]), hide_index=True)

ui.disclaimer()
