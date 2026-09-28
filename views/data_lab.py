"""Data Lab: our problem statement answered with real data (Tox21 + rat LD50)."""

import pandas as pd
import streamlit as st

from btd import realdata as rd
from btd import ui
from btd.drawing import assay_active_chart, assay_effect_chart, ld50_box_chart, ld50_histogram_chart

ui.page_header("Data Lab · real data", "Are toxic compounds really more lethal?",
               "Our problem statement, answered with two real, public datasets: Tox21 for "
               "toxic / non-toxic, and rat oral LD50 values for how much it takes to kill.")

with st.container(border=True):
    st.caption("THE PROBLEM STATEMENT")
    st.markdown("*Take any chemical toxicity dataset from Kaggle or the UCI repository (Tox21 is a good "
                "one to start with). Find out how many compounds are toxic and how many are non-toxic. "
                "Then compare the average toxicity value (LD50 or whatever measure your dataset has) for "
                "the two groups. Is there a visible difference?*")

if not rd.available():
    st.error("The data files are missing. Run `python scripts/get_data.py` from the project folder to "
             "download them into `data/real/`.", icon=":material/database_off:")
    st.stop()


@st.cache_data
def tox21_labelled():
    return rd.add_labels(rd.load_tox21())


@st.cache_data
def merged():
    return rd.load_merged()


@st.cache_data
def comparison(column):
    return rd.compare(merged(), column)


@st.cache_data
def effects():
    return rd.assay_effects(merged())


tox = tox21_labelled()
counts = rd.label_counts(tox)
data = merged()

# ---------------------------------------------------------------- 1. get the data
st.header("1 · Get the data", anchor=False)
st.write("We need two tables. **Tox21** says whether each compound was toxic in 12 laboratory tests, "
         "but it has no LD50. So we add a second table of **rat oral LD50** values and join the two by "
         "chemical structure.")
d1, d2 = st.columns(2)
with d1.container(border=True, height="stretch"):
    st.markdown("**Tox21** :gray-badge[7,831 compounds] :gray-badge[12 assays]")
    st.write("From the US Tox21 programme (NIH, EPA, FDA). Each compound was tested in cell-based "
             "assays for nuclear-receptor and stress-response effects: 1 = active (toxic), "
             "0 = inactive, blank = not tested.")
    st.markdown("Kaggle: `epicskills/tox21-dataset` · also in MoleculeNet / DeepChem")
with d2.container(border=True, height="stretch"):
    st.markdown("**LDToxDB** :gray-badge[13,329 compounds] :gray-badge[rat, oral]")
    st.write("Measured acute oral LD50 values in rats, compiled from NIH CATMoS, EPA TEST and NTP by "
             "the AI4PFAS project (MIT licence). Stored as −log(LD50 in mol/kg): higher means more toxic.")
    st.markdown("GitHub: `AI4PFAS/AI4PFAS` · alternative on Kaggle: "
                "`iapetus509/therapeutics-data-commons-acute-toxicity-ld50`")

t_web, t_hub, t_cli, t_direct, t_script = st.tabs(
    ["Kaggle website", "kagglehub (Python)", "Kaggle command line", "Direct link", "Our script"])
with t_web:
    st.markdown("""
1. Make a free account at **kaggle.com**.
2. Search for **Tox21** and open the dataset page (for example *epicskills/tox21-dataset*).
3. Click **Download** (top right). You get a `.zip` file.
4. Unzip it and put the CSV file in `data/real/` inside the project, named `tox21.csv`.
""")
with t_hub:
    st.markdown("`kagglehub` is Kaggle's own Python library. Public datasets download without logging in.")
    st.code("""pip install kagglehub

import kagglehub
folder = kagglehub.dataset_download("epicskills/tox21-dataset")
print(folder)            # the folder where the files were saved

import pandas as pd
from pathlib import Path
csv_file = next(Path(folder).rglob("*.csv"))
tox21 = pd.read_csv(csv_file)
print(tox21.shape)""", language="python")
    st.markdown("If Kaggle asks you to log in: open **kaggle.com → Settings → API**, click "
                "**Generate New Token**, then run `kagglehub.login()` and paste the token.")
