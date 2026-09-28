"""
get_data.py — download the real toxicity datasets and build the file the Data Lab uses.

Run it from the project folder:

    pip install -r requirements-data.txt        # rdkit + kagglehub (only needed for this script)
    python scripts/get_data.py                  # Tox21 from Kaggle, LD50 from GitHub
    python scripts/get_data.py --direct         # skip Kaggle, use direct links for everything
    python scripts/get_data.py --ld50 tdc       # use the TDC LD50 set on Kaggle instead of LDToxDB

What it does, step by step:
  1. Tox21 (7,831 compounds × 12 yes/no toxicity assays)
       Kaggle:  epicskills/tox21-dataset            (downloaded with kagglehub)
       Direct:  the MoleculeNet copy hosted by DeepChem
  2. Rat oral LD50 values
       LDToxDB (default, 13,329 compounds, MIT licence) from the AI4PFAS project on GitHub
       or the TDC "Acute Toxicity LD50" set on Kaggle (iapetus509/therapeutics-data-commons-acute-toxicity-ld50)
  3. Matches the two by chemical structure with RDKit and writes
       data/real/tox21.csv         the Tox21 table as downloaded
       data/real/tox21_ld50.csv    one row per compound found in both, ready for the website

The website itself does not need RDKit or kagglehub; it only reads the two CSV files.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "real"

ASSAYS = ["NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER", "NR-ER-LBD", "NR-PPAR-gamma",
          "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"]

KAGGLE_TOX21 = "epicskills/tox21-dataset"
KAGGLE_TDC_LD50 = "iapetus509/therapeutics-data-commons-acute-toxicity-ld50"
DIRECT_TOX21 = [
    "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz",
    "https://raw.githubusercontent.com/batmanlab/drugEmbedding/master/DrugEmbedding/data/tox21/tox21.csv",
]
DIRECT_LDTOXDB = "https://raw.githubusercontent.com/AI4PFAS/AI4PFAS/main/data/ldtoxdb-raw.csv"

SMILES_COLUMNS = ["smiles", "SMILES", "Smiles", "SMI", "smi", "Drug", "canonical_smiles"]
LD50_COLUMNS = ["NeglogLD50", "Y", "LD50", "ld50", "label"]


# --------------------------------------------------------------------------- download helpers
def kaggle_csvs(handle):
    """Download a Kaggle dataset with kagglehub and return every CSV file inside it."""
    import kagglehub                                    # pip install kagglehub
    folder = Path(kagglehub.dataset_download(handle))   # returns the local folder
    print(f"  downloaded {handle} to {folder}")
    return sorted(folder.rglob("*.csv")) + sorted(folder.rglob("*.csv.gz"))


def first_column(frame, candidates):
    for name in candidates:
        if name in frame.columns:
            return name
    return None


def with_ids(frame):
    """Make sure every compound has a mol_id (some copies of Tox21 on Kaggle leave it out)."""
    if "mol_id" in frame.columns:
        return frame
    frame = frame.copy()
    other = first_column(frame, ["ID", "id", "Compound ID", "compound_id"])
    ids = frame[other].astype(str) if other else [f"TOX-{i + 1}" for i in range(len(frame))]
    frame.insert(0, "mol_id", ids)
    return frame


def get_tox21(direct):
    if not direct:
        try:
            for path in kaggle_csvs(KAGGLE_TOX21):
                frame = pd.read_csv(path)
                if all(a in frame.columns for a in ASSAYS) and first_column(frame, SMILES_COLUMNS):
                    print(f"  using {path.name}")
                    return with_ids(frame)
            print("  no Tox21 table with all 12 assays found in the Kaggle download; trying direct links")
        except Exception as error:                      # no kagglehub, no internet, no token ...
            print(f"  Kaggle download failed ({error}); trying direct links")
    for url in DIRECT_TOX21:
        try:
            frame = pd.read_csv(url)                    # pandas can read straight from a web address
            print(f"  downloaded {url}")
            return frame
        except Exception as error:
            print(f"  could not read {url} ({error})")
    sys.exit("Could not download Tox21. Download it by hand from Kaggle and save it as data/real/tox21.csv")


def get_ld50(source):
    if source == "tdc":
        for path in kaggle_csvs(KAGGLE_TDC_LD50):
            frame = pd.read_csv(path)
            if first_column(frame, SMILES_COLUMNS) and first_column(frame, LD50_COLUMNS):
                print(f"  using {path.name}")
                return frame, "TDC LD50_Zhu"
        sys.exit("The Kaggle TDC download had no table with SMILES and LD50 columns.")
    frame = pd.read_csv(DIRECT_LDTOXDB)
    print(f"  downloaded {DIRECT_LDTOXDB}")
    return frame, "LDToxDB"


# --------------------------------------------------------------------------- chemistry
def structure_info(smiles):
    """Parent structure key, molecular weight and logP for one SMILES string.

    Salts and mixtures are reduced to their largest fragment (the 'parent'),
    and compounds are matched on the first block of the InChIKey, which
    describes how the atoms are connected. That lets the same compound match
    even when two databases draw its salt or stereochemistry differently.
    """
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors
    mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
    if mol is None:
        return None, np.nan, np.nan, np.nan
    parent = max(Chem.GetMolFrags(mol, asMols=True), key=lambda m: m.GetNumHeavyAtoms())
    key = Chem.MolToInchiKey(parent)[:14]
    return key, Descriptors.MolWt(parent), Crippen.MolLogP(parent), Descriptors.MolWt(mol)


def build(tox21, ld50, ld50_name):
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")

    smi = first_column(tox21, SMILES_COLUMNS)
    info = tox21[smi].apply(lambda s: pd.Series(structure_info(s), index=["key", "mw", "logp", "mw_full"]))
    tox = pd.concat([tox21[["mol_id", smi] + ASSAYS].rename(columns={smi: "smiles"}), info], axis=1)
    tox = tox.dropna(subset=["key"])
    # Some structures appear twice in Tox21; merge them (active if active in either copy).
    agg = {a: "max" for a in ASSAYS}
    agg.update({"mol_id": "first", "smiles": "first", "mw": "first", "logp": "first"})
    tox = tox.groupby("key", as_index=False).agg(agg)

    lsmi, lval = first_column(ld50, SMILES_COLUMNS), first_column(ld50, LD50_COLUMNS)
    linfo = ld50[lsmi].apply(lambda s: pd.Series(structure_info(s), index=["key", "mw", "logp", "mw_full"]))
    ld = pd.concat([ld50, linfo], axis=1).dropna(subset=["key", lval])
    ld["neglog_ld50"] = ld[lval].astype(float)                      # -log10(LD50 in mol/kg)
    ld["log_mgkg"] = np.log10(10 ** (-ld["neglog_ld50"]) * ld["mw_full"] * 1000)
    name_col = first_column(ld, ["Chem_Name", "Drug_ID", "name"])
    src_col = first_column(ld, ["Source"])
    ld_agg = {"neglog_ld50": "mean", "log_mgkg": "mean"}
    if name_col:
        ld_agg[name_col] = "first"
    if src_col:
        ld_agg[src_col] = lambda s: "/".join(sorted(set(map(str, s))))
    ld = ld.groupby("key", as_index=False).agg(ld_agg)
    ld = ld.rename(columns={name_col or "": "name", src_col or "": "ld50_source"})
    if "ld50_source" not in ld:
        ld["ld50_source"] = ld50_name

    merged = tox.merge(ld, on="key", how="inner")
    merged["n_tested"] = merged[ASSAYS].notna().sum(axis=1)
    merged["n_active"] = (merged[ASSAYS] == 1).sum(axis=1)
    merged["toxic"] = (merged["n_active"] > 0).astype(int)
    merged["ld50_mg_per_kg"] = (10 ** merged["log_mgkg"]).map(lambda x: float(f"{x:.3g}"))  # 3 significant figures
    merged["neglog_ld50"] = merged["neglog_ld50"].round(4)
    merged["mw"] = merged["mw"].round(2)
    merged["logp"] = merged["logp"].round(2)
    columns = ["mol_id", "name", "smiles", "key", "toxic", "n_active", "n_tested"] + ASSAYS + \
              ["neglog_ld50", "ld50_mg_per_kg", "ld50_source", "mw", "logp"]
    if "name" not in merged:
        merged["name"] = ""
    return merged[columns].sort_values("mol_id")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--direct", action="store_true", help="skip Kaggle and use direct links")
    parser.add_argument("--ld50", choices=["ldtoxdb", "tdc"], default="ldtoxdb", help="which LD50 dataset to use")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    print("1. Tox21")
    tox21 = get_tox21(args.direct)
    tox21.to_csv(OUT / "tox21.csv", index=False)
    print(f"   saved {len(tox21):,} compounds to data/real/tox21.csv")

    print("2. LD50")
    ld50, ld50_name = get_ld50(args.ld50)
    print(f"   {len(ld50):,} LD50 records from {ld50_name}")

    print("3. Matching the two by structure (RDKit)")
    merged = build(tox21, ld50, ld50_name)
    merged.to_csv(OUT / "tox21_ld50.csv", index=False)
    print(f"   {len(merged):,} compounds have both Tox21 results and an LD50 -> data/real/tox21_ld50.csv")


if __name__ == "__main__":
    main()
