"""Investigation page: the evidence board, the charts and the conclusion.

The flow on this page is the investigation algorithm:
    open all four evidence cards -> answer two questions -> grade -> explain or send back
"""

import inspect

import streamlit as st

from btd import progress as prog
from btd import ui
from btd.analysis import dataset_frame, pattern_report, pattern_sentences
from btd.data import CASE_BY_ID, CASE_IDS, MECHANISM_BY_ID, evidence_datasets, option_label
from btd.drawing import CHANNEL, dose_chart, pathway_dot
from btd.scoring import SCORE_RULES, get_hint, grade_case

# ---------------------------------------------------------------- which case?
# The link that opened this page says which case (?case=case-03).
case_id = st.query_params.get("case", st.session_state.get("active_case", CASE_IDS[0]))
if case_id not in CASE_BY_ID:
    case_id = CASE_IDS[0]
st.session_state.active_case = case_id
case = CASE_BY_ID[case_id]
board = ui.investigation(case_id)
notebook = ui.progress()


def switch_case():
    chosen = st.session_state.case_switch
    if chosen:
        st.query_params["case"] = chosen


st.session_state.case_switch = case_id       # keep the switcher in step with the link
st.segmented_control(
    "Case file",
    CASE_IDS,
    key="case_switch",
    on_change=switch_case,
    format_func=lambda cid: f"Case {CASE_BY_ID[cid]['number']}" + (" ✓" if prog.is_solved(notebook, cid) else ""),
    label_visibility="collapsed",
)

if st.session_state.pop("celebrate", False):
    st.balloons()

# ------------------------------------------------------------------- header
st.caption(f"CASE {case['number']} · {case['codename']} · {case['difficulty'].upper()}")
st.title(case["title"], anchor=False)
with st.container(border=True):
    c1, c2, c3 = st.columns([1.3, 1.3, 0.6])
    c1.markdown(f"**Specimen**  \n{case['specimen']}")
    c2.markdown(f"**Exposure**  \n{case['exposure']}")
    c3.markdown(f"**Duration**  \n{case['duration']}")
st.info(case["brief"], icon=":material/description:")


# ------------------------------------------------------------ evidence board
def show_dataset(dataset):
    """One dataset, four ways: chart, interactive chart, table, pattern detector."""
    ui.simulated_tag()
    tab_chart, tab_hover, tab_table, tab_pattern = st.tabs(
        ["Chart", "Interactive (hover)", "Data table", "Pattern detector"])
    frame = dataset_frame(dataset)
    with tab_chart:
        with_bars = st.toggle("Show error bars (3 simulated replicates, made with NumPy)",
                              value=True, key=f"bars-{dataset['id']}")
        st.pyplot(dose_chart(dataset, show_replicates=with_bars))
        st.caption(dataset["caption"])
    with tab_hover:
        # Numbering the levels keeps them in dose order on the interactive chart.
        numbered = frame.copy()
        numbered.index = [f"{i} · {level}" for i, level in enumerate(frame.index)]
        colors = [CHANNEL[s["channel"]] for s in dataset["series"]]
        if dataset["type"] == "bar":
            st.bar_chart(numbered, x_label=dataset["xLabel"], y_label=dataset["yLabel"],
                         color=colors, stack=False)
        else:
            st.line_chart(numbered, x_label=dataset["xLabel"], y_label=dataset["yLabel"],
                          color=colors)
        st.caption("Hover any point to read its value. Simulated data.")
    with tab_table:
        st.dataframe(frame)
    with tab_pattern:
        st.write("Python measured how each value moves as the dose goes up "
                 "(`pattern_report()` in `btd/analysis.py`):")
        st.dataframe(pattern_report(dataset), hide_index=True)
        for sentence in pattern_sentences(dataset):
            st.markdown(f"- {sentence}")
        st.caption("The pattern tells you what moved. Deciding what that means is your job.")


st.header("Evidence board", anchor=False)
opened = board["opened"]
st.progress(len(opened) / len(case["evidence"]),
            text=f"Evidence discovered: {len(opened)}/{len(case['evidence'])}")

for column, evidence in zip(st.columns(len(case["evidence"])), case["evidence"]):
    with column:
        is_open = evidence["id"] in opened
        clicked = st.button(
            f"Evidence {evidence['id']}  \n{evidence['kind']}",
            key=f"ev-{case_id}-{evidence['id']}",
            icon=":material/check_circle:" if is_open else ":material/lock:",
            type="primary" if board["selected"] == evidence["id"] else "secondary",
            width="stretch",
        )
        st.caption(evidence["title"] if is_open else "Sealed — click to open")
        if clicked:
            if not is_open:
                opened.append(evidence["id"])
                st.toast(f"Evidence {evidence['id']} added to the board", icon=":material/push_pin:")
            board["selected"] = evidence["id"]
            st.rerun()

selected = next((e for e in case["evidence"] if e["id"] == board["selected"]), None)
if selected is None:
    st.info("Select a card above to read it. All four must be opened before a conclusion can be "
            "submitted.", icon=":material/touch_app:")
else:
    with st.container(border=True):
        st.caption(f"EVIDENCE {selected['id']} · {selected['kind'].upper()}")
        st.subheader(selected["title"], anchor=False)
        st.write(selected["body"])
        for readout in selected["readouts"]:
            color, icon, word = ui.READOUT_STYLE[readout["state"]]
            label, value, state = st.columns([2.2, 2.2, 1])
            label.write(readout["label"])
            value.markdown(f"**{readout['value']}**")
            state.markdown(f":{color}-badge[{icon} {word}]")
        for dataset in evidence_datasets(case, selected):
            st.divider()
            show_dataset(dataset)

