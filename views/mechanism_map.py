"""Mechanism map: the five stages from toxic exposure to cellular effect."""

import streamlit as st

from btd import ui
from btd.analysis import mechanisms_frame
from btd.data import MECHANISM_MAP

stages = MECHANISM_MAP["stages"]

ui.page_header("Mechanism map", MECHANISM_MAP["title"], MECHANISM_MAP["intro"])

# The chain, one card per stage.
for column, stage in zip(st.columns(len(stages)), stages):
    with column.container(border=True, height="stretch"):
        st.caption(f"STAGE {stage['index']}" + ("  →" if stage["index"] < len(stages) else ""))
        st.markdown(f"**{stage['name']}**")
        st.write(stage["short"])
        st.caption(f":material/schedule: {stage['timescale']}")

choice = st.segmented_control(
    "Read a stage", [s["id"] for s in stages], default=stages[0]["id"], required=True,
    format_func=lambda sid: next(f"{s['index']}. {s['name']}" for s in stages if s["id"] == sid),
)
stage = next(s for s in stages if s["id"] == choice)

with st.container(border=True):
    st.subheader(f"Stage {stage['index']} · {stage['name']}", anchor=False)
    st.caption(f"Timescale: {stage['timescale']}")
    st.write(stage["body"])
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**What happens**")
        for line in stage["detail"]:
            st.markdown(f"- {line}")
    with c2:
        st.markdown("**The cell's defences**")
        for line in stage["defences"]:
            st.markdown(f"- {line}")
    with c3:
        st.markdown("**What the lab measures**")
        st.markdown(" ".join(f":primary-badge[{m}]" for m in stage["markers"]))

st.subheader("Mechanisms at a glance", anchor=False)
st.table(mechanisms_frame(), hide_index=True)
st.page_link("views/cell_lab.py", label="Trace each mechanism through the cell in the Cell Lab",
             icon=":material/blur_circular:")

ui.disclaimer()
