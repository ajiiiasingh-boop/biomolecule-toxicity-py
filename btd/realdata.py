"""
realdata.py — the real-data investigation: Tox21 toxicity labels compared with rat LD50 values.

The question (from our problem statement):
    Take a chemical toxicity dataset (Tox21). How many compounds are toxic and how many
    are non-toxic? Compare the average toxicity value (LD50) of the two groups.
    Is there a visible difference?

Tox21 only says yes/no for 12 laboratory assays; it has no LD50. So the LD50 values come
from a second dataset (LDToxDB) and the two are matched by chemical structure in
scripts/get_data.py. This module only reads the two finished CSV files in data/real/,
so it needs nothing beyond NumPy and Pandas.

Units: `neglog_ld50` is -log10(LD50 in mol/kg). A HIGHER number means a SMALLER lethal
dose, i.e. a MORE toxic compound. A difference of 0.30 means about 2 times more toxic
(10 ** 0.30 ≈ 2).
"""

from pathlib import Path

import numpy as np
import pandas as pd

REAL_DIR = Path(__file__).resolve().parent.parent / "data" / "real"
TOX21_FILE = REAL_DIR / "tox21.csv"
MERGED_FILE = REAL_DIR / "tox21_ld50.csv"

# The 12 Tox21 assays, in plain words.
ASSAYS = {
    "NR-AR": "Androgen receptor (full length)",
    "NR-AR-LBD": "Androgen receptor, ligand-binding domain",
    "NR-AhR": "Aryl hydrocarbon receptor",
    "NR-Aromatase": "Aromatase enzyme inhibition",
    "NR-ER": "Estrogen receptor alpha (full length)",
    "NR-ER-LBD": "Estrogen receptor, ligand-binding domain",
    "NR-PPAR-gamma": "PPAR-gamma receptor",
    "SR-ARE": "Antioxidant response element (oxidative stress)",
    "SR-ATAD5": "ATAD5 (DNA damage / genotoxicity)",
    "SR-HSE": "Heat shock response (protein stress)",
    "SR-MMP": "Mitochondrial membrane potential",
    "SR-p53": "p53 pathway (DNA damage response)",
}
ASSAY_IDS = list(ASSAYS)

# GHS acute oral toxicity categories (LD50 in mg/kg body weight).
GHS_BINS = [0, 5, 50, 300, 2000, 5000, np.inf]
GHS_LABELS = ["Cat 1 · ≤5 · fatal", "Cat 2 · 5–50 · fatal", "Cat 3 · 50–300 · toxic",
              "Cat 4 · 300–2000 · harmful", "Cat 5 · 2000–5000 · may be harmful", "Not classified · >5000"]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_tox21(path=TOX21_FILE):
    """The Tox21 table: one row per compound, 12 assay columns (1 active, 0 inactive, blank untested)."""
    return pd.read_csv(path)


def load_merged(path=MERGED_FILE):
    """Compounds that have both Tox21 results and an LD50 value."""
    return pd.read_csv(path)


def available():
    return TOX21_FILE.exists() and MERGED_FILE.exists()


# ---------------------------------------------------------------------------
# Step 1: how many are toxic?
# ---------------------------------------------------------------------------
def add_labels(tox21):
    """Label each compound: toxic = active (1) in at least one of the 12 assays."""
    frame = tox21.copy()
    assays = frame[ASSAY_IDS]
    frame["n_tested"] = assays.notna().sum(axis=1)       # how many assays it was tested in
    frame["n_active"] = (assays == 1).sum(axis=1)        # how many of them it was active in
    frame["toxic"] = (frame["n_active"] > 0).astype(int)
    return frame


def label_counts(labelled):
    """The headline numbers for the toxic / non-toxic split."""
    toxic = int(labelled["toxic"].sum())
    total = len(labelled)
    non_toxic = total - toxic
    fully_tested = int(((labelled["toxic"] == 0) & (labelled["n_tested"] == len(ASSAY_IDS))).sum())
    return {"total": total, "toxic": toxic, "non_toxic": non_toxic,
            "toxic_pct": round(toxic / total * 100, 1), "non_toxic_fully_tested": fully_tested}


def assay_table(tox21):
    """Active / inactive / not tested counts for each assay."""
    assays = tox21[ASSAY_IDS]
    table = pd.DataFrame({
        "Assay": ASSAY_IDS,
        "What it detects": [ASSAYS[a] for a in ASSAY_IDS],
        "Active (toxic)": [(assays[a] == 1).sum() for a in ASSAY_IDS],
        "Inactive": [(assays[a] == 0).sum() for a in ASSAY_IDS],
        "Not tested": [assays[a].isna().sum() for a in ASSAY_IDS],
    })
    tested = table["Active (toxic)"] + table["Inactive"]
    table["% active"] = (table["Active (toxic)"] / tested * 100).round(1)
    return table


# ---------------------------------------------------------------------------
# Step 2: compare the average LD50 of the two groups
# ---------------------------------------------------------------------------
def split(merged, column="neglog_ld50", label="toxic"):
    """The measurement for the toxic group and for the non-toxic group, as NumPy arrays."""
    values = merged[[label, column]].dropna()
    return values.loc[values[label] == 1, column].to_numpy(float), values.loc[values[label] == 0, column].to_numpy(float)


