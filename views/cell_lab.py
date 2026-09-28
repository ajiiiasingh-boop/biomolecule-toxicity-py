"""Cell Lab: a Matplotlib drawing of the cell, with the route each mechanism takes."""

import streamlit as st

from btd import ui
from btd.data import CASE_BY_ID, CELL_MAP, CELL_PART_BY_ID
from btd.drawing import cell_diagram

routes = CELL_MAP["routes"]

ui.page_header("Cell lab", "Where the damage happens",
               "Pick a mechanism to trace the path a toxicant takes through the cell, or pick one "
               "part of the cell to see what it does and what toxicity does to it.")

left, right = st.columns([1.9, 1], gap="large")

with right:
    route_id = st.radio("Trace a mechanism", [None] + list(routes),
                        format_func=lambda r: "Whole cell (no route)" if r is None else routes[r]["label"])
    part_id = st.selectbox("Inspect one part of the cell", list(CELL_PART_BY_ID), index=None,
                           format_func=lambda p: CELL_PART_BY_ID[p]["name"],
                           placeholder="Choose a part…")

    if route_id:
        route = routes[route_id]
        with st.container(border=True):
            st.markdown(f"**{route['label']}**")
            for step, pid in enumerate(route["path"], start=1):
                st.markdown(f":primary-badge[{step}] {CELL_PART_BY_ID[pid]['name']}")
            st.write(route["note"])

    if part_id:
        part = CELL_PART_BY_ID[part_id]
        with st.container(border=True):
            st.markdown(f"**{part['name']}** {ui.biomolecule_badge(part['biomolecule'])}")
            st.markdown(f"**What it does.** {part['function']}")
            st.markdown(f"**Under toxicity.** {part['underToxicity']}")
            cases = [CASE_BY_ID[c] for c in part["caseIds"] if c in CASE_BY_ID]
            if cases:
                st.caption("Appears in: " + ", ".join(f"Case {c['number']} ({c['title']})" for c in cases))

    if not route_id and not part_id:
        st.info("Nothing selected yet — the whole cell is shown.", icon=":material/touch_app:")

with left:
    path = routes[route_id]["path"] if route_id else None
    st.pyplot(cell_diagram(route=path, selected=part_id))
    st.caption("Schematic, not to scale. Colours follow the biomolecule classes: blue DNA/RNA, "
               "green proteins, red lipids, gold carbohydrates.")

ui.disclaimer()