with t_cli:
    st.code("""pip install kaggle
kaggle auth login                                  # or set KAGGLE_API_TOKEN
kaggle datasets download -d epicskills/tox21-dataset --unzip -p data/real""", language="bash")
with t_direct:
    st.markdown("No account needed. Pandas can read a CSV straight from a web address:")
    st.code("""import pandas as pd
tox21 = pd.read_csv("https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz")
ld50 = pd.read_csv("https://raw.githubusercontent.com/AI4PFAS/AI4PFAS/main/data/ldtoxdb-raw.csv")""",
            language="python")
with t_script:
    st.markdown("`scripts/get_data.py` does everything: downloads Tox21 (Kaggle first, direct link if "
                "that fails), downloads the LD50 table, matches the compounds with RDKit and saves the two "
                "files this page reads.")
    st.code("""pip install -r requirements-data.txt      # rdkit + kagglehub
python scripts/get_data.py""", language="bash")

# ---------------------------------------------------------------- 2. how many are toxic
st.header("2 · How many compounds are toxic?", anchor=False)
st.write("Rule: a compound is **toxic** if it was active in **at least one** of the 12 Tox21 assays, "
         "and **non-toxic** if it was active in none of the assays it was tested in.")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Compounds in Tox21", f"{counts['total']:,}", border=True)
m2.metric("Toxic", f"{counts['toxic']:,}", f"{counts['toxic_pct']}% of all", delta_color="off",
          delta_arrow="off", border=True)
m3.metric("Non-toxic", f"{counts['non_toxic']:,}", f"{100 - counts['toxic_pct']:.1f}% of all",
          delta_color="off", delta_arrow="off", border=True)
m4.metric("Non-toxic in all 12 tests", f"{counts['non_toxic_fully_tested']:,}",
          help="Non-toxic compounds that were actually tested in every one of the 12 assays. The rest "
               "had at least one assay missing, so they are 'non-toxic as far as we know'.", border=True)
st.pyplot(assay_active_chart(rd.assay_table(tox)))
st.markdown("**Reading the chart.** Each assay catches a different kind of harm. The stress-response "
            "assays (SR-ARE for oxidative stress, SR-MMP for mitochondria) flag the most compounds; "
            "PPAR-gamma flags the fewest. The 12 percentages add up to more than 36.7% because many "
            "compounds are active in several assays.")
with st.expander("All 12 assays as a table"):
    st.dataframe(rd.assay_table(tox), hide_index=True)

# ---------------------------------------------------------------- 3. compare LD50
st.header("3 · Compare the average LD50", anchor=False)
st.write(f"Tox21 has no LD50, so we matched its compounds to the LD50 table by structure. "
         f"**{len(data):,} compounds** appear in both: {int(data['toxic'].sum()):,} toxic and "
         f"{int((data['toxic'] == 0).sum()):,} non-toxic in Tox21.")

unit = st.segmented_control("Show LD50 as", ["−log(mol/kg)", "mg/kg"], default="−log(mol/kg)",
                            required=True, key="ld50_unit")
column = "neglog_ld50" if unit == "−log(mol/kg)" else "ld50_mg_per_kg"
log_scale = column == "ld50_mg_per_kg"
axis_label = ("−log(LD50 in mol/kg)   (higher = more toxic)" if not log_scale
              else "LD50 in mg/kg, log scale   (lower = more toxic)")

stats = rd.group_stats(data, column)
fmt = "{:,.0f}" if log_scale else "{:.2f}"
s1, s2 = st.columns(2)
for col, row, color in zip((s1, s2), stats.to_dict("records"), ("primary", "blue")):
    with col.container(border=True):
        st.markdown(f"**:{color}[{row['Group']}]** · {row['Compounds']:,} compounds")
        a, b = st.columns(2)
        a.metric("Average (mean)", fmt.format(row["Mean"]))
        b.metric("Median", fmt.format(row["Median"]))

