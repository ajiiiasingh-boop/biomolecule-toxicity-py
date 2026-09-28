"""
drawing.py — every picture in the project, drawn with Matplotlib.

    dose_chart()        the evidence charts (line or bar, with error bars)
    cell_diagram()      the cell, its organelles, and the route a toxicant takes
    target_bar_chart()  how many toxins in the library hit each biomolecule

Why `Figure()` and not `plt.subplots()`?
A website serves many people at the same time. pyplot keeps one shared
"current figure" for the whole program, so two visitors could draw on the same
picture. Creating a Figure object directly gives every chart its own canvas.
The drawing commands (ax.plot, ax.bar, ax.set_title ...) are exactly the ones
you already know from pyplot.
"""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, RegularPolygon, Wedge

from btd.analysis import dataset_frame, simulate_replicates
from btd.data import BIOMOLECULES, CELL_PART_BY_ID

# The same warm-pink palette as the website.
COLORS = {
    "ground": "#fff5f3",
    "surface": "#fffaf9",
    "ink": "#3d2130",
    "ink2": "#7a5866",
    "faint": "#d9bfc8",
    "edge": "#f0d3dc",
    "key": "#d6336c",
    "cyto": "#fff0f2",
}
# One colour per biomolecule class ("channel"), checked for colour-blind safety.
CHANNEL = {
    "dna-rna": "#2566bd",
    "protein": "#0e8f7f",
    "lipid": "#cf3b4a",
    "carbohydrate": "#b8860b",
}


