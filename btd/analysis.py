"""
analysis.py — reading the evidence the way a scientist would, with NumPy and Pandas.

Computational thinking: PATTERN RECOGNITION.
Every case hides its answer in the DIRECTION the numbers move as the dose goes
up. A falling enzyme activity with a rising substrate means inhibition; a
rising MDA with a falling membrane integrity means lipid peroxidation. The
functions below turn that idea into code: they measure how much each value
changed from the control, whether it rose or fell at every step, and how
strongly it tracks the dose.

    NumPy  -> fast maths on whole arrays at once (no loops needed)
    Pandas -> tables (DataFrames) we can filter, group and show on screen
"""

import numpy as np
import pandas as pd

from btd.data import (BIOMOLECULES, CASES, MECHANISMS, TOXIN_CATEGORIES, biomolecule_label,
                      mechanism_label)

# Changes smaller than this (in %) are treated as "no real change".
FLAT_BAND = 5


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------
def dataset_frame(dataset):
    """Turn a dataset's rows into a DataFrame: one row per exposure level,
    one column per measurement."""
    columns = [series["key"] for series in dataset["series"]]
    frame = pd.DataFrame(dataset["rows"]).set_index(dataset["xKey"])
    frame.index.name = dataset["xLabel"]
    return frame[columns]


def percent_change(values):
    """How far each value is from the control (the first value), in %.

    NumPy does the whole array in one line: [100, 82, 55, 28] -> [0, -18, -45, -72]
    """
    values = np.asarray(values, dtype=float)
    return (values / values[0] - 1) * 100


def describe_trend(values):
    """Name the pattern in one measurement across the dose levels.

    Returns (words, arrow), for example ("falls steadily", "↓").
    """
    values = np.asarray(values, dtype=float)
    change = percent_change(values)
    steps = np.diff(values)                     # change between neighbouring doses

    if np.all(np.abs(change) < FLAT_BAND):
        return "stays flat", "→"
    if np.all(steps <= 0):
        return "falls steadily", "↓"
    if np.all(steps >= 0):
        return "rises steadily", "↑"
    return "changes direction", "↕"


def dose_correlation(values):
    """Pearson correlation between dose level (0, 1, 2, 3) and the values.

    +1 means it rises perfectly with dose, -1 means it falls perfectly,
    0 means no link. A flat line has no correlation at all, so we return 0.
    """
    values = np.asarray(values, dtype=float)
    if np.std(values) == 0:
        return 0.0
    dose = np.arange(len(values))
    return float(np.corrcoef(dose, values)[0, 1])


def pattern_report(dataset):
    """One row per measurement: control, top dose, % change, trend, correlation."""
    frame = dataset_frame(dataset)
    rows = []
    for column in frame.columns:
        values = frame[column].to_numpy()
        words, arrow = describe_trend(values)
        rows.append({
            "Measurement": column,
            "Control": values[0],
            "Highest dose": values[-1],
            "Change vs control (%)": round(float(percent_change(values)[-1]), 1),
            "Pattern": f"{arrow} {words}",
            "Correlation with dose (r)": round(dose_correlation(values), 2),
        })
    return pd.DataFrame(rows)


def pattern_sentences(dataset):
    """The same pattern report written as plain sentences."""
    sentences = []
    for row in pattern_report(dataset).to_dict("records"):
        change = row["Change vs control (%)"]
        sign = "+" if change > 0 else ""
        sentences.append(
            f"**{row['Measurement']}** {row['Pattern'][2:]}: "
            f"{row['Control']:g} → {row['Highest dose']:g} ({sign}{change:g}% vs control)"
        )
    return sentences


def seed_from(text):
    """A repeatable random seed made from a piece of text (same text, same seed)."""
    return sum(ord(character) for character in text)