toxic_values, safe_values = rd.split(data, column)
tab_box, tab_hist, tab_table = st.tabs(["Box plot", "Histogram", "Table"])
with tab_box:
    st.pyplot(ld50_box_chart(toxic_values, safe_values, axis_label, log_x=log_scale,
                             more_toxic="left" if log_scale else "right"))
    st.caption("Each dot is one compound. The box holds the middle half of each group; the thick line is "
               "the median.")
with tab_hist:
    st.pyplot(ld50_histogram_chart(toxic_values, safe_values, axis_label, log_x=log_scale))
with tab_table:
    st.dataframe(stats.round(3 if not log_scale else 0), hide_index=True)
    if log_scale:
        st.caption("Means in mg/kg are pulled up by a few very large values; the median and the −log "
                   "scale describe the typical compound better.")

st.subheader("Is the difference real, or just chance?", anchor=False)
result = comparison("neglog_ld50")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Difference in −log(LD50)", f"{result['difference']:+.2f}", border=True)
r2.metric("Times more toxic", f"×{result['fold']:.1f}", border=True,
          help="10 to the power of the difference: the typical toxic compound kills at about half the dose.")
r3.metric("Cohen's d", f"{result['cohens_d']:.2f}", border=True,
          help="Difference in means divided by the spread. 0.2 small, 0.5 medium, 0.8 large.")
r4.metric("Permutation p-value", f"{result['p_value']:.4f}", border=True,
          help=f"We shuffled the toxic / non-toxic labels {result['n_permutations']:,} times with NumPy "
               "and counted how often chance produced a gap at least this large.")
st.success(rd.conclusion(result), icon=":material/fact_check:")
with st.expander("How the permutation test works (NumPy)"):
    st.markdown("If being toxic in Tox21 had nothing to do with LD50, the labels would be arbitrary. "
                "So we mix all 3,831 LD50 values together, deal them out again into a 'toxic' pile and "
                "a 'non-toxic' pile of the same sizes, and measure the gap. Repeating this 10,000 times "
                "shows how big a gap chance alone produces. The p-value is the share of shuffles whose "
                "gap is at least as big as the real one.")
    st.code("""pooled = np.concatenate([toxic, non_toxic])
for _ in range(10_000):
    rng.shuffle(pooled)
    diff = pooled[:len(toxic)].mean() - pooled[len(toxic):].mean()
    if abs(diff) >= abs(observed):
        count += 1
p_value = (count + 1) / (10_000 + 1)""", language="python")

# ---------------------------------------------------------------- 4. per assay
st.header("4 · Which assays point to lethal compounds?", anchor=False)
st.write("The same comparison, one assay at a time: how much lower is the LD50 of the compounds each "
         "assay flags?")
st.pyplot(assay_effect_chart(effects()))
st.markdown("**Aromatase, p53 and PPAR-gamma** actives are about 3 times more lethal than the compounds "
            "those assays clear. Assays for **DNA damage (p53, ATAD5)**, **oxidative stress (ARE)** and "
            "**mitochondria (MMP)** also separate the groups. The **estrogen and androgen receptor** "
            "assays show no clear link: hormone-like activity is a real hazard, but not one that kills a "
            "rat within days.")
with st.expander("Per-assay numbers"):
    st.dataframe(effects(), hide_index=True, column_config={
        "p-value": st.column_config.NumberColumn(format="%.4f")})

