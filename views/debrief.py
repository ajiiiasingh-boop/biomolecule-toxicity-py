"""Case Report page: the final debrief, downloadable as a file."""

import streamlit as st

from btd import progress as prog
from btd import ui
from btd.analysis import case_record_frame
from btd.data import CASES, MECHANISM_BY_ID
from btd.scoring import RULE_TEXT

notebook = ui.progress()
summary = prog.summary(notebook)

ui.page_header("Final debrief", "Case report",
               "Everything you have solved so far, how the score was built, and a copy to keep.")

if summary["cases_solved"] == 0:
    st.info("No cases solved yet. Solve a case and it will appear here.", icon=":material/search:")
    ui.open_case_link(prog.next_unsolved(notebook) or CASES[0]["id"], label="Start investigating",
                      primary=False)

# ------------------------------------------------------------------ totals
score_col, stats_col = st.columns([1, 2.2], gap="large")
with score_col.container(border=True):
    st.caption("DETECTIVE SCORE")
    st.markdown(f"# :primary[{summary['score']}]")
    st.caption("points")
with stats_col:
    row = st.columns(4)
    row[0].metric("Cases solved", f"{summary['cases_solved']}/{summary['cases_total']}", border=True)
    row[1].metric("Hints used", summary["hints_used"], border=True)
    row[2].metric("Attempts", summary["attempts"], border=True)
    row[3].metric("Accuracy", f"{summary['accuracy']}%" if summary["accuracy"] is not None else "—",
                  border=True, help="Cases solved ÷ conclusions submitted")
    quiz = summary["quiz"]
    st.markdown(f"**Quiz:** {quiz['score']}/{quiz['total']} (+{quiz['points']} points)" if quiz
                else "**Quiz:** not taken yet")

# ------------------------------------------------------------- case record
st.subheader("Case record", anchor=False)
record = case_record_frame(notebook)            # a Pandas DataFrame
st.dataframe(
    record,
    hide_index=True,
    column_config={
        "Solved": st.column_config.CheckboxColumn("Solved"),
        "Points": st.column_config.ProgressColumn("Points", min_value=0, max_value=120, format="%d"),
    },
)

# ------------------------------------------------------ mechanisms identified
st.subheader("Mechanisms identified", anchor=False)
solved_cases = [c for c in CASES if c["id"] in summary["solved_ids"]]
if not solved_cases:
    st.caption("None yet. Solve a case to add its mechanism here.")
for case in solved_cases:
    mechanism = MECHANISM_BY_ID[case["solution"]["mechanism"]]
    with st.container(border=True):
        st.markdown(f"**{mechanism['label']}** {ui.biomolecule_badge(mechanism['biomolecule'])} "
                    f":gray-badge[Case {case['number']}]")
        st.caption(mechanism["oneLine"])

# --------------------------------------------------------- how score is built
with st.container(border=True):
    st.caption("HOW THE SCORE WAS BUILT")
    st.markdown("  ".join(f":primary-badge[{label} **{value}**]" for label, value in RULE_TEXT))
    st.caption("Points for a case are banked once, the first time it is solved, so replaying a "
               "case cannot inflate the score. A quiz retake replaces the earlier quiz points.")

# ----------------------------------------------------------------- download
st.subheader("Keep a copy", anchor=False)
name = st.text_input("Detective name for the report (optional)", max_chars=40)
d1, d2 = st.columns(2)
d1.download_button("Download case report (.txt)", prog.make_report(notebook, name),
                   file_name="case-report.txt", mime="text/plain", icon=":material/download:",
                   width="stretch")
d2.download_button("Download case record (.csv)", record.to_csv(index=False),
                   file_name="case-record.csv", mime="text/csv", icon=":material/table_view:",
                   width="stretch")

st.divider()
b1, b2, b3 = st.columns(3)
if b1.button("Back to case files", icon=":material/folder_open:", width="stretch"):
    st.switch_page("views/case_files.py")
if b2.button("Take the quiz", icon=":material/quiz:", width="stretch"):
    st.switch_page("views/quiz.py")
with b3.popover("Reset all progress", icon=":material/restart_alt:", width="stretch"):
    st.write("This clears your score, every case and the quiz. It cannot be undone.")
    if st.button("Yes, reset everything", type="primary"):
        st.session_state.progress = prog.new_progress()
        st.session_state.investigations = {}
        st.session_state.pop("quiz_result", None)
        st.rerun()

ui.disclaimer()