st.divider()

# -------------------------------------------------------------- conclusion
st.header("Your conclusion", anchor=False)
result = board["result"]


def hint_block(field):
    """Show the hint if it was bought, otherwise a button to buy it."""
    if field in board["hints"]:
        st.info(board["hints"][field], icon=":material/lightbulb:")
    elif result is None and st.button(f"Use a hint ({SCORE_RULES['hint_penalty']} points)",
                                      key=f"hint-{case_id}-{field}", icon=":material/lightbulb:",
                                      type="tertiary"):
        board["hints"][field] = get_hint(case, field)
        prog.record_hint(notebook, case_id)
        st.rerun()


def show_solved(result):
    st.success(f"**CASE SOLVED** · +{result['points']} points", icon=":material/verified:")
    st.subheader(result["verdict"], anchor=False)
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        st.caption("WHY THIS IS THE ANSWER")
        for paragraph in result["explanation"].split("\n\n"):
            st.write(paragraph)
    with right:
        st.caption("POINTS")
        for label, correct, points in result["breakdown"]:
            mark = ":green[:material/check:]" if correct else ":orange[:material/remove:]"
            st.markdown(f"{mark} {label} — **{points:+d}**")
        st.caption("CAUSAL PATHWAY")
        color = CHANNEL[case["solution"]["biomolecule"]]
        st.graphviz_chart(pathway_dot(result["pathway"], color), width="stretch")
    st.caption("KEY TERMS")
    for column, term in zip(st.columns(len(result["key_terms"])), result["key_terms"]):
        with column.container(border=True, height="stretch"):
            st.markdown(f"**{term['term']}**")
            st.caption(term["def"])
    mechanism = MECHANISM_BY_ID[case["solution"]["mechanism"]]
    st.markdown(f"Mechanism identified: **{mechanism['label']}** "
                f"{ui.biomolecule_badge(case['solution']['biomolecule'])} — {mechanism['oneLine']}")


def show_under_the_hood(result):
    with st.expander("Under the hood: how Python marked this answer", icon=":material/code:"):
        st.write("Submitting called `grade_case()` from `btd/scoring.py`. "
                 "This is the dictionary it returned (long texts left out):")
        st.json({k: v for k, v in result.items() if k not in ("explanation", "key_terms", "pathway")},
                expanded=1)
        st.write("And this is the function itself:")
        st.code(inspect.getsource(grade_case), line_numbers=True)


remaining = len(case["evidence"]) - len(opened)

if result and result["solved"]:
    show_solved(result)
    show_under_the_hood(result)
    next_case = prog.next_unsolved(notebook)
    b1, b2 = st.columns([1, 1])
    if next_case:
        if b1.button(f"Next case: {CASE_BY_ID[next_case]['title']}", type="primary",
                     icon=":material/arrow_forward:", width="stretch"):
            st.query_params["case"] = next_case
            st.rerun()
    else:
        if b1.button("All cases closed — view your case report", type="primary",
                     icon=":material/assignment:", width="stretch"):
            st.switch_page("views/debrief.py")
    if b2.button("Replay this case (points are only banked once)", icon=":material/replay:",
                 width="stretch"):
        st.session_state.investigations.pop(case_id)
        st.rerun()

elif remaining > 0:
    st.warning(f"{remaining} evidence card{'s' if remaining != 1 else ''} still unread. "
               "Open them all to unlock the conclusion.", icon=":material/lock:")

else:
    locked = result is not None                # a wrong answer is on screen
    questions = case["questions"]
    answers = {}
    q_cols = st.columns(2, gap="large")
    for column, (number, field) in zip(q_cols, enumerate(("biomolecule", "mechanism"), start=1)):
        with column:
            st.markdown(f"**Q{number}. {questions[field]['prompt']}**")
            answers[field] = st.radio(
                f"Q{number}",
                questions[field]["options"],
                index=None,
                format_func=lambda option, f=field: option_label(f, option),
                key=f"q{number}-{case_id}-{board['attempt']}",
                label_visibility="collapsed",
                disabled=locked,
            )
            hint_block(field)

    hints_used = len(board["hints"])
    st.caption(f"Attempt {board['attempt']} · {hints_used} hint{'s' if hints_used != 1 else ''} used · "
               "correct biomolecule +50, correct mechanism +50, first-attempt bonus +20, each hint −10")

    if not locked:
        ready = answers["biomolecule"] and answers["mechanism"]
        if st.button("Submit conclusion", type="primary", icon=":material/gavel:", disabled=not ready):
            graded = grade_case(case, answers["biomolecule"], answers["mechanism"],
                                hints_used=hints_used, attempt=board["attempt"])
            board["result"] = graded
            if prog.record_attempt(notebook, case_id, graded):
                st.session_state.celebrate = True
            st.rerun()
    else:
        st.error("**Not quite.** Part of your conclusion does not fit the evidence. Nothing is "
                 "lost — go back and look again.", icon=":material/search:")
        for field in ("biomolecule", "mechanism"):
            correct = result[f"{field}_correct"]
            chosen = option_label(field, result["submitted"][field])
            with st.container(border=True):
                mark = ":green[:material/check_circle:]" if correct else ":orange[:material/cancel:]"
                st.markdown(f"{mark} **{field.capitalize()}:** {chosen}")
                st.write(result["feedback"][field])
        show_under_the_hood(result)
        if st.button("Try again", type="primary", icon=":material/replay:"):
            board["attempt"] += 1
            board["result"] = None
            st.rerun()

st.divider()
ui.disclaimer()
