"""
BIOMOLECULE TOXICITY DETECTIVE — Python edition
================================================

Run it with:      streamlit run app.py
(or double-click run.py, which installs the libraries and starts it for you)

This file is the front door of the website. It sets up the page, lists every
page in the navigation bar, and draws the detective's notebook in the sidebar.
Each page lives in its own file in views/, and all the logic lives in btd/.
"""

import streamlit as st

from btd import ui

st.set_page_config(
    page_title="Biomolecule Toxicity Detective",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="auto",      # open on computers, tucked away on phones
)
ui.init_state()

# Every page of the site. The dictionary keys become the menu sections.
pages = {
    "": [
        st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
        st.Page("views/case_files.py", title="Case Files", icon=":material/folder_open:"),
        st.Page("views/biomolecules.py", title="Biomolecules", icon=":material/genetics:"),
        st.Page("views/toxin_library.py", title="Toxin Library", icon=":material/science:"),
        st.Page("views/quiz.py", title="Quiz", icon=":material/quiz:"),
        st.Page("views/data_lab.py", title="Data Lab", icon=":material/query_stats:"),
        st.Page("views/about.py", title="About", icon=":material/info:"),
        # Reached through links and buttons, so they are hidden from the menu.
        st.Page("views/investigation.py", title="Investigation", icon=":material/search:",
                visibility="hidden"),
        st.Page("views/debrief.py", title="Case Report", icon=":material/assignment:",
                visibility="hidden"),
    ],
    "Explore": [
        st.Page("views/mechanism_map.py", title="Mechanism Map", icon=":material/account_tree:"),
        st.Page("views/cell_lab.py", title="Cell Lab", icon=":material/blur_circular:"),
        st.Page("views/python_lab.py", title="Python Lab (CT)", icon=":material/code:"),
    ],
}

current_page = st.navigation(pages, position="top")
current_page.run()

# Drawn after the page, so the score already includes anything the page just did.
ui.sidebar()
