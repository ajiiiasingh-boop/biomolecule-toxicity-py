"""
ui.py — small Streamlit helpers shared by every page.

How Streamlit works, in one paragraph: every time the visitor clicks
something, Streamlit runs the page's Python file again from top to bottom and
redraws the page. Anything that must survive those re-runs (the score, which
evidence cards are open) is kept in st.session_state, a dictionary that
belongs to one visitor's browser tab.
"""

import streamlit as st

from btd import progress as prog
from btd.data import BIOMOLECULE_BY_ID, CASE_BY_ID, DISCLAIMER

# Streamlit's built-in colour names, matched to the biomolecule classes in
# .streamlit/config.toml (blue = DNA/RNA, green = protein, red = lipid, yellow = carbohydrate).
CHANNEL_COLOR = {"dna-rna": "blue", "protein": "green", "lipid": "red", "carbohydrate": "yellow"}

# How each kind of lab reading is shown.
READOUT_STYLE = {
    "alert": ("orange", ":material/priority_high:", "Abnormal"),
    "normal": ("green", ":material/check:", "Normal"),
    "info": ("gray", ":material/info:", "Clue"),
}

INVESTIGATION_PAGE = "views/investigation.py"


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
def init_state():
    """Create the visitor's notebook the first time the app runs for them."""
    if "progress" not in st.session_state:
        st.session_state.progress = prog.new_progress()
    if "investigations" not in st.session_state:
        st.session_state.investigations = {}


def progress():
    init_state()
    return st.session_state.progress


def investigation(case_id):
    """The working state of one case: which cards are open, hints, attempts."""
    init_state()
    boards = st.session_state.investigations
    if case_id not in boards:
        boards[case_id] = {"opened": [], "selected": None, "hints": {}, "attempt": 1, "result": None}
    return boards[case_id]


# ---------------------------------------------------------------------------
# Small building blocks
# ---------------------------------------------------------------------------
def page_header(eyebrow, title, lede=None):
    st.caption(eyebrow.upper())
    st.title(title, anchor=False)
    if lede and len(lede) > 170:            # long introductions read better as body text
        st.markdown(f":gray[{lede}]")
    elif lede:
        st.markdown(f"##### :gray[{lede}]")


def biomolecule_badge(biomolecule_id):
    b = BIOMOLECULE_BY_ID[biomolecule_id]
    return f":{CHANNEL_COLOR[biomolecule_id]}-badge[{b['emoji']} {b['label']}]"


def disclaimer():
    st.warning(DISCLAIMER, icon=":material/school:")


def simulated_tag():
    st.badge("SIMULATED EDUCATIONAL DATA", icon=":material/science:", color="primary")


def open_case_link(case_id, label=None, primary=True):
    """A link that opens the investigation page on one case."""
    case = CASE_BY_ID[case_id]
    st.page_link(
        INVESTIGATION_PAGE,
        label=label or f"Open case {case['number']}",
        icon=":material/search:",
        query_params={"case": case_id},
        width="stretch" if primary else "content",
    )


def status_badge(case_id):
    """Solved / in progress / not started, as a coloured badge."""
    record = progress()["cases"].get(case_id)
    if record and record["solved"]:
        return f":green-badge[:material/check: Solved · {record['points']} pts]"
    if record and (record["attempts"] or record["hints_used"]):
        return ":orange-badge[:material/pending: In progress]"
    return ":gray-badge[Not started]"


def case_card(case, brief_length=150, details=False):
    """One case as a bordered card with a link into the investigation."""
    with st.container(border=True, height="stretch"):
        st.caption(f"CASE {case['number']} · {case['codename']}")
        st.subheader(case["title"], anchor=False)
        st.markdown(f":violet-badge[:material/signal_cellular_alt: {case['difficulty']}] "
                    f":gray-badge[{len(case['evidence'])} evidence cards] {status_badge(case['id'])}")
        brief = case["brief"]
        st.write(brief if len(brief) <= brief_length else brief[:brief_length].rstrip() + "…")
        if details:
            st.markdown(f"**Specimen:** {case['specimen']}  \n"
                        f"**Exposure:** {case['exposure']}  \n"
                        f"**Duration:** {case['duration']}")
        open_case_link(case["id"], label="Open case file")


# ---------------------------------------------------------------------------
# The sidebar: the detective's notebook, visible on every page
# ---------------------------------------------------------------------------
def sidebar():
    s = prog.summary(progress())
    with st.sidebar:
        st.subheader(":material/badge: Detective's notebook", anchor=False)
        st.metric("Detective score", s["score"], border=True)
        st.progress(s["cases_solved"] / s["cases_total"],
                    text=f"Cases solved: {s['cases_solved']} / {s['cases_total']}")
        col1, col2 = st.columns(2)
        col1.metric("Hints used", s["hints_used"])
        quiz = s["quiz"]
        col2.metric("Quiz", f"{quiz['score']}/{quiz['total']}" if quiz else "—")

        next_case = prog.next_unsolved(progress())
        if next_case:
            label = "Start investigation" if s["cases_solved"] == 0 else \
                f"Continue: Case {CASE_BY_ID[next_case]['number']}"
            st.page_link(INVESTIGATION_PAGE, label=label, icon=":material/search:",
                         query_params={"case": next_case})
        st.page_link("views/debrief.py", label="My case report", icon=":material/assignment:")
        st.divider()
        st.caption("Educational simulation. Every case, compound and number is simulated "
                   "and is not a clinical or real-world toxicology assessment.")
