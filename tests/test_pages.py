"""Runs every page of the website without a browser (Streamlit's AppTest),
then plays Case 01 from start to finish."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
PAGES = ["home", "case_files", "investigation", "debrief", "biomolecules", "toxin_library", "data_lab",
         "quiz", "about", "mechanism_map", "cell_lab", "python_lab"]


class TestPages(unittest.TestCase):
    def test_every_page_runs_without_errors(self):
        app = AppTest.from_file(APP, default_timeout=60)
        app.run()
        for name in PAGES:
            app.switch_page(f"views/{name}.py")
            app.run()
            self.assertEqual(len(app.exception), 0, f"{name}: {[e.value for e in app.exception]}")

    def test_play_case_one(self):
        app = AppTest.from_file(APP, default_timeout=60)
        app.run()
        app.switch_page("views/investigation.py")
        app.run()
        for card in "ABCD":
            app.button(key=f"ev-case-01-{card}").click()
            app.run()
        app.radio(key="q1-case-01-1").set_value("protein")
        app.radio(key="q2-case-01-1").set_value("enzyme-inhibition")
        app.run()
        submit = next(b for b in app.button if b.label == "Submit conclusion")
        submit.click()
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state.progress["score"], 120)
        self.assertTrue(app.session_state.progress["cases"]["case-01"]["solved"])


if __name__ == "__main__":
    unittest.main()