def simulate_replicates(dataset, n=3):
    """Simulate n laboratory replicates for every point in a dataset.

    Real experiments are repeated (usually in triplicate) and never give
    exactly the same number twice. This builds that scatter with NumPy while
    keeping the case data unchanged: the noise in each group is centred so the
    MEAN of the replicates equals the published value exactly.

    Returns an array of shape (dose levels, measurements, n).
    """
    rng = np.random.default_rng(seed_from(dataset["id"]))
    means = dataset_frame(dataset).to_numpy(dtype=float)          # (levels, measurements)
    spread = 0.04 if "%" in dataset["yLabel"] else 0.01           # 4% scatter, 1% for °C
    noise = rng.normal(0.0, 1.0, size=(*means.shape, n))
    noise = noise - noise.mean(axis=2, keepdims=True)              # centre each group on 0
    return means[..., np.newaxis] * (1 + spread * noise)


def replicate_table(dataset, n=3):
    """The simulated replicates as a readable table with mean and SD columns."""
    replicates = simulate_replicates(dataset, n)
    frame = dataset_frame(dataset)
    rows = []
    for i, level in enumerate(frame.index):
        for j, measurement in enumerate(frame.columns):
            values = replicates[i, j]
            row = {"Exposure": level, "Measurement": measurement}
            for k, value in enumerate(values, start=1):
                row[f"Rep {k}"] = round(float(value), 1)
            row["Mean"] = round(float(values.mean()), 1)
            row["SD"] = round(float(values.std(ddof=1)), 1)
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Library tables
# ---------------------------------------------------------------------------
def toxin_frame():
    """Flatten the toxin library (categories -> entries) into one table."""
    rows = []
    for category in TOXIN_CATEGORIES:
        for entry in category["entries"]:
            rows.append({
                "Toxin": entry["name"],
                "Category": category["name"],
                "category_id": category["id"],
                "Target": biomolecule_label(entry["target"]),
                "target_id": entry["target"],
                "Target detail": entry["targetNote"],
                "Mechanism of action": entry["mechanism"],
                "Consequence": entry["consequence"],
                "Markers": ", ".join(entry["markers"]),
            })
    return pd.DataFrame(rows)


def filter_toxins(frame, category_ids=None, target_ids=None, text=""):
    """Filter the toxin table with boolean masks (True = keep the row)."""
    keep = pd.Series(True, index=frame.index)
    if category_ids:
        keep &= frame["category_id"].isin(category_ids)
    if target_ids:
        keep &= frame["target_id"].isin(target_ids)
    if text:
        haystack = frame["Toxin"] + " " + frame["Mechanism of action"] + " " + frame["Markers"]
        keep &= haystack.str.contains(text, case=False, regex=False)
    return frame[keep]


def target_counts(frame):
    """How many toxins in a table hit each biomolecule class (all four listed)."""
    order = [b["label"] for b in BIOMOLECULES]
    return frame.groupby("Target").size().reindex(order, fill_value=0)


def mechanisms_frame():
    return pd.DataFrame([{
        "Mechanism": m["label"],
        "Main target": biomolecule_label(m["biomolecule"]),
        "What happens": m["oneLine"],
        "Tell-tale sign": m["tell"],
    } for m in MECHANISMS])


def biomolecule_compare_frame():
    return pd.DataFrame([{
        "Biomolecule": f"{b['emoji']} {b['label']}",
        "Built from": b["builtFrom"],
        "Key job": b["keyJob"],
        "Found in": ", ".join(b["whereInCell"]),
    } for b in BIOMOLECULES])


def case_record_frame(progress):
    """The player's case record as a table (used on the case report page)."""
    rows = []
    for case in CASES:
        record = progress["cases"].get(case["id"], {})
        solved = record.get("solved", False)
        rows.append({
            "Case": case["number"],
            "Title": case["title"],
            "Difficulty": case["difficulty"],
            "Solved": solved,
            "Attempts": record.get("attempts", 0),
            "Hints": record.get("hints_used", 0),
            "Points": record.get("points", 0) if solved else 0,
            "Mechanism": mechanism_label(case["solution"]["mechanism"]) if solved else "—",
        })
    return pd.DataFrame(rows)


def quiz_frame(result):
    """One row per quiz question: what was chosen, what was right."""
    rows = []
    for number, r in enumerate(result["results"], start=1):
        rows.append({
            "Q": number,
            "Topic": r["topic"],
            "Your answer": r["options"][r["chosen"]] if r["chosen"] is not None else "—",
            "Correct answer": r["options"][r["answer"]],
            "Correct": r["correct"],
        })
    return pd.DataFrame(rows)
