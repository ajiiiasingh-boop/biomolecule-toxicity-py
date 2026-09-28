"""
btd — the "engine" of Biomolecule Toxicity Detective.

This package holds all the logic and none of the screens. The website
(app.py + views/) and the terminal game (play_in_terminal.py) both import
from here, so the rules of the game are written exactly once.

    data.py      loads the biology from the JSON files        (standard library only)
    scoring.py   grades answers, hints and the quiz            (standard library only)
    progress.py  keeps the detective's score and case record   (standard library only)
    analysis.py  reads the datasets like a scientist would     (NumPy + Pandas)
    drawing.py   draws the charts and the cell diagram         (Matplotlib)
    ui.py        small Streamlit helpers shared by every page  (Streamlit)

Computational thinking: this split is DECOMPOSITION. One big problem
("build a toxicity investigation game") becomes six small modules, each with
one job that can be written, tested and explained on its own.
"""
