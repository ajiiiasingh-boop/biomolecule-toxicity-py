"""Toxin library: what each class of toxicant does inside a cell, filterable with Pandas."""

import streamlit as st

from btd import ui
from btd.analysis import filter_toxins, target_counts, toxin_frame
from btd.data import BIOMOLECULE_BY_ID, BIOMOLECULES, TOXIN_CATEGORIES, toxin_entry_count
from btd.drawing import target_bar_chart

ui.page_header("Toxin library", "What the toxicant does to the molecule",
               f"{toxin_entry_count()} classes of toxicant in {len(TOXIN_CATEGORIES)} groups, each "
               "traced to the biomolecule it damages and the markers that reveal it.")
st.info("This library describes mechanisms of action inside a cell, for learning. It does not "
        "describe how to obtain, prepare, concentrate or handle any substance.",
        icon=":material/shield:")

table = toxin_frame()                       # every entry in one Pandas DataFrame

f1, f2 = st.columns(2)
categories = f1.pills("Category", [c["id"] for c in TOXIN_CATEGORIES], selection_mode="multi",
                      format_func=lambda cid: next(c["name"] for c in TOXIN_CATEGORIES if c["id"] == cid))
targets = f2.pills("Target biomolecule", [b["id"] for b in BIOMOLECULES], selection_mode="multi",
                   format_func=lambda bid: f"{BIOMOLECULE_BY_ID[bid]['emoji']} {BIOMOLECULE_BY_ID[bid]['label']}")
search = st.text_input("Search names, mechanisms and markers", placeholder="e.g. thiol, DNA adduct, ATP",
                       icon=":material/search:")

view = filter_toxins(table, categories, targets, search.strip())
st.caption(f"Showing {len(view)} of {len(table)} entries")

tab_cards, tab_table, tab_chart = st.tabs(["Cards", "Table", "Chart"])

with tab_cards:
    if view.empty:
        st.info("Nothing matches those filters.")
    rows = view.to_dict("records")
    for start in range(0, len(rows), 2):
        for column, entry in zip(st.columns(2), rows[start:start + 2]):
            with column.container(border=True, height="stretch"):
                st.markdown(f"#### {entry['Toxin']}")
                st.markdown(f":gray-badge[{entry['Category']}] {ui.biomolecule_badge(entry['target_id'])}")
                st.caption(f"Target: {entry['Target detail']}")
                st.markdown(f"**Mechanism.** {entry['Mechanism of action']}")
                st.markdown(f"**Consequence.** {entry['Consequence']}")
                st.markdown("**Markers:** " + " ".join(f":primary-badge[{m.strip()}]"
                                                       for m in entry["Markers"].split(",")))

with tab_table:
    st.dataframe(view.drop(columns=["category_id", "target_id"]), hide_index=True)
    st.download_button("Download this table (.csv)",
                       view.drop(columns=["category_id", "target_id"]).to_csv(index=False),
                       file_name="toxin-library.csv", mime="text/csv", icon=":material/download:")

with tab_chart:
    st.write("Which biomolecule do the toxins in the current view attack? "
             "(`groupby` in Pandas, bars in Matplotlib)")
    st.pyplot(target_bar_chart(target_counts(view)))

st.subheader("The four categories", anchor=False)
for category in TOXIN_CATEGORIES:
    with st.expander(f"{category['name']} — {category['tagline']}"):
        st.write(category["overview"])
        st.caption(", ".join(e["name"] for e in category["entries"]))

ui.disclaimer()