def style_axes(ax):
    """The house style: no box, a light grid, soft ink colours."""
    ax.set_facecolor(COLORS["surface"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(COLORS["faint"])
    ax.tick_params(colors=COLORS["ink2"], labelsize=8.5)
    ax.yaxis.grid(True, color=COLORS["edge"], linewidth=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(COLORS["ink2"])
    ax.yaxis.label.set_color(COLORS["ink2"])


def spread_labels(values, min_gap):
    """Nudge end-of-line labels apart so they never print on top of each other.

    A tiny algorithm: sort the label heights, then walk upwards and push any
    label that is closer than min_gap to the one below it.
    """
    order = np.argsort(values)
    placed = np.array(values, dtype=float)
    for previous, current in zip(order[:-1], order[1:]):
        if placed[current] - placed[previous] < min_gap:
            placed[current] = placed[previous] + min_gap
    return placed


# ---------------------------------------------------------------------------
# Evidence charts
# ---------------------------------------------------------------------------
def dose_chart(dataset, show_replicates=True):
    """Draw one case dataset. Values are the case data; error bars (optional)
    are the SD of three simulated replicates from analysis.simulate_replicates."""
    frame = dataset_frame(dataset)
    levels = list(frame.index)
    x = np.arange(len(levels))
    series = dataset["series"]
    replicates = simulate_replicates(dataset) if show_replicates else None

    fig = Figure(figsize=(7.4, 4.0), dpi=160, facecolor=COLORS["surface"])
    ax = fig.subplots()
    style_axes(ax)

    if dataset["type"] == "bar":
        width = 0.6 / len(series)
        for j, s in enumerate(series):
            values = frame[s["key"]].to_numpy(dtype=float)
            positions = x + (j - (len(series) - 1) / 2) * width
            bars = ax.bar(positions, values, width=width * 0.9, color=CHANNEL[s["channel"]],
                          alpha=0.88, label=s["key"], zorder=2)
            if replicates is not None:
                sd = replicates[:, j].std(axis=1, ddof=1)
                ax.errorbar(positions, values, yerr=sd, fmt="none", ecolor=COLORS["ink"],
                            elinewidth=1, capsize=4, zorder=3)
            ax.bar_label(bars, labels=[f"{v:g}" for v in values], padding=4,
                         fontsize=8.5, color=COLORS["ink"], fontweight="bold")
        # Bars always start at zero, so their heights can be compared honestly.
        ax.set_ylim(0, dataset["yMax"] * 1.08)
        ax.set_xlim(-0.6, len(levels) - 0.4)
    else:
        ends = []
        for j, s in enumerate(series):
            color = CHANNEL[s["channel"]]
            values = frame[s["key"]].to_numpy(dtype=float)
            if replicates is not None:
                sd = replicates[:, j].std(axis=1, ddof=1)
                ax.errorbar(x, values, yerr=sd, fmt="none", ecolor=color, elinewidth=1,
                            capsize=3, alpha=0.75, zorder=2)
            ax.plot(x, values, marker="o", markersize=6.5, linewidth=2.3, color=color,
                    markeredgecolor="white", markeredgewidth=1.3, label=s["key"], zorder=3)
            ends.append((values[-1], color))
        if "%" in dataset["yLabel"]:
            # Dashed reference line at the control level (explained in the x-axis label).
            ax.axhline(100, color=COLORS["faint"], linewidth=1, linestyle="--", zorder=1)
        # Direct labels at the end of each line, spread apart if they collide.
        heights = spread_labels([v for v, _ in ends], min_gap=dataset["yMax"] * 0.055)
        for (value, color), height in zip(ends, heights):
            ax.annotate(f"{value:g}", (x[-1], value), xytext=(x[-1] + 0.12, height),
                        textcoords="data", va="center", fontsize=8.5, color=color,
                        fontweight="bold")
        ax.set_ylim(0, dataset["yMax"])
        ax.set_xlim(-0.25, len(levels) - 1 + 0.45)

    ax.set_xticks(x, levels)
    x_label = dataset["xLabel"]
    if dataset["type"] != "bar" and "%" in dataset["yLabel"]:
        x_label += "      (dashed line = control level, 100%)"
    ax.set_xlabel(x_label, fontsize=9)
    ax.set_ylabel(dataset["yLabel"], fontsize=9)
    ax.set_title(dataset["title"], loc="left", fontsize=10.5, fontweight="bold",
                 color=COLORS["ink"], pad=26 if len(series) > 1 else 10)
    if len(series) > 1:
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=len(series),
                  frameon=False, fontsize=8, handlelength=1.6, columnspacing=1.2,
                  labelcolor=COLORS["ink"])
    fig.text(0.995, 0.01, "SIMULATED EDUCATIONAL DATA", ha="right", va="bottom",
             fontsize=7, color=COLORS["key"], fontweight="bold")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Cell diagram
# ---------------------------------------------------------------------------
# Where each part is drawn (x, y in a 0-100 box, y counted from the top, the
# same convention as data/cell_map.json) and where its label sits.
ANCHOR = {
    "membrane": (50, 10.5), "mitochondria": (33, 33), "cytoplasm": (22, 66),
    "enzymes": (44, 80), "nucleus": (62, 27.5), "dna": (64, 44), "er": (78, 68),
}
LABEL_AT = {
    "membrane": (50, 0.5), "mitochondria": (-11, 22), "cytoplasm": (-11, 62),
    "enzymes": (-4, 100), "nucleus": (109, 14), "dna": (109, 40), "er": (109, 80),
}


def _ellipse_points(cx, cy, width, height, count):
    """Points evenly spaced around an ellipse (NumPy does all of them at once)."""
    t = np.linspace(0, 2 * np.pi, count, endpoint=False)
    return cx + width / 2 * np.cos(t), cy + height / 2 * np.sin(t)


def cell_diagram(route=None, selected=None):
    """Draw the cell. `route` is a list of part ids to trace with numbered
    arrows; `selected` is one part id to outline in the key colour."""
    route = route or []
    fig = Figure(figsize=(7.6, 5.4), dpi=160, facecolor=COLORS["surface"])
    ax = fig.subplots()
    ax.set_xlim(-27, 127)
    ax.set_ylim(106, -6)            # y grows downwards, like the website's diagram
    ax.axis("off")

    def alpha_for(part_id):
        """Parts on the traced route stay bright; everything else fades."""
        return 1.0 if not route or part_id in route else 0.28

    lipid, dna, protein, carb = (CHANNEL[k] for k in ("lipid", "dna-rna", "protein", "carbohydrate"))

    # Plasma membrane: a bilayer drawn as two outlines with phospholipid heads.
    a = alpha_for("membrane")
    ax.add_patch(Ellipse((50, 52), 92, 86, facecolor=COLORS["cyto"], edgecolor=lipid,
                         linewidth=2.2, alpha=max(a, 0.6), zorder=1))
    ax.add_patch(Ellipse((50, 52), 87, 81, facecolor="none", edgecolor=lipid,
                         linewidth=1.2, alpha=a, zorder=1))
    hx, hy = _ellipse_points(50, 52, 89.5, 83.5, 120)
    ax.scatter(hx, hy, s=7, color=lipid, alpha=a, zorder=2, linewidths=0)

    # Cytoplasm: glucose rings floating in the cytosol.
    a = alpha_for("cytoplasm")
    for gx, gy in [(16, 60), (24, 72), (14, 76), (30, 60), (22, 84), (58, 88), (86, 56)]:
        ax.add_patch(RegularPolygon((gx, gy), numVertices=6, radius=1.9, facecolor="none",
                                    edgecolor=carb, linewidth=1.2, alpha=a, zorder=2))

    # Mitochondria: two capsules with folded cristae inside.
    a = alpha_for("mitochondria")
    for (mx, my, w, h, angle) in [(33, 33, 20, 9, 18), (20, 48, 14, 6.5, -30)]:
        ax.add_patch(Ellipse((mx, my), w, h, angle=angle, facecolor="#fdf1d6", edgecolor=carb,
                             linewidth=1.6, alpha=a, zorder=3))
        t = np.linspace(-w / 2 + 2, w / 2 - 2, 60)
        wave = (h / 2 - 1.3) * np.sin(t * 1.4)
        rad = np.deg2rad(angle)
        ax.plot(mx + t * np.cos(rad) - wave * np.sin(rad), my + t * np.sin(rad) + wave * np.cos(rad),
                color=carb, linewidth=0.9, alpha=a, zorder=4)

    # Nucleus with nucleolus and chromatin (DNA drawn as sine-wave threads).
    a = alpha_for("nucleus")
    ax.add_patch(Ellipse((63, 45), 32, 34, facecolor="#e8f0fb", edgecolor=dna,
                         linewidth=2, alpha=a, zorder=3))
    ax.add_patch(Circle((70, 38), 3.6, facecolor=dna, alpha=0.55 * a, zorder=4))
    a = alpha_for("dna")
    t = np.linspace(0, 1, 120)
    for k, y0 in enumerate([41, 46, 51, 55]):
        xs = 52 + 20 * t
        ys = y0 + 1.6 * np.sin(2 * np.pi * (3 + k) * t)
        ax.plot(xs, ys, color=dna, linewidth=1.1, alpha=a, zorder=5)

    # Endoplasmic reticulum: stacked curved membranes beside the nucleus.
    a = alpha_for("er")
    t = np.linspace(-1, 1, 80)
    for k in range(4):
        ax.plot(72 + 14 * t, 64 + k * 3.4 + 2.2 * t ** 2, color=protein, linewidth=1.6,
                alpha=a, zorder=3)

    # Cytosolic enzymes: little Pac-Man shapes (a pocket = the active site).
    a = alpha_for("enzymes")
    for ex, ey, turn in [(40, 79, 0), (47, 82, 40), (44, 75, 200), (52, 77, 120), (36, 84, 300)]:
        ax.add_patch(Wedge((ex, ey), 2.2, 30 + turn, 330 + turn, facecolor=protein,
                           edgecolor="white", linewidth=0.6, alpha=a, zorder=4))

    # Labels with leader lines, coloured by biomolecule class.
    for part_id, (lx, ly) in LABEL_AT.items():
        part = CELL_PART_BY_ID[part_id]
        color = CHANNEL[part["biomolecule"]]
        is_selected = part_id == selected
        ax.annotate(
            part["name"], xy=ANCHOR[part_id], xytext=(lx, ly), ha="center", va="center",
            fontsize=10.5, fontweight="bold" if is_selected or part_id in route else "normal",
            color=COLORS["ink"], alpha=alpha_for(part_id) ** 0.5, zorder=8,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor=COLORS["key"] if is_selected else color,
                      linewidth=2.2 if is_selected else 1),
            arrowprops=dict(arrowstyle="-", color=color, linewidth=0.9,
                            alpha=alpha_for(part_id), shrinkA=0, shrinkB=2),
        )

    # The traced route: numbered stops joined by curved arrows.
    for step, part_id in enumerate(route, start=1):
        px, py = ANCHOR[part_id]
        if step < len(route):
            nx, ny = ANCHOR[route[step]]
            ax.add_patch(FancyArrowPatch((px, py), (nx, ny), connectionstyle="arc3,rad=0.25",
                                         arrowstyle="-|>", mutation_scale=14, linewidth=2,
                                         color=COLORS["key"], shrinkA=9, shrinkB=9, zorder=9))
        ax.add_patch(Circle((px, py), 3.2, facecolor=COLORS["key"], edgecolor="white",
                            linewidth=1.5, zorder=10))
        ax.text(px, py, str(step), ha="center", va="center", fontsize=9.5, color="white",
                fontweight="bold", zorder=11)

    fig.tight_layout(pad=0.3)
    return fig


# ---------------------------------------------------------------------------
# Toxin library chart
# ---------------------------------------------------------------------------
def target_bar_chart(counts):
    """Horizontal bars: number of library entries per target biomolecule."""
    labels = list(counts.index)
    values = counts.to_numpy()
    colors = [CHANNEL[b["id"]] for b in BIOMOLECULES if b["label"] in labels]

    fig = Figure(figsize=(6.4, 2.6), dpi=160, facecolor=COLORS["surface"])
    ax = fig.subplots()
    style_axes(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=COLORS["edge"], linewidth=0.8)
    positions = np.arange(len(labels))[::-1]           # first label at the top
    bars = ax.barh(positions, values, color=colors, height=0.62, zorder=2)
    ax.bar_label(bars, padding=4, fontsize=9, color=COLORS["ink"], fontweight="bold")
    ax.set_yticks(positions, labels)
    ax.set_xlim(0, max(values.max(), 1) * 1.18)
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.set_xlabel("Number of toxins in the current view", fontsize=8.5)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Flowcharts as Graphviz text (Streamlit's st.graphviz_chart draws them)
# ---------------------------------------------------------------------------
def _quote(text):
    """Make a piece of text safe to put inside a Graphviz label."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def pathway_dot(steps, color):
    """Build the causal pathway (exposure -> ... -> effect) as Graphviz text.

    This is plain string-building with a loop: one line per box, one line per
    arrow. Streamlit turns the text into a diagram.
    """
    lines = [
        "digraph pathway {",
        '  bgcolor="transparent"; rankdir=TB; nodesep=0.25; ranksep=0.28;',
        f'  node [shape=box, style="rounded,filled", fillcolor="#fffaf9", color="{color}", '
        'penwidth=1.6, fontname="Helvetica", fontsize=13, fontcolor="#3d2130", width=3.2, '
        'margin="0.16,0.08"];',
        '  edge [color="#d6336c", penwidth=1.4, arrowsize=0.7];',
    ]
    for number, step in enumerate(steps, start=1):
        lines.append(f'  s{number} [label="{number}. {_quote(step)}"];')
    for number in range(1, len(steps)):
        lines.append(f"  s{number} -> s{number + 1};")
    lines.append("}")
    return "\n".join(lines)


def investigation_flowchart_dot():
    """The investigation algorithm as a flowchart (used on the Python Lab page)."""
    return """
digraph investigation {
  bgcolor="transparent"; rankdir=TB; nodesep=0.35; ranksep=0.32;
  node [fontname="Helvetica", fontsize=11, fontcolor="#3d2130", penwidth=1.4, color="#d6336c",
        style="rounded,filled", fillcolor="#fffaf9", shape=box, margin="0.16,0.08"];
  edge [color="#8e6a79", fontname="Helvetica", fontsize=10, fontcolor="#7a5866", arrowsize=0.7];

  start   [label="Start: open a case", shape=oval, fillcolor="#ffe8ec"];
  open    [label="Open an evidence card"];
  all4    [label="All 4 cards opened?", shape=diamond, style=filled, fillcolor="#fff5f3"];
  answer  [label="Choose biomolecule (Q1)\\nand mechanism (Q2)"];
  hint    [label="Optional hint\\n(-10 points each)", color="#b8860b", fontcolor="#7f5d06"];
  grade   [label="grade_case() compares\\nanswers with the key"];
  both    [label="Both correct?", shape=diamond, style=filled, fillcolor="#fff5f3"];
  solved  [label="CASE SOLVED\\nexplanation + pathway\\npoints banked", fillcolor="#e3f4ef", color="#0e8f7f"];
  fb      [label="Targeted feedback\\npoints to the evidence", color="#c2410c"];
  next    [label="Next case", shape=oval, fillcolor="#ffe8ec"];

  start -> open -> all4;
  all4 -> open  [label=" no"];
  all4 -> answer [label=" yes"];
  answer -> hint [style=dashed, arrowhead=none];
  answer -> grade -> both;
  both -> solved [label=" yes"];
  both -> fb [label=" no"];
  fb -> answer [label=" try again", constraint=false];
  solved -> next;
}
"""


# ---------------------------------------------------------------------------
# Real-data charts (Data Lab page): Tox21 groups compared on LD50
# ---------------------------------------------------------------------------
GROUP_COLORS = {"toxic": "#d6336c", "non_toxic": "#2566bd"}   # checked for colour-blind safety


def ld50_box_chart(toxic, non_toxic, x_label, log_x=False, more_toxic="right",
                   names=("Toxic in Tox21", "Non-toxic in Tox21")):
    """Two horizontal box plots with every compound shown as a faint dot.

    The box is the middle half of the compounds, the line inside is the median,
    and the dots show how much the two groups overlap.
    """
    fig = Figure(figsize=(7.6, 3.4), dpi=160, facecolor=COLORS["surface"])
    ax = fig.subplots()
    style_axes(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=COLORS["edge"], linewidth=0.8)
    groups = [(names[1], non_toxic, GROUP_COLORS["non_toxic"], 0),
              (names[0], toxic, GROUP_COLORS["toxic"], 1)]
    if log_x:
        ax.set_xscale("log")
    rng = np.random.default_rng(7)
    for name, values, color, y in groups:
        jitter = y + rng.uniform(-0.28, 0.28, size=len(values))
        ax.scatter(values, jitter, s=5, color=color, alpha=0.18, linewidths=0, zorder=2)
        ax.boxplot(values, positions=[y], orientation="horizontal", widths=0.5, showfliers=False,
                         patch_artist=True, zorder=3,
                         medianprops=dict(color=COLORS["ink"], linewidth=2),
                         boxprops=dict(facecolor="none", edgecolor=color, linewidth=1.8),
                         whiskerprops=dict(color=color, linewidth=1.4),
                         capprops=dict(color=color, linewidth=1.4))
        median = float(np.median(values))
        ax.annotate(f"median {median:,.0f}" if log_x else f"median {median:.2f}", (median, y + 0.3),
                    ha="center", va="bottom",
                    fontsize=8.5, color=COLORS["ink"], fontweight="bold")
    ax.set_yticks([0, 1], [f"{g[0]}\n(n = {len(g[1]):,})" for g in groups])
    ax.set_ylim(-0.6, 1.75)
    ax.set_xlabel(x_label, fontsize=9)
    if more_toxic:
        ax.annotate("more toxic →" if more_toxic == "right" else "← more toxic",
                    xy=(1 if more_toxic == "right" else 0, -0.2), xycoords="axes fraction",
                    ha="right" if more_toxic == "right" else "left", va="top", fontsize=8,
                    color=COLORS["ink2"])
    fig.tight_layout()
    return fig


def ld50_histogram_chart(toxic, non_toxic, x_label, bins=40, log_x=False,
                         names=("Toxic in Tox21", "Non-toxic in Tox21")):
    """The shape of both distributions, as outlines on one axis (share of each group)."""
    fig = Figure(figsize=(7.6, 3.4), dpi=160, facecolor=COLORS["surface"])
    ax = fig.subplots()
    style_axes(ax)
    both = np.concatenate([toxic, non_toxic])
    if log_x:
        ax.set_xscale("log")
        edges = np.logspace(np.log10(both[both > 0].min()), np.log10(both.max()), bins + 1)
    else:
        edges = np.histogram_bin_edges(both, bins=bins)
    for name, values, color in ((names[1], non_toxic, GROUP_COLORS["non_toxic"]),
                                (names[0], toxic, GROUP_COLORS["toxic"])):
        weights = np.full(len(values), 100 / len(values))       # each group sums to 100%
        ax.hist(values, bins=edges, weights=weights, histtype="step", linewidth=2, color=color, label=name)
        ax.axvline(np.median(values), color=color, linewidth=1.2, linestyle="--")
    ax.set_xlabel(x_label, fontsize=9)
    ax.set_ylabel("% of the group", fontsize=9)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right", labelcolor=COLORS["ink"])
    ax.annotate("dashed lines = medians", xy=(0, 1.02), xycoords="axes fraction", fontsize=8,
                color=COLORS["ink2"])
    fig.tight_layout()
    return fig


def assay_effect_chart(effects):
    """How much more toxic (in LD50) the actives of each assay are than its inactives."""
    frame = effects.iloc[::-1]                                    # biggest at the top
    fig = Figure(figsize=(7.6, 4.4), dpi=160, facecolor=COLORS["surface"])
    ax = fig.subplots()
    style_axes(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=COLORS["edge"], linewidth=0.8)
    significant = frame["p-value"] < 0.05
    colors = [GROUP_COLORS["toxic"] if s else COLORS["faint"] for s in significant]
    positions = np.arange(len(frame))
    ax.barh(positions, frame["Difference"], color=colors, height=0.62, zorder=2)
    for y, (diff, fold, sig) in enumerate(zip(frame["Difference"], frame["Times more toxic"], significant)):
        label = f"×{fold:.1f}" if sig else f"×{fold:.1f}  n.s."
        ax.annotate(label, (max(diff, 0), y), xytext=(4, 0), textcoords="offset points", va="center",
                    fontsize=8.5, color=COLORS["ink"], fontweight="bold" if sig else "normal")
    ax.set_yticks(positions, frame["Assay"])
    ax.axvline(0, color=COLORS["ink2"], linewidth=0.8)
    ax.set_xlim(min(0, frame["Difference"].min()) - 0.02, frame["Difference"].max() * 1.25)
    ax.set_xlabel("Actives minus inactives, in −log(LD50)  (×N = times more toxic)", fontsize=9)
    fig.text(0.995, 0.01, "grey = not significant (p ≥ 0.05)", ha="right", va="bottom", fontsize=7,
             color=COLORS["ink2"])
    fig.tight_layout()
    return fig


def assay_active_chart(table):
    """Share of tested compounds that were active in each assay."""
    frame = table.sort_values("% active")
    fig = Figure(figsize=(7.6, 4.0), dpi=160, facecolor=COLORS["surface"])
    ax = fig.subplots()
    style_axes(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=COLORS["edge"], linewidth=0.8)
    positions = np.arange(len(frame))
    bars = ax.barh(positions, frame["% active"], color=GROUP_COLORS["toxic"], height=0.62, zorder=2)
    ax.bar_label(bars, labels=[f"{v:.1f}%" for v in frame["% active"]], padding=4, fontsize=8.5,
                 color=COLORS["ink"])
    ax.set_yticks(positions, frame["Assay"])
    ax.set_xlim(0, frame["% active"].max() * 1.2)
    ax.set_xlabel("% of tested compounds that were active (toxic)", fontsize=9)
    fig.tight_layout()
    return fig
