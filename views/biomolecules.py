"""Biomolecule database: the four classes, how toxicity hits each one, and its markers."""

import streamlit as st

from btd import ui
from btd.analysis import biomolecule_compare_frame
from btd.data import BIOMOLECULE_BY_ID, BIOMOLECULES, CELL_PART_BY_ID, MECHANISMS

ui.page_header("Biomolecule database", "Four classes, four ways to fail",
               "What each biomolecule is built from, what it does, and the fingerprints it leaves "
               "when a toxicant damages it.")

# The link that opened this page may name a biomolecule (?b=lipid). The
# switcher and the link are kept in step, the same way as on the case page.
ids = [b["id"] for b in BIOMOLECULES]
wanted = st.query_params.get("b")
st.session_state.bm_choice = wanted if wanted in ids else ids[0]


def pick():
    st.query_params["b"] = st.session_state.bm_choice


choice = st.segmented_control(
    "Biomolecule", ids, key="bm_choice", required=True, on_change=pick,
    format_func=lambda bid: f"{BIOMOLECULE_BY_ID[bid]['emoji']} {BIOMOLECULE_BY_ID[bid]['label']}",
    label_visibility="collapsed",
)
b = BIOMOLECULE_BY_ID[choice]
color = ui.CHANNEL_COLOR[b["id"]]

with st.container(border=True):
    st.markdown(f"## {b['emoji']} :{color}[{b['label']}]")
    st.markdown(f"*{b['tagline']}*  ·  :gray-badge[{b['short']}]")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Built from**  \n{b['builtFrom']}")
    c2.markdown(f"**Key job**  \n{b['keyJob']}")
    places = " ".join(f":{color}-badge[{CELL_PART_BY_ID[p]['name'] if p in CELL_PART_BY_ID else p}]"
                      for p in b["whereInCell"])
    c3.markdown(f"**Found in**  \n{places}")
    st.write(b["summary"])

tab_hits, tab_structure, tab_repair, tab_markers, tab_mech = st.tabs(
    ["How toxicity hits it", "Structure", "Repair and defence", "Markers", "Mechanisms"])

with tab_hits:
    for left_right in range(0, len(b["howToxicityHits"]), 2):
        for column, hit in zip(st.columns(2), b["howToxicityHits"][left_right:left_right + 2]):
            with column.container(border=True, height="stretch"):
                st.markdown(f"**{hit['title']}**")
                st.write(hit["body"])

with tab_structure:
    for line in b["structure"]:
        st.markdown(f"- {line}")

with tab_repair:
    for line in b["repair"]:
        st.markdown(f"- {line}")

with tab_markers:
    st.write("Laboratory read-outs that show this class has been damaged:")
    st.markdown(" ".join(f":{color}-badge[{marker}]" for marker in b["markers"]))

with tab_mech:
    related = [m for m in MECHANISMS if m["biomolecule"] == b["id"]]
    for mechanism in related:
        with st.container(border=True):
            st.markdown(f"**{mechanism['label']}**")
            st.write(mechanism["oneLine"])
            st.caption(f"Tell-tale sign: {mechanism['tell']}")

st.subheader("Compare all four", anchor=False)
st.table(biomolecule_compare_frame(), hide_index=True)

ui.disclaimer()
