"""Home page: the briefing, the four biomolecule classes and a preview of the cases."""

import streamlit as st

from btd import progress as prog
from btd import ui
from btd.data import BIOMOLECULES, CASES, QUIZ, answer_mechanisms
from btd.scoring import RULE_TEXT

# Bars in the specimen panel. Fixed illustrative values, labelled as such.
READOUT = {
    "dna-rna": (34, "8-oxo-dG ↑"),
    "protein": (28, "Activity ↓"),
    "lipid": (41, "MDA ↑"),
    "carbohydrate": (52, "ATP ↓"),
}

summary = prog.summary(ui.progress())

# ------------------------------------------------------------------ hero
left, right = st.columns([1.35, 1], gap="large")
with left:
    st.caption("CASE SERIES BTD‑2041 · EDUCATIONAL SIMULATION")
    st.title("Biomolecule :primary[Toxicity Detective]", anchor=False)
    st.markdown("##### Something has gone wrong inside the cell. Follow the evidence. "
                "Identify the biomolecule. Solve the toxicity case.")
    b1, b2 = st.columns(2)
    if b1.button("Start investigation", type="primary", icon=":material/arrow_forward:",
                 width="stretch"):
        st.switch_page("views/case_files.py")
    if b2.button("Open the biomolecule database", icon=":material/genetics:", width="stretch"):
        st.switch_page("views/biomolecules.py")

    st.space("small")
    stats = st.columns(4)
    stats[0].metric("Case files", len(CASES), border=True)
    stats[1].metric("Biomolecules", len(BIOMOLECULES), border=True)
    stats[2].metric("Mechanisms", len(answer_mechanisms()), border=True)
    stats[3].metric("Quiz questions", len(QUIZ), border=True)

with right:
    with st.container(border=True):
        head, tag = st.columns([2, 1])
        head.caption("SPECIMEN PANEL")
        tag.badge("Illustrative", color="gray")
        for b in BIOMOLECULES:
            integrity, marker = READOUT[b["id"]]
            st.progress(integrity / 100,
                        text=f"{b['emoji']} **{b['label']}** · integrity {integrity}% · :orange[{marker}]")
        st.caption("Four classes of biomolecule, four ways for a cell to be damaged. "
                   "Each case in this series points at exactly one of them.")

st.divider()

# ------------------------------------------------------------- the premise
st.caption("BRIEFING")
st.header("What you are looking for", anchor=False)
st.write(
    "Biomolecules such as proteins, lipids, carbohydrates, DNA and RNA are essential for cellular "
    "function. Toxic substances can interfere with these molecules through mechanisms such as "
    "enzyme inhibition, oxidative damage, denaturation and lipid peroxidation. Each mechanism "
    "leaves a different set of fingerprints — and reading those fingerprints, rather than the "
    "symptom at the end of the chain, is what this investigation trains."
)
cards = st.columns(4)
for column, b in zip(cards, BIOMOLECULES):
    with column.container(border=True, height="stretch"):
        st.markdown(f"### {b['emoji']} :{ui.CHANNEL_COLOR[b['id']]}[{b['label']}]")
        st.caption(b["tagline"])
        with st.expander("How toxicity affects it"):
            st.write(b["summary"])
            for hit in b["howToxicityHits"][:2]:
                st.markdown(f"**{hit['title']}.** {hit['body']}")
            st.page_link("views/biomolecules.py", label="Full database entry",
                         icon=":material/arrow_forward:", query_params={"b": b["id"]})
st.page_link("views/mechanism_map.py", label="See the full mechanism chain",
             icon=":material/account_tree:")

st.divider()

# ------------------------------------------------------------ how it works
st.caption("PROCEDURE")
st.header("How an investigation runs", anchor=False)
steps = [
    ("Open the evidence", "Four evidence cards per case: a molecular observation, an experimental "
     "dataset, a structural clue about the biomolecule itself, and the effect on the cell. All "
     "four must be opened before you can submit."),
    ("Read the data", "Every case carries a simulated dose–response dataset. Switch to the "
     "interactive chart to hover any point, or read the table. The direction a curve moves is "
     "usually the whole answer."),
    ("Commit to a conclusion", "Name the affected biomolecule and the mechanism. Correct answers "
     "unlock the full explanation and the causal pathway; wrong ones send you back to a specific "
     "piece of evidence."),
]
for column, (number, (title, text)) in zip(st.columns(3), enumerate(steps, start=1)):
    with column:
        st.markdown(f"## :blue[{number}]")
        st.subheader(title.upper(), anchor=False)
        st.write(text)

with st.container(border=True):
    st.caption("SCORING")
    st.markdown("  ".join(f":primary-badge[{label} **{value}**]" for label, value in RULE_TEXT))
    st.markdown(f"Your score **{summary['score']}** · Solved "
                f"**{summary['cases_solved']}/{summary['cases_total']}**")

st.divider()

# ------------------------------------------------------------ case preview
st.caption("OPEN CASE FILES")
st.header("Six investigations", anchor=False)
for column, case in zip(st.columns(3), CASES[:3]):
    with column:
        ui.case_card(case, brief_length=145)
st.page_link("views/case_files.py", label="View all case files", icon=":material/arrow_forward:")

if summary["all_solved"]:
    st.success(f"All {summary['cases_total']} cases solved.", icon=":material/verified:")
    st.page_link("views/debrief.py", label="View final debrief", icon=":material/assignment:")

st.divider()
ui.disclaimer()