# ---------------------------------------------------------------- 5. discussion
st.header("5 · What it means", anchor=False)
g1, g2 = st.columns([1.1, 1], gap="large")
with g1:
    st.markdown("""
- **There is a visible difference.** Tox21-toxic compounds have a lower lethal dose: median about
  1,600 mg/kg against about 2,250 mg/kg, roughly **2 times more toxic** on the log scale.
- **But the groups overlap a lot.** Cohen's d is about 0.4. Plenty of "non-toxic" compounds are
  deadly, and plenty of "toxic" ones are mild.
- **Why?** Tox21 measures specific effects in cells in a dish. LD50 measures death of a whole animal,
  which also depends on absorption, metabolism and how the body clears the compound.
- **Limits.** Only 3,831 of 7,831 compounds had an LD50; some Tox21 compounds were not tested in every
  assay; and LD50 values come from different labs.
""")
with g2:
    st.caption("GHS ACUTE ORAL TOXICITY CATEGORY (by LD50)")
    ghs = rd.ghs_table(data)
    st.dataframe(ghs, width="stretch")
    deadly_clean = int(ghs["Non-toxic in Tox21"].iloc[:2].sum())
    st.caption(f"{deadly_clean} compounds that passed every Tox21 test they took still fall in GHS "
               "categories 1–2 (“fatal if swallowed”).")

# ---------------------------------------------------------------- 6. any dataset
st.header("6 · Try it on another dataset", anchor=False)
st.write("Upload any CSV with a yes/no toxicity column and a numeric measure (for example a Kaggle "
         "download). The same code counts the two groups and compares their averages.")
upload = st.file_uploader("CSV file", type=["csv"], key="lab_upload")
if upload is not None:
    frame = pd.read_csv(upload)
    st.caption(f"{len(frame):,} rows · {len(frame.columns)} columns")
    two_valued = [c for c in frame.columns if frame[c].dropna().nunique() == 2]
    numeric = [c for c in frame.columns if pd.api.types.is_numeric_dtype(frame[c]) and frame[c].nunique() > 2]
    if not two_valued or not numeric:
        st.warning("I need one column with exactly two values (toxic / non-toxic) and one numeric column.")
    else:
        u1, u2, u3 = st.columns(3)
        label_col = u1.selectbox("Toxic / non-toxic column", two_valued)
        values = sorted(frame[label_col].dropna().unique(), key=str)
        toxic_value = u2.selectbox("Which value means toxic?", values, index=len(values) - 1)
        measure = u3.selectbox("Measure to compare", numeric)
        work = frame[[label_col, measure]].dropna()
        work["toxic"] = (work[label_col] == toxic_value).astype(int)
        n_t, n_s = int(work["toxic"].sum()), int((work["toxic"] == 0).sum())
        k1, k2 = st.columns(2)
        k1.metric("Toxic", f"{n_t:,}", border=True)
        k2.metric("Non-toxic", f"{n_s:,}", border=True)
        if min(n_t, n_s) >= 3:
            res = rd.compare(work, measure, n_permutations=5_000)
            st.dataframe(rd.group_stats(work, measure, names=("Toxic", "Non-toxic")).round(3), hide_index=True)
            a, b = rd.split(work, measure)
            st.pyplot(ld50_box_chart(a, b, measure, more_toxic=None, names=("Toxic", "Non-toxic")))
            st.info(rd.conclusion(res, measure=measure), icon=":material/fact_check:")
        else:
            st.warning("Each group needs at least 3 rows to compare.")

# ---------------------------------------------------------------- sources
st.divider()
st.download_button("Download the matched table (.csv)", data.to_csv(index=False), file_name="tox21_ld50.csv",
                   mime="text/csv", icon=":material/download:")
st.caption("Sources: Tox21 Data Challenge (NIH NCATS, EPA, FDA), as distributed by MoleculeNet / DeepChem "
           "and on Kaggle. LDToxDB from Feinstein et al., J. Chem. Inf. Model. 2021 (AI4PFAS, MIT licence), "
           "compiled from NIH CATMoS, EPA TEST and NTP data. Compounds matched by the connectivity layer of "
           "the InChIKey with RDKit.")