def group_stats(merged, column="neglog_ld50", label="toxic", names=("Toxic in Tox21", "Non-toxic in Tox21")):
    """n, mean, median and standard deviation for both groups."""
    toxic, safe = split(merged, column, label)
    rows = []
    for name, values in zip(names, (toxic, safe)):
        rows.append({"Group": name, "Compounds": len(values), "Mean": values.mean(),
                     "Median": np.median(values), "Std. dev.": values.std(ddof=1)})
    return pd.DataFrame(rows)


def cohens_d(a, b):
    """Effect size: the difference in means measured in standard deviations.

    About 0.2 is small, 0.5 medium, 0.8 large.
    """
    pooled = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2)
    return float((np.mean(a) - np.mean(b)) / pooled)


def permutation_test(a, b, n=10_000, seed=21):
    """Could a gap this big appear by chance?

    Shuffle the toxic / non-toxic labels n times and count how often the shuffled
    groups differ by at least as much as the real ones. That fraction is the p-value.
    """
    rng = np.random.default_rng(seed)
    observed = np.mean(a) - np.mean(b)
    pooled = np.concatenate([a, b])
    count = 0
    for _ in range(n):
        rng.shuffle(pooled)
        diff = pooled[:len(a)].mean() - pooled[len(a):].mean()
        if abs(diff) >= abs(observed):
            count += 1
    return float(observed), (count + 1) / (n + 1)       # +1 so the p-value is never exactly 0


def compare(merged, column="neglog_ld50", label="toxic", n_permutations=10_000):
    """Everything needed to answer 'is there a visible difference?' in one dictionary."""
    toxic, safe = split(merged, column, label)
    diff, p = permutation_test(toxic, safe, n=n_permutations)
    result = {
        "n_toxic": len(toxic), "n_non_toxic": len(safe),
        "mean_toxic": float(toxic.mean()), "mean_non_toxic": float(safe.mean()),
        "median_toxic": float(np.median(toxic)), "median_non_toxic": float(np.median(safe)),
        "difference": diff, "cohens_d": cohens_d(toxic, safe), "p_value": p,
        "n_permutations": n_permutations,
    }
    if column == "neglog_ld50":
        result["fold"] = float(10 ** diff)               # how many times more toxic, on average
    return result


def effect_size_word(d):
    d = abs(d)
    return "large" if d >= 0.8 else "medium" if d >= 0.5 else "small-to-medium" if d >= 0.3 else \
        "small" if d >= 0.2 else "negligible"


def conclusion(result, measure="−log(LD50)"):
    """A plain-English answer to the question, built from the numbers."""
    p, d = result["p_value"], result["cohens_d"]
    real = p < 0.05 and abs(d) >= 0.2
    higher = "higher" if result["difference"] > 0 else "lower"
    opening = "Yes." if real else "Not clearly."
    text = (f"{opening} The toxic group's average {measure} is {higher} "
            f"({result['mean_toxic']:.2f} vs {result['mean_non_toxic']:.2f})")
    if "fold" in result and result["difference"] > 0:
        text += (f", which means a lower lethal dose: about {result['fold']:.1f} times more toxic on average")
    chance = "is very unlikely to be chance" if p < 0.001 else "is unlikely to be chance" if p < 0.05 else \
        "could easily be chance"
    text += (f". A gap this size {chance} (permutation p ≈ {p:.4f}), and the effect is "
             f"{effect_size_word(d)} (Cohen's d = {d:.2f})")
    text += ", so the two groups still overlap a lot." if abs(d) < 0.8 else "."
    return text


# ---------------------------------------------------------------------------
# Step 3: which assays matter most?
# ---------------------------------------------------------------------------
def assay_effects(merged, n_permutations=2_000):
    """For each assay: average −log(LD50) of its actives minus its inactives."""
    rows = []
    for assay in ASSAY_IDS:
        active = merged.loc[merged[assay] == 1, "neglog_ld50"].to_numpy(float)
        inactive = merged.loc[merged[assay] == 0, "neglog_ld50"].to_numpy(float)
        diff, p = permutation_test(active, inactive, n=n_permutations, seed=len(assay))
        rows.append({"Assay": assay, "What it detects": ASSAYS[assay], "Active": len(active),
                     "Inactive": len(inactive), "Difference": round(diff, 3),
                     "Times more toxic": round(10 ** diff, 2), "p-value": p})
    return pd.DataFrame(rows).sort_values("Difference", ascending=False, ignore_index=True)


def ghs_table(merged):
    """How many compounds of each group fall in each GHS acute oral toxicity category."""
    category = pd.cut(merged["ld50_mg_per_kg"], bins=GHS_BINS, labels=GHS_LABELS)
    table = pd.crosstab(category, merged["toxic"].map({1: "Toxic in Tox21", 0: "Non-toxic in Tox21"}))
    table = table.reindex(columns=["Toxic in Tox21", "Non-toxic in Tox21"], fill_value=0)
    table.index.name = "GHS category · LD50 mg/kg"
    table.columns.name = None
    return table


# ---------------------------------------------------------------------------
# Any dataset: the same comparison on a table the user uploads
# ---------------------------------------------------------------------------
def guess_columns(frame):
    """Suggest a yes/no label column and a numeric measure column in an unknown table."""
    binary, numeric = [], []
    for column in frame.columns:
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        if len(values) < max(10, len(frame) * 0.5):
            continue
        if set(np.unique(values)) <= {0, 1}:
            binary.append(column)
        else:
            numeric.append(column)
    return binary, numeric
