"""Case Files page: all six investigations, with their status."""

import streamlit as st

from btd import progress as prog
from btd import ui
from btd.data import CASES

summary = prog.summary(ui.progress())

ui.page_header(
    "Case files",
    "Six investigations",
    "Each case hides one damaged biomolecule and one mechanism. Open all four pieces of evidence, "
    "then name them both.",
)
st.progress(summary["cases_solved"] / summary["cases_total"],
            text=f"{summary['cases_solved']} of {summary['cases_total']} solved")
if summary["all_solved"]:
    st.success("Every case is closed. Your final debrief is ready.", icon=":material/verified:")
    st.page_link("views/debrief.py", label="View final debrief", icon=":material/assignment:")

levels = []
for case in CASES:                    # difficulty levels in the order they first appear
    if case["difficulty"] not in levels:
        levels.append(case["difficulty"])
chosen = st.pills("Difficulty", levels, selection_mode="multi", default=levels)
shown = [case for case in CASES if case["difficulty"] in chosen]

if not shown:
    st.info("No difficulty selected. Pick at least one above.")

# Three cards per row.
for start in range(0, len(shown), 3):
    for column, case in zip(st.columns(3), shown[start:start + 3]):
        with column:
            ui.case_card(case, brief_length=220, details=True)

st.divider()
ui.disclaimer()
