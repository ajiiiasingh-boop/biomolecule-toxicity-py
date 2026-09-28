"""About page: what the project is, what it is not, and how it is built."""

import streamlit as st

from btd import ui
from btd.data import BIOMOLECULES, CASES, DISCLAIMER, QUIZ, toxin_entry_count

ui.page_header("About this project", "What this is, and what it is not",
               "An interactive teaching piece about biomolecular toxicology, built as an "
               "investigation rather than a set of pages to read.")

st.warning(f"**Educational simulation — please read.** {DISCLAIMER}", icon=":material/school:")
c1, c2, c3 = st.columns(3)
c1.write("Every case, specimen, compound code and numerical value here is invented. The datasets "
         "were written by hand to behave the way real dose–response data behaves, so reading them "
         "teaches something transferable — but they are not measurements and are not drawn from "
         "any publication.")
c2.write("The biology is simplified on purpose. Real lesions overlap: a toxicant that peroxidises "
         "lipids will also damage proteins and DNA. Each case here is built around one dominant "
         "mechanism so the reasoning can be learned in isolation first.")
c3.write("Nothing here is clinical, diagnostic or regulatory guidance, and nothing here describes "
         "how to obtain, prepare, concentrate or handle any substance. The toxin library covers "
         "mechanisms of action inside a cell and stops there.")

st.subheader("Why it is built as a game", anchor=False)
st.write("Toxicology is usually taught as a list: here are the mechanisms, here are the markers, "
         "here are the consequences. In practice an investigator meets it in the reverse order — "
         "something is wrong with a cell, and you work backwards to the molecule. So the cases "
         "hand over the evidence in the order it would actually arrive: an observation, a dataset, "
         "a structural clue, an effect. A wrong conclusion sends you back to the specific piece of "
         "evidence that rules it out instead of simply being marked incorrect.")

st.subheader("What is in it", anchor=False)
m = st.columns(4)
m[0].metric("Investigation cases", len(CASES), border=True)
m[1].metric("Database entries", len(BIOMOLECULES), border=True)
m[2].metric("Toxin library entries", toxin_entry_count(), border=True)
m[3].metric("Quiz questions", len(QUIZ), border=True)

st.subheader("Biology meets computational thinking", anchor=False)
b1, b2 = st.columns(2, gap="large")
with b1.container(border=True, height="stretch"):
    st.markdown("**The biology** (unchanged from the web version)")
    st.write("Four biomolecule classes — DNA/RNA, proteins, lipids, carbohydrates — and six "
             "mechanisms of toxic damage: enzyme inhibition, oxidative DNA damage, lipid "
             "peroxidation, protein denaturation, metabolic interference and nucleic-acid "
             "intercalation. Each case walks from exposure to cellular effect.")
with b2.container(border=True, height="stretch"):
    st.markdown("**The computational thinking**")
    st.write("Decomposition into modules, pattern recognition on dose–response data with NumPy, "
             "abstraction of every case into one data format, and a grading algorithm that "
             "marks every answer the same way. The Python Lab page shows each one with the real code.")
st.page_link("views/python_lab.py", label="Open the Python Lab", icon=":material/code:")

st.subheader("How it is built", anchor=False)
st.write("The whole project is written in Python. Streamlit turns the Python scripts into web "
         "pages, so there is no separate HTML, CSS or JavaScript to write. The biology lives in "
         "JSON data files; a small engine (the btd package) loads it, grades answers and keeps the "
         "score; NumPy and Pandas analyse the datasets; Matplotlib draws the charts and the cell. "
         "Because Streamlit runs the Python on the server and sends only the finished page to the "
         "browser, the answer keys never reach the player's browser.")
st.markdown(" ".join(f":primary-badge[{name}]" for name in
                     ["Python 3", "Streamlit", "Pandas", "NumPy", "Matplotlib", "Graphviz (via Streamlit)",
                      "JSON data", "unittest"]))

with st.container(border=True):
    st.caption("THIS SESSION")
    st.write("No account and no personal data. Your score lives only in this browser tab while it "
             "is open (Streamlit session state). Download your case report from the Case Report "
             "page to keep a copy.")

ui.disclaimer()
