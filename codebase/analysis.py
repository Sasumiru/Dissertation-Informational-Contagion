import datetime
import os
import subprocess
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg") #no window, just save the png
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy import stats
import multiround as mr #imports
sys.stdout.reconfigure(encoding="utf-8")


TOP_N = 10 #size of the top and bottom tables, ties at the edge are all kept
TOL = 0.05 #change in a headline correlation that counts as stronger or weaker
ALPHA = 0.05 #significance level used in the text
CONTROLS = ["log_total_assets", "cet1_ratio", "direct_reach"] #rq3 partial correlation controls
PINGOUIN_TOL = 1e-8 #how close our partial correlation has to be to pingouin's
CENT_TOL = 1e-10 #recomputed vs saved centrality

# reference results from earlier runs, logistic mapping, full sample
REF_FULL = {"delta": 1.0, "laterRounds": "full", "pctAll": 77.0, "pctNone": 21.0}
REF_MAIN = {"pctNone": 21.0, "meanTotal": 60.0}
REF_TOL_PCT = 2.0 #percentage points either side of the reference
REF_TOL_MEAN = 1.0 #banks either side of the reference mean

RQ1_FILE = "output/rq1_summary.csv"
RQ2_FILE = "output/rq2_comparisons.csv"
RQ3_FILE = "output/rq3_correlations.csv"
REPORT_FILE = "output/results_report.md"
DETERMINISM_FILE = "output/determinism_check.txt"
FIG_DIR = "output/figures"
DPI = 300

# figure colours (validated categorical slots 1 and 2) and ink
BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e6e5e1"
SHADE = "#efeeeb" #background band behind banks that are never hit
NOTE_INK = "#52514e" #annotation text
FIG_WIDTH = 6.5 #inches, fits the page width so text prints at its real size

# one style for every figure
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.labelcolor": INK,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

CENT_LABELS = {
    "weighted_degree": "Weighted degree",
    "eigenvector": "Eigenvector",
    "pagerank": "PageRank",
    "betweenness": "Betweenness",
}
MEASURE_LABELS = {
    "direct_reach": "Direct reach",
    "indirect_reach": "Indirect reach",
    "total_reach": "Total reach",
    "exposure": "Exposure",
}
COMPARE_LABELS = {
    "linear": "Linear mapping",
    "convex": "Convex mapping",
    "single": "Single-round model",
    "main_spec": "Main spec",
}
RUN_LABELS = {
    "main": "Main spec",
    "no_public_banks": "Without the four public-sector banks",
    "strong_link_70": "Strong-link cut-off at the 70th percentile",
    "strong_link_80": "Strong-link cut-off at the 80th percentile",
    "complete_centrality": "Centrality on the complete network (RQ3 only)",
    "delta_1.0": "No decay (delta = 1.0)",
    "delta_0.3": "Decay delta = 0.3",
    "delta_0.7": "Decay delta = 0.7",
    "tau_95": "Distress threshold at the 95th percentile",
    "later_rounds_full": "Later rounds along the full network",
}


# ---------- loading ----------

def loadTables(params):
    tables = {}
    for _, row in params.iterrows():
        key = (row["run"], row["variant"])
        tables[key] = pd.read_csv(mr.outputPath(*key)).set_index("LEI_Code")
    return tables

def allRuns():
    return ["main"] + list(mr.ROBUSTNESS)


# ---------- formatting ----------

def fmtR(x):
    return "n/a" if pd.isna(x) else f"{x:.2f}"

def fmtP(p):
    if pd.isna(p):
        return "n/a"
    return "<0.001" if p < 0.0005 else f"{p:.3f}" #3 dp, anything that rounds to 0.000 shown as <0.001

def fmtNum(x, dp=2):
    return f"{x:.{dp}f}"

def mdTable(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


# ---------- statistics ----------

def spearman(a, b):
    common = a.index.intersection(b.index)
    a, b = a[common], b[common]
    if a.nunique() < 2 or b.nunique() < 2: #constant series has no rank correlation
        return np.nan, np.nan
    res = stats.spearmanr(a, b)
    return float(res[0]), float(res[1])

def topSet(series, n=TOP_N, largest=True):
    if largest:
        edge = series.nlargest(n).iloc[-1]
        return set(series[series >= edge].index) #keeps every bank tied with the 10th
    edge = series.nsmallest(n).iloc[-1]
    return set(series[series <= edge].index)

def topOverlap(ref, other):
    common = ref.index.intersection(other.index) #only banks in both samples
    refTop = topSet(ref[common])
    otherTop = topSet(other[common])
    return len(refTop & otherTop), len(refTop), len(otherTop)

def partialSpearman(data, x, y, controls):
    ranks = data[[x, y] + controls].rank(method="average") #rank everything first
    n = len(ranks)
    Z = np.column_stack([np.ones(n), ranks[controls].values]) #intercept + control ranks

    def residuals(col):
        beta = np.linalg.lstsq(Z, ranks[col].values, rcond=None)[0] #ols
        return ranks[col].values - Z @ beta

    resX = residuals(x)
    resY = residuals(y)
    if np.std(resX) == 0 or np.std(resY) == 0:
        return np.nan, np.nan, n
    r = float(np.corrcoef(resX, resY)[0, 1])
    df = n - 2 - len(controls)
    t = r * np.sqrt(df / (1 - r ** 2))
    p = float(2 * stats.t.sf(abs(t), df)) #two sided
    return r, p, n

def pingouinCheck(data, x, y, controls, r):
    try:
        import pingouin as pg
    except ImportError:
        return "not available (pingouin not installed)"
    if pd.isna(r):
        return "n/a"
    res = pg.partial_corr(data=data, x=x, y=y, covar=controls, method="spearman")
    pgR = float(res["r"].iloc[0])
    verdict = "match" if abs(pgR - r) < PINGOUIN_TOL else "MISMATCH"
    return f"{verdict} (pingouin r = {pgR:.4f})"

def classify(mainVal, runVal):
    if pd.isna(mainVal) or pd.isna(runVal):
        return "n/a"
    if np.sign(mainVal) != np.sign(runVal) and abs(mainVal) >= TOL and abs(runVal) >= TOL:
        return "reversed"
    change = abs(runVal) - abs(mainVal)
    if change >= TOL:
        return "stronger"
    if change <= -TOL:
        return "weaker"
    return "unchanged"


# ---------- research questions ----------

def rankedTable(table, col, largest=True):
    keep = topSet(table[col], largest=largest)
    out = table.loc[sorted(keep)].copy()
    out["rank"] = table[col].rank(ascending=False, method="average")[out.index] #1 = highest
    return out.sort_values([col, "Name"], ascending=[not largest, True])

def rq1(table):
    rho, p = spearman(table["total_reach"], table["exposure"])
    return {
        "n_banks": len(table),
        "mean_total_reach": table["total_reach"].mean(),
        "zero_total_reach": int((table["total_reach"] == 0).sum()),
        "zero_indirect_reach": int((table["indirect_reach"] == 0).sum()),
        "rho_reach_exposure": rho,
        "p_reach_exposure": p,
    }

def compareRow(run, comparison, measure, ref, other):
    rho, p = spearman(ref, other)
    overlap, refSize, otherSize = topOverlap(ref, other)
    return {
        "run": run,
        "comparison": comparison,
        "measure": measure,
        "spearman_rho": rho,
        "p_value": p,
        "top10_overlap": overlap,
        "reference_top10_size": refSize,
        "other_top10_size": otherSize,
        "n_banks": len(ref.index.intersection(other.index)),
    }

def rq2(run, tables):
    base = tables[(run, "base")]
    rows = []
    for variant in ["linear", "convex"]: #mapping comparisons split by round so its clear where differences come from
        other = tables[(run, variant)]
        for measure in ["direct_reach", "indirect_reach", "total_reach", "exposure"]:
            rows.append(compareRow(run, variant, measure, base[measure], other[measure]))
    single = tables[(run, "single")]
    for measure in ["total_reach", "exposure"]: #single round has no indirect reach
        rows.append(compareRow(run, "single", measure, base[measure], single[measure]))
    if run != "main":
        mainTable = tables[("main", "base")]
        for measure in ["total_reach", "exposure"]:
            rows.append(compareRow(run, "main_spec", measure, mainTable[measure], base[measure]))
    return rows

def rq3(run, table):
    network = "complete" if run == "complete_centrality" else "strong"
    rows = []
    for cent in mr.CENTRALITIES:
        rho, p = spearman(table[cent], table["indirect_reach"])
        pr, pp, n = partialSpearman(table, cent, "indirect_reach", CONTROLS)
        rows.append({
            "run": run,
            "network": network,
            "centrality": cent,
            "n_banks": n,
            "spearman_rho": rho,
            "p_value": p,
            "partial_rho": pr,
            "partial_p_value": pp,
            "pingouin_check": pingouinCheck(table, cent, "indirect_reach", CONTROLS, pr),
        })
    return rows

def describe(table):
    rows = []
    for col in ["total_reach", "direct_reach", "indirect_reach", "exposure", "rounds"]:
        s = table[col]
        rows.append({
            "measure": col,
            "mean": s.mean(),
            "median": s.median(),
            "min": s.min(),
            "max": s.max(),
            "std": s.std(), #sample sd, ddof = 1
            "zeros": int((s == 0).sum()),
        })
    return pd.DataFrame(rows)

def rq2Headline(rq2Df, run):
    sub = rq2Df[(rq2Df["run"] == run) & (rq2Df["measure"] == "total_reach") &
                (rq2Df["comparison"].isin(["linear", "convex", "single"]))]
    return sub["spearman_rho"].min() if len(sub) else np.nan #weakest agreement across the three


# ---------- validation ----------

def csvText(df, index):
    return df.to_csv(index=index).replace("\r\n", "\n")

def fileText(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")

def pctOf(mask):
    return 100 * mask.mean()

def validationChecks(tables, params):
    checks = []
    sim, meta, metrics = mr.loadInputs()

    # 1 symmetric matrix, zero diagonal, every sample used
    asym = params["max_abs_asymmetry"].max()
    diag = params["max_abs_diagonal"].max()
    checks.append(("1. Similarity matrix symmetric, diagonal 0",
                   asym == 0 and diag == 0,
                   f"max abs(S - S transposed) = {asym:.1e}, max abs(diagonal) = {diag:.1e} "
                   f"(all {len(params)} runs)"))

    # 2 direct + indirect = total
    bad = sum(int((t["direct_reach"] + t["indirect_reach"] != t["total_reach"]).sum()) for t in tables.values())
    checks.append(("2. direct + indirect = total for every trigger", bad == 0,
                   f"{bad} mismatches across {len(tables)} runs x every trigger"))

    # 3 sum exposure = sum total reach
    badRuns = [k for k, t in tables.items() if t["exposure"].sum() != t["total_reach"].sum()]
    mainT = tables[("main", "base")]
    checks.append(("3. Sum of exposure = sum of total_reach", not badRuns,
                   f"main: {mainT['exposure'].sum()} = {mainT['total_reach'].sum()}; "
                   f"{len(badRuns)} of {len(tables)} runs differ"))

    # rerun everything in memory for checks 4 and 5
    mem = mr.runEverything(sim, meta, metrics)

    # 4 trigger never distressed
    diagHits = sum(int(np.diag(roundMat).astype(bool).sum()) for _, roundMat, _ in mem.values())
    savedRounds = pd.read_csv(mr.ROUNDS_FILE, index_col=0).values
    diagHits += int(np.diag(savedRounds).astype(bool).sum())
    checks.append(("4. No trigger counts itself as distressed", diagHits == 0,
                   f"{diagHits} self-distress cases across {len(mem)} runs x {len(sim)} triggers"))

    # 5 deterministic, in memory rerun identical to the saved csvs
    diffs = []
    for key, (table, roundMat, _) in mem.items():
        if csvText(table, False) != fileText(mr.outputPath(*key)):
            diffs.append(key)
    mainRounds = pd.DataFrame(mem[("main", "base")][1], index=sim.index, columns=sim.index)
    if csvText(mainRounds, True) != fileText(mr.ROUNDS_FILE):
        diffs.append("cascade_rounds_main")
    if csvText(mr.paramTable(mem), False) != fileText(mr.PARAMS_FILE):
        diffs.append("run_parameters")
    checks.append(("5a. Deterministic: in-memory rerun identical to saved CSVs", not diffs,
                   f"{len(mem) + 2} files compared character for character, {len(diffs)} differ"))
    checks.append(("5b. Deterministic: both scripts rerun from scratch, outputs byte-identical",
                   None, f"done outside the scripts, hashes in {DETERMINISM_FILE}"))

    # 6 reference results
    refT, _, _ = mr.runSpec(sim, meta, metrics, delta=REF_FULL["delta"], laterRounds=REF_FULL["laterRounds"])
    allPct = pctOf(refT["total_reach"] == len(refT) - 1)
    nonePct = pctOf(refT["total_reach"] == 0)
    okFull = abs(allPct - REF_FULL["pctAll"]) <= REF_TOL_PCT and abs(nonePct - REF_FULL["pctNone"]) <= REF_TOL_PCT
    checks.append(("6a. Reference: delta=1.0, tau=90th, later rounds on full network", okFull,
                   f"{allPct:.1f}% distress all {len(refT) - 1} (ref ~{REF_FULL['pctAll']:.0f}%), "
                   f"{nonePct:.1f}% distress none (ref ~{REF_FULL['pctNone']:.0f}%)"))
    mainNone = pctOf(mainT["total_reach"] == 0)
    mainMean = mainT["total_reach"].mean()
    okMain = abs(mainNone - REF_MAIN["pctNone"]) <= REF_TOL_PCT and abs(mainMean - REF_MAIN["meanTotal"]) <= REF_TOL_MEAN
    checks.append(("6b. Reference: main spec", okMain,
                   f"{mainNone:.1f}% distress none (ref ~{REF_MAIN['pctNone']:.0f}%), "
                   f"mean total_reach = {mainMean:.2f} (ref ~{REF_MAIN['meanTotal']:.0f})"))

    # 7 direct reach identical across mappings
    mismatch = 0
    nRuns = 0
    for run in allRuns():
        if (run, "linear") not in tables:
            continue
        nRuns += 1
        d = tables[(run, "base")]["direct_reach"]
        mismatch += int((d != tables[(run, "linear")]["direct_reach"]).sum())
        mismatch += int((d != tables[(run, "convex")]["direct_reach"]).sum())
        mismatch += int((d != tables[(run, "single")]["total_reach"]).sum())
    checks.append(("7. direct_reach identical across logistic, linear, convex (and = single-round total)",
                   mismatch == 0, f"{mismatch} mismatching triggers across {nRuns} runs"))

    # 8 recomputed centrality matches network_metrics.csv
    cutoff = params.loc[(params["run"] == "main") & (params["variant"] == "base"), "strong_cutoff"].iloc[0]
    recomputed = mr.getCentrality(sim, metrics, cutoff, "strong", recompute=True)
    saved = mr.getCentrality(sim, metrics, cutoff, "strong", recompute=False)
    centDiff = float((recomputed - saved).abs().max().max())
    checks.append(("8. Recomputed strong-link centrality = _thresh columns in network_metrics.csv",
                   centDiff < CENT_TOL, f"max abs difference = {centDiff:.1e}"))

    # 9 public banks
    public = mr.findPublicBanks(meta)
    checks.append(("9. Exactly 4 public-sector banks matched by name", len(public) == 4,
                   "; ".join(public.values())))

    refFacts = {"allPct": allPct, "nonePct": nonePct, "mainNone": mainNone, "mainMean": mainMean,
                "public": public}
    return checks, refFacts


# ---------- figures ----------

def styleAxes(ax):
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)

def saveFig(fig, path):
    fig.savefig(path, dpi=DPI, facecolor="white")
    plt.close(fig)

def note(ax, x, y, text, **kwargs):
    ax.text(x, y, text, fontsize=8, color=NOTE_INK, **kwargs)

def histogram(series, xlabel, ylabel, path, maxVal):
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.4))
    bins = np.arange(0, maxVal + 6, 5) #5 bank wide bins
    ax.hist(series, bins=bins, color=BLUE, edgecolor="white", linewidth=1)
    ax.set_xlabel(xlabel, color=INK)
    ax.set_ylabel(ylabel, color=INK)
    ax.set_xlim(0, bins[-1])
    styleAxes(ax)
    fig.tight_layout()
    saveFig(fig, path)

def reachAllTriggers(table, path):
    d = table.sort_values(["total_reach", "direct_reach"], ascending=False).reset_index(drop=True)
    n = len(d)
    top = n - 1 #most banks a trigger can distress
    x = np.arange(n)
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.4))
    ax.bar(x, d["direct_reach"], width=0.85, color=BLUE, label="Direct reach (round 1)")
    ax.bar(x, d["indirect_reach"], bottom=d["direct_reach"], width=0.85, color=ORANGE,
           label="Indirect reach (round 2 onwards)")

    started = int((d["total_reach"] > 0).sum())
    if started < n: #grey band over triggers whose cascade never starts
        ax.axvspan(started - 0.5, n - 0.5, color=SHADE, lw=0)
        note(ax, (started + n) / 2 - 0.5, top * 0.42, f"{n - started} banks:\ncascade\nnever starts",
             ha="center", va="center")

    best = d.iloc[0]
    ax.annotate(f"{best['Name']}:\n{best['direct_reach']} direct, {best['indirect_reach']} indirect",
                xy=(0, best["total_reach"]), xytext=(n * 0.17, top * 0.98), fontsize=8, color=NOTE_INK,
                arrowprops=dict(arrowstyle="-", color=NOTE_INK, lw=0.8))
    ax.set_xlim(-1, n)
    ax.set_ylim(0, top * 1.06)
    ax.set_xticks([])
    ax.set_xlabel("Trigger banks, ordered from highest to lowest total reach")
    ax.set_ylabel("Banks distressed")
    styleAxes(ax)
    ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 1), ncol=2, fontsize=8) #above the plot, clear of the band
    fig.tight_layout()
    saveFig(fig, path)

def exposureAllBanks(table, path):
    e = table.sort_values(["exposure", "Name"], ascending=[False, True]).reset_index(drop=True)
    n = len(e)
    never = e["exposure"] == 0
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.0))
    ax.bar(np.arange(n), e["exposure"], width=0.85, color=np.where(never, MUTED, BLUE))

    most = e.iloc[0]
    tiedTop = int((e["exposure"] == most["exposure"]).sum())
    label = f"{most['Name']}: most exposed ({most['exposure']})" if tiedTop == 1 else \
        f"Most exposed: {most['exposure']} ({tiedTop} banks)"
    if tiedTop == 1 and most["total_reach"] == 0:
        label += ",\nbut total reach of 0" #true here, checked rather than assumed
    ax.annotate(label, xy=(0, most["exposure"]), xytext=(n * 0.09, (n - 1) * 0.87), fontsize=8,
                color=NOTE_INK, arrowprops=dict(arrowstyle="-", color=NOTE_INK, lw=0.8))

    nNever = int(never.sum())
    if nNever:
        ax.axvspan(n - nNever - 0.5, n - 0.5, color=SHADE, lw=0)
        noLinks = (e.loc[never, "weighted_degree"] == 0).all() #weighted degree 0 = no strong links
        why = " with no strong links" if noLinks else ""
        note(ax, n - 0.5, (n - 1) * 0.87, f"Grey: {nNever} banks{why},\nnever distressed", ha="right", va="top")
    ax.set_xlim(-1, n + 0.5)
    ax.set_ylim(0, (n - 1) * 0.95)
    ax.set_xticks([])
    ax.set_xlabel("Banks, ordered from most to least exposed")
    ax.set_ylabel("Simulations in which\nthe bank is distressed")
    styleAxes(ax)
    fig.tight_layout()
    saveFig(fig, path)

def centralityScatter(table, rq3Main, path):
    order = rq3Main.sort_values("partial_rho", ascending=False)["centrality"] #strongest panel first
    zero = table["indirect_reach"] == 0
    fig, axes = plt.subplots(2, 2, figsize=(FIG_WIDTH, 5.2))
    for ax, cent in zip(axes.flat, order):
        ax.scatter(table.loc[~zero, cent], table.loc[~zero, "indirect_reach"], s=14, color=BLUE, alpha=0.85,
                   lw=0, label="Indirect reach > 0")
        ax.scatter(table.loc[zero, cent], table.loc[zero, "indirect_reach"], s=14, facecolor="none",
                   edgecolor=MUTED, lw=0.7, label="Indirect reach = 0")
        r = rq3Main.set_index("centrality").loc[cent]
        ax.text(0.97, 0.30, f"ρ = {fmtR(r['spearman_rho'])}\npartial ρ = {fmtR(r['partial_rho'])}",
                transform=ax.transAxes, ha="right", va="center", fontsize=8, color=INK) #sits in the empty band between 0 and the first nonzero reach
        ax.set_xlabel(f"{CENT_LABELS[cent]} (strong-link network)")
        ax.set_ylim(-5, (len(table) - 1) * 0.95)
        ax.ticklabel_format(axis="x", style="plain")
        ax.xaxis.set_major_locator(MaxNLocator(4))
        styleAxes(ax)
    for ax in axes[:, 0]:
        ax.set_ylabel("Indirect reach (banks)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    saveFig(fig, path)

def topBars(table, path):
    top = rankedTable(table, "total_reach").iloc[::-1] #highest at the top of the chart
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 0.3 * len(top) + 1.2))
    y = np.arange(len(top))
    ax.barh(y, top["direct_reach"], height=0.75, color=BLUE, label="Direct reach (round 1)")
    ax.barh(y, top["indirect_reach"], left=top["direct_reach"], height=0.75, color=ORANGE,
            label="Indirect reach (round 2 onwards)")
    ax.set_yticks(y)
    ax.set_yticklabels(top["Name"])
    ax.set_ylim(-0.6, len(top) - 0.4)
    ax.set_xlabel("Banks distressed")
    styleAxes(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.legend(frameon=False, fontsize=8, loc="lower right", bbox_to_anchor=(1, 1), ncol=2) #above the bars
    fig.tight_layout()
    saveFig(fig, path)

def makeFigures(mainT, rq3Main):
    os.makedirs(FIG_DIR, exist_ok=True)
    n = len(mainT)
    files = {
        "fig4_1_reach_all_triggers.png": f"Direct and indirect reach of all {n} trigger banks, sorted by total reach; the grey band marks triggers whose cascade never starts.",
        "fig4_2_exposure_all_banks.png": f"Exposure of all {n} banks, sorted from most to least exposed; grey bars are banks never distressed.",
        "fig4_3_centrality_vs_indirect.png": "Four-panel scatter of each strong-link centrality measure against indirect reach, with Spearman and partial rho in each panel; hollow markers have indirect reach 0.",
        "total_reach_hist.png": f"Histogram of total reach across the {n} trigger banks, 5-bank bins.",
        "exposure_hist.png": f"Histogram of exposure across the {n} banks, 5-simulation bins.",
        "top10_direct_indirect.png": "Stacked bars of direct and indirect reach for the top-10 banks by total reach, including all banks tied at 10th place.",
    }
    reachAllTriggers(mainT, f"{FIG_DIR}/fig4_1_reach_all_triggers.png")
    exposureAllBanks(mainT, f"{FIG_DIR}/fig4_2_exposure_all_banks.png")
    centralityScatter(mainT, rq3Main, f"{FIG_DIR}/fig4_3_centrality_vs_indirect.png")
    histogram(mainT["total_reach"], "Total reach (banks distressed)", "Number of trigger banks",
              f"{FIG_DIR}/total_reach_hist.png", n - 1)
    histogram(mainT["exposure"], "Exposure (simulations in which the bank is distressed)", "Number of banks",
              f"{FIG_DIR}/exposure_hist.png", n - 1)
    topBars(mainT, f"{FIG_DIR}/top10_direct_indirect.png")
    return files


# ---------- report ----------

def gitInfo():
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", "codebase"], capture_output=True, #pycache isnt a code change
                               text=True).stdout.strip()
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True,
                                text=True).stdout.strip()
    except OSError:
        return "unknown", "unknown", False
    return commit, branch, bool(dirty)

def paramLine(p):
    return (f"n = {p['n_banks']} banks, s0 = {p['s0']:.4f}, tau = {p['tau']:.4f}, "
            f"strong-link cut-off = {p['strong_cutoff']:.4f}, strong links = {p['n_strong_links']}")

def getParams(params, run, variant="base"):
    return params[(params["run"] == run) & (params["variant"] == variant)].iloc[0]

def rankRows(table, col, largest, extra):
    ranked = rankedTable(table, col, largest)
    rows = []
    for _, r in ranked.iterrows():
        rank = f"{r['rank']:g}"
        rows.append([rank, r["Name"], r["Country"]] + [int(r[c]) for c in extra])
    return rows

def compareCell(rq2Df, run, comparison, measure):
    row = rq2Df[(rq2Df["run"] == run) & (rq2Df["comparison"] == comparison) & (rq2Df["measure"] == measure)]
    if not len(row):
        return "n/a"
    r = row.iloc[0]
    return f"{fmtR(r['spearman_rho'])} (p {fmtP(r['p_value'])}), top-10 {r['top10_overlap']}/{r['reference_top10_size']}"

def rq3Cell(rq3Df, run, cent):
    r = rq3Df[(rq3Df["run"] == run) & (rq3Df["centrality"] == cent)].iloc[0]
    return (f"rho {fmtR(r['spearman_rho'])} (p {fmtP(r['p_value'])}); "
            f"partial {fmtR(r['partial_rho'])} (p {fmtP(r['partial_p_value'])})")

def partialOf(rq3Df, run, cent):
    return rq3Df[(rq3Df["run"] == run) & (rq3Df["centrality"] == cent)].iloc[0]["partial_rho"]

def robustnessSection(run, params, rq1Df, rq2Df, rq3Df):
    p = getParams(params, run)
    m = rq1Df.loc["main"]
    r = rq1Df.loc[run]
    lines = [f"### {RUN_LABELS[run]} (`{run}`)", "",
             f"Values used: {paramLine(p)}; delta = {p['delta']}, tau percentile = {p['tau_pct']}, "
             f"strong-link percentile = {p['strong_pct']}, later rounds = {p['later_rounds']}, "
             f"centrality = {p['centrality_source']} network"
             f"{' (recomputed)' if p['centrality_recomputed'] else ''}.", ""]
    rows = []
    rq3Only = run in mr.RQ3_ONLY
    if not rq3Only:
        rows += [
            ["RQ1", "Mean total reach", fmtNum(m["mean_total_reach"]), fmtNum(r["mean_total_reach"])],
            ["RQ1", "Triggers with total reach = 0", int(m["zero_total_reach"]), int(r["zero_total_reach"])],
            ["RQ1", "Triggers with indirect reach = 0", int(m["zero_indirect_reach"]), int(r["zero_indirect_reach"])],
            ["RQ1", "rho(total reach, exposure)", fmtR(m["rho_reach_exposure"]), fmtR(r["rho_reach_exposure"])],
            ["RQ1", "Total reach vs main spec", "-", compareCell(rq2Df, run, "main_spec", "total_reach")],
            ["RQ1", "Exposure vs main spec", "-", compareCell(rq2Df, run, "main_spec", "exposure")],
        ]
        for comp in ["linear", "convex", "single"]:
            for measure in ["total_reach", "exposure"]:
                rows.append(["RQ2", f"{MEASURE_LABELS[measure]}: {COMPARE_LABELS[comp].lower()}",
                             compareCell(rq2Df, "main", comp, measure), compareCell(rq2Df, run, comp, measure)])
        for comp in ["linear", "convex"]:
            rows.append(["RQ2", f"Indirect reach: {COMPARE_LABELS[comp].lower()}",
                         compareCell(rq2Df, "main", comp, "indirect_reach"),
                         compareCell(rq2Df, run, comp, "indirect_reach")])
    for cent in mr.CENTRALITIES:
        rows.append(["RQ3", CENT_LABELS[cent], rq3Cell(rq3Df, "main", cent), rq3Cell(rq3Df, run, cent)])
    lines.append(mdTable(["RQ", "Measure", "Main spec", "This run"], rows))
    lines.append("")

    if rq3Only:
        rq1Label = rq2Label = "n/a (cascade identical to main spec)"
    else:
        rq1Label = classify(m["rho_reach_exposure"], r["rho_reach_exposure"])
        rq2Label = classify(rq2Headline(rq2Df, "main"), rq2Headline(rq2Df, run))
    rq3Labels = ", ".join(f"{CENT_LABELS[c]} {classify(partialOf(rq3Df, 'main', c), partialOf(rq3Df, run, c))}"
                          for c in mr.CENTRALITIES)
    lines.append(f"**Headline vs main spec:** RQ1 {rq1Label}; RQ2 {rq2Label}; RQ3 (partial rho) {rq3Labels}.")
    lines.append("")
    return lines

def countSig(rq3Df, run, col):
    sub = rq3Df[rq3Df["run"] == run]
    return int((sub[col] < ALPHA).sum())

def extremes(rq3Df, run, col):
    sub = rq3Df[rq3Df["run"] == run].set_index("centrality")[col]
    lo, hi = sub.idxmin(), sub.idxmax()
    return lo, sub[lo], hi, sub[hi]

def plainSummary(mainT, rq1Df, rq2Df, rq3Df):
    m = rq1Df.loc["main"]
    n = int(m["n_banks"])
    topBank = mainT.sort_values(["total_reach", "Name"], ascending=[False, True]).iloc[0]
    topExp = mainT.sort_values(["exposure", "Name"], ascending=[False, True]).iloc[0]
    nTopExp = int((mainT["exposure"] == topExp["exposure"]).sum())
    directOnly = int(((mainT["direct_reach"] > 0) & (mainT["indirect_reach"] == 0)).sum())
    lines = ["**RQ1.**",
             f"Total reach ranges from {mainT['total_reach'].min()} to {mainT['total_reach'].max()} banks, "
             f"with a mean of {mainT['total_reach'].mean():.2f} and a median of {mainT['total_reach'].median():g}. "
             f"{int(m['zero_total_reach'])} of the {n} trigger banks distress no other bank, and "
             f"{int(m['zero_indirect_reach'])} have no indirect reach ({directOnly} of these distress banks in "
             f"round 1 only). The highest total reach is {topBank['total_reach']} ({topBank['Name']}). "
             f"The highest exposure is {topExp['exposure']} of {n - 1} simulations"
             f"{f' ({topExp.Name})' if nTopExp == 1 else f', shared by {nTopExp} banks'}. "
             f"The Spearman correlation between total reach and exposure is {fmtR(m['rho_reach_exposure'])} "
             f"(p {fmtP(m['p_reach_exposure'])}).", ""]

    def rho(comp, measure):
        return fmtR(rq2Df[(rq2Df["run"] == "main") & (rq2Df["comparison"] == comp) &
                          (rq2Df["measure"] == measure)].iloc[0]["spearman_rho"])

    def ov(comp, measure):
        r = rq2Df[(rq2Df["run"] == "main") & (rq2Df["comparison"] == comp) & (rq2Df["measure"] == measure)].iloc[0]
        return f"{r['top10_overlap']}/{r['reference_top10_size']}"

    lines += ["**RQ2.**",
              f"Direct reach is identical under the logistic, linear and convex mappings for every trigger "
              f"(rho = {rho('linear', 'direct_reach')} and {rho('convex', 'direct_reach')}). "
              f"Indirect reach has rho = {rho('linear', 'indirect_reach')} with the linear mapping and "
              f"{rho('convex', 'indirect_reach')} with the convex mapping. "
              f"For total reach, rho with the main ranking is {rho('linear', 'total_reach')} (linear), "
              f"{rho('convex', 'total_reach')} (convex) and {rho('single', 'total_reach')} (single-round), "
              f"with top-10 overlaps of {ov('linear', 'total_reach')}, {ov('convex', 'total_reach')} and "
              f"{ov('single', 'total_reach')}. "
              f"For exposure, the corresponding rho values are {rho('linear', 'exposure')}, "
              f"{rho('convex', 'exposure')} and {rho('single', 'exposure')}, with top-10 overlaps of "
              f"{ov('linear', 'exposure')}, {ov('convex', 'exposure')} and {ov('single', 'exposure')}.", ""]

    lo, loV, hi, hiV = extremes(rq3Df, "main", "spearman_rho")
    plo, ploV, phi, phiV = extremes(rq3Df, "main", "partial_rho")
    lines += ["**RQ3.**",
              f"On the strong-link network, the Spearman correlation between centrality and indirect reach "
              f"ranges from {fmtR(loV)} ({CENT_LABELS[lo]}) to {fmtR(hiV)} ({CENT_LABELS[hi]}), and "
              f"{countSig(rq3Df, 'main', 'p_value')} of the 4 measures have p < {ALPHA}. "
              f"After controlling for log total assets, CET1 ratio and direct reach, the partial correlation "
              f"ranges from {fmtR(ploV)} ({CENT_LABELS[plo]}) to {fmtR(phiV)} ({CENT_LABELS[phi]}), and "
              f"{countSig(rq3Df, 'main', 'partial_p_value')} of the 4 have p < {ALPHA}. "
              f"On the complete network the partial correlations range from "
              f"{fmtR(rq3Df[rq3Df['run'] == 'complete_centrality']['partial_rho'].min())} to "
              f"{fmtR(rq3Df[rq3Df['run'] == 'complete_centrality']['partial_rho'].max())}.", ""]
    return lines

def anomalies(mainT, tables, rq1Df, rq2Df, rq3Df, params, refFacts):
    n = len(mainT)
    items = []
    sizes = {
        "top-10 total reach": len(topSet(mainT["total_reach"])),
        "bottom-10 total reach": len(topSet(mainT["total_reach"], largest=False)),
        "top-10 exposure": len(topSet(mainT["exposure"])),
        "bottom-10 exposure": len(topSet(mainT["exposure"], largest=False)),
    }
    tied = [f"{k} has {v} banks" for k, v in sizes.items() if v != TOP_N]
    if tied:
        items.append("**Ties in the top/bottom tables.** All banks tied with the 10th bank are kept, so " +
                     "; ".join(tied) + ". Ranks are average ranks (1 = highest). The top-10 overlap in RQ2 is "
                     "reported as k / (size of the reference top-10 set) for the same reason, so it can exceed 10.")
    items.append(f"**Few distinct values.** Main-spec exposure takes only {mainT['exposure'].nunique()} distinct "
                 f"values and total reach {mainT['total_reach'].nunique()}, so rankings contain many ties. "
                 "Spearman rho handles these with average ranks.")
    directOnly = mainT[(mainT["direct_reach"] > 0) & (mainT["indirect_reach"] == 0)]
    items.append(f"**Zero reach.** Every trigger with direct reach 0 also has total reach 0, because later rounds "
                 f"start only from banks distressed in round 1 ({int(rq1Df.loc['main', 'zero_total_reach'])} "
                 f"triggers). A further {len(directOnly)} triggers distress banks in round 1 but none later: "
                 + ", ".join(f"{r['Name']} (direct {r['direct_reach']})" for _, r in directOnly.iterrows()) + ".")
    items.append("**Why direct reach does not depend on the mapping.** All three mappings (logistic, linear, "
                 "convex) only ever increase as similarity increases, and tau is always set at the same "
                 "percentile of each mapping's own values. So whichever mapping is used, round 1 distresses "
                 "exactly the banks whose similarity to the trigger is above the same similarity level. That "
                 "makes direct reach, and the whole single-round model, identical across mappings (validation "
                 "check 7). Any difference between mappings in indirect or total reach comes only from rounds "
                 "2 onwards, where the risk passed on by several distressed banks is added up and the shape of "
                 "the mapping changes those sums.")
    items.append("**Single-round model.** Its total reach equals the main spec's direct reach for every trigger, "
                 "and its indirect reach is always 0. That is why no indirect-reach comparison is reported for it.")
    ref = refFacts
    items.append(f"**Reference results.** delta = 1.0 on the full network: {ref['allPct']:.1f}% of triggers "
                 f"distress all {n - 1} banks, {ref['nonePct']:.1f}% distress none. Main spec: "
                 f"{ref['mainNone']:.1f}% none, mean total reach {ref['mainMean']:.2f}. Both are within the "
                 f"tolerance used ({REF_TOL_PCT:g} percentage points, {REF_TOL_MEAN:g} bank).")
    items.append("**Without the four public-sector banks.** Matched names: " + "; ".join(ref["public"].values()) +
                 ". s0, tau, the strong-link cut-off and all four centralities are recomputed on the 103-bank "
                 "sample. Comparisons with the main spec use the 103 banks present in both, and the main "
                 "top-10 is re-taken on those 103 banks.")
    items.append("**Centrality on the complete network.** The cascade is identical to the main spec, so only "
                 "RQ3 changes. RQ1 and RQ2 are marked n/a.")
    items.append("**pingouin.** It is not installed (and was not installed), so the partial correlation is "
                 "computed only by the rank, OLS-residual and Pearson method described in the brief.")
    items.append(f"**Headline labels.** 'Unchanged / weaker / stronger / reversed' compare a single correlation "
                 f"with the main spec. For RQ1 it is rho(total reach, exposure); for RQ2 it is the smallest of "
                 f"the three rho values for total reach (linear, convex, single-round); for RQ3 it is the "
                 f"partial rho for each measure. The label is 'stronger' or 'weaker' if |rho| changes by at "
                 f"least {TOL}, and 'reversed' if the sign flips and both values have |rho| >= {TOL}. These "
                 f"cut-offs were my choice, not part of the brief.")
    items.append("**Other assumptions.** Percentiles use numpy's default linear interpolation. 'rounds' is the "
                 "last round in which a bank became newly distressed (0 if none). Standard deviations are "
                 "sample standard deviations (ddof = 1). p-values below 0.0005 are shown as <0.001. Linear and "
                 "convex runs keep the strong links defined on similarity and recompute tau on their own values.")
    cascadeRuns = [r for r in allRuns() if r not in mr.RQ3_ONLY]
    negative = [r for r in cascadeRuns if rq1Df.loc[r, "rho_reach_exposure"] < 0]
    items.append("**Reach-exposure correlation across runs** (rho, then number of distinct exposure values): " +
                 ", ".join(f"{r} {fmtR(rq1Df.loc[r, 'rho_reach_exposure'])} "
                           f"({tables[(r, 'base')]['exposure'].nunique()})" for r in cascadeRuns) + "." +
                 (f" It is negative in: {', '.join(negative)}." if negative else ""))
    weakRq3 = rq3Df[(rq3Df["partial_p_value"] >= ALPHA)]
    if len(weakRq3):
        items.append("**RQ3 partial correlations with p >= 0.05:** " +
                     ", ".join(f"{r['run']} {CENT_LABELS[r['centrality']]} ({fmtR(r['partial_rho'])}, "
                               f"p {fmtP(r['partial_p_value'])})" for _, r in weakRq3.iterrows()) + ".")
    items.append("**Same network in model and centrality.** In the main spec, rounds 2 onwards travel along "
                 "the same strong-link network that the four centrality measures are computed on.")
    oddNames = [nm for nm in mainT["Name"] if nm[-1].isdigit()]
    if oddNames:
        items.append("**Bank names.** These names end in a digit in bank_metadata.csv (taken from "
                     "TR_Metadata.xlsx) and are reported as they appear: " + "; ".join(oddNames) + ".")
    sim = mr.loadInputs()[0]
    S = mr.zeroDiagonal(sim)
    offMax = mr.pairValues(S).max()
    if offMax > 1:
        items.append(f"**Floating point.** The largest off-diagonal similarity is {offMax!r}, just above 1 because "
                     "of rounding in the cosine similarity. It is kept as is; the effect on f(s) is below 1e-15.")
    maxRounds = {run: int(tables[(run, 'base')]['rounds'].max()) for run in allRuns()}
    items.append("**Cascade length.** Maximum rounds per run: " +
                 ", ".join(f"{k} {v}" for k, v in maxRounds.items()) + ".")
    return items

def writeReport(tables, params, checks, refFacts, rq1Df, rq2Df, rq3Df, figFiles):
    mainT = tables[("main", "base")]
    p = getParams(params, "main")
    commit, branch, dirty = gitInfo()
    L = ["# Results report", ""]

    # 1 run summary
    L += ["## 1. Run summary", "",
          f"- Date: {datetime.date.today().isoformat()}",
          f"- Git commit (code): `{commit}` on branch `{branch}`"
          f"{' (WARNING: uncommitted changes in codebase/)' if dirty else ''}",
          f"- Number of banks: {p['n_banks']} (pairs: {p['n_banks'] * (p['n_banks'] - 1) // 2})",
          f"- Mapping: {mr.MAPPING}, f(s) = 1 / (1 + exp(-{mr.STEEPNESS}(s - s0))); robustness linear "
          f"{mr.LINEAR_SENS}*s and convex s^{mr.CONVEX_K}",
          f"- s0 (median off-diagonal similarity) = {p['s0']:.4f}",
          f"- Distress threshold: tau = {mr.TAU_PCT}th percentile of off-diagonal f(s) = {p['tau']:.4f}",
          f"- Strong links: similarity >= {mr.STRONG_PCT}th percentile = {p['strong_cutoff']:.4f}, "
          f"giving {p['n_strong_links']} strong links",
          f"- Decay delta = {mr.DELTA}; later rounds along {mr.LATER_ROUNDS} links",
          f"- Centrality: strong-link network (`_thresh` columns of network_metrics.csv)",
          f"- Partial-correlation controls: {', '.join(CONTROLS)}",
          f"- Run as: `python codebase/multiround.py` then `python codebase/analysis.py`", ""]
    otherVariants = [["Linear mapping", getParams(params, "main", "linear")],
                     ["Convex mapping", getParams(params, "main", "convex")]]
    L.append(mdTable(["Main-spec variant", "tau", "s0", "Strong cut-off", "Strong links"],
                     [[name, f"{q['tau']:.4f}", f"{q['s0']:.4f}", f"{q['strong_cutoff']:.4f}", q["n_strong_links"]]
                      for name, q in otherVariants]))
    L.append("")

    # 2 validation
    L += ["## 2. Validation checks", ""]
    L.append(mdTable(["Check", "Result", "Numbers"],
                     [[c, "see note" if ok is None else ("PASS" if ok else "FAIL"), detail] for c, ok, detail in checks]))
    L.append("")

    # 3 descriptive
    L += ["## 3. Descriptive statistics (main spec)", ""]
    desc = describe(mainT)
    L.append(mdTable(["Measure", "Mean", "Median", "Min", "Max", "Std dev", "Zeros"],
                     [[d["measure"], fmtNum(d["mean"]), f"{d['median']:g}", int(d["min"]), int(d["max"]),
                       fmtNum(d["std"]), d["zeros"]] for _, d in desc.iterrows()]))
    L.append("")

    # 4 rq1
    m = rq1Df.loc["main"]
    reachCols = ["total_reach", "direct_reach", "indirect_reach", "rounds"]
    reachHead = ["Rank", "Bank", "Country", "Total", "Direct", "Indirect", "Rounds"]
    L += ["## 4. RQ1: Rankings", "",
          f"Triggers with total reach = 0: **{int(m['zero_total_reach'])}** of {int(m['n_banks'])}. "
          f"Triggers with indirect reach = 0: **{int(m['zero_indirect_reach'])}**. "
          f"Spearman rho(total reach, exposure) = **{fmtR(m['rho_reach_exposure'])}** "
          f"(p {fmtP(m['p_reach_exposure'])}).", "",
          "Ranks are average ranks, 1 = highest. Banks tied with the 10th are included.", "",
          "**Top 10 by total reach**", "", mdTable(reachHead, rankRows(mainT, "total_reach", True, reachCols)), "",
          "**Bottom 10 by total reach**", "", mdTable(reachHead, rankRows(mainT, "total_reach", False, reachCols)), "",
          "**Top 10 by exposure**", "",
          mdTable(["Rank", "Bank", "Country", "Exposure"], rankRows(mainT, "exposure", True, ["exposure"])), "",
          "**Bottom 10 by exposure**", "",
          mdTable(["Rank", "Bank", "Country", "Exposure"], rankRows(mainT, "exposure", False, ["exposure"])), ""]

    # 5 rq2
    L += ["## 5. RQ2: Robustness of the rankings (main spec)", "",
          "Spearman rho between the main-spec ranking and the alternative. The top-10 overlap is the number of "
          "main-spec top-10 banks (ties included) that are also in the alternative's top 10.", ""]
    sub = rq2Df[rq2Df["run"] == "main"]
    L.append(mdTable(["Comparison", "Measure", "rho", "p-value", "Top-10 overlap"],
                     [[COMPARE_LABELS[r["comparison"]], MEASURE_LABELS[r["measure"]], fmtR(r["spearman_rho"]),
                       fmtP(r["p_value"]), f"{r['top10_overlap']}/{r['reference_top10_size']}"]
                      for _, r in sub.iterrows()]))
    L.append("")

    # 6 rq3
    L += ["## 6. RQ3: Centrality and indirect reach (main spec, strong-link network)", "",
          f"Partial Spearman controls: log(total assets), CET1 ratio, direct reach. "
          f"n = {int(m['n_banks'])}, df for the partial test = {int(m['n_banks']) - 2 - len(CONTROLS)}.", ""]
    sub = rq3Df[rq3Df["run"] == "main"]
    L.append(mdTable(["Centrality", "Spearman rho", "p-value", "Partial rho", "Partial p-value", "pingouin check"],
                     [[CENT_LABELS[r["centrality"]], fmtR(r["spearman_rho"]), fmtP(r["p_value"]),
                       fmtR(r["partial_rho"]), fmtP(r["partial_p_value"]), r["pingouin_check"]]
                      for _, r in sub.iterrows()]))
    L.append("")

    # 7 robustness
    L += ["## 7. Robustness", "",
          "Each run changes one setting from the main spec. Cells show Spearman rho (p-value), plus the top-10 "
          "overlap where relevant. For RQ2 rows, the comparison is inside the same run: that run's logistic "
          "multi-round ranking against its own linear, convex or single-round version.", ""]
    for run in mr.ROBUSTNESS:
        L += robustnessSection(run, params, rq1Df, rq2Df, rq3Df)

    # 8 figures
    L += ["## 8. Figures", ""]
    for f, d in figFiles.items():
        L.append(f"- `{FIG_DIR}/{f}`: {d}")
    L.append("")

    # 9 plain english
    L += ["## 9. Plain-English summary", ""]
    L += plainSummary(mainT, rq1Df, rq2Df, rq3Df)

    # 10 anomalies
    L += ["## 10. Anomalies and caveats", ""]
    for item in anomalies(mainT, tables, rq1Df, rq2Df, rq3Df, params, refFacts):
        L.append(f"- {item}")
    L.append("")

    with open(REPORT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))


def main():
    params = pd.read_csv(mr.PARAMS_FILE)
    tables = loadTables(params)
    print(f"Loaded {len(tables)} runs")

    checks, refFacts = validationChecks(tables, params)
    print("\n--- validation ---")
    for c, ok, detail in checks:
        print(f"{'NOTE' if ok is None else ('PASS' if ok else 'FAIL')}  {c}: {detail}")
    if not all(ok for _, ok, _ in checks if ok is not None):
        raise SystemExit("A validation check failed, stopping before writing results")

    rq1Rows, rq2Rows, rq3Rows = [], [], []
    for run in allRuns():
        table = tables[(run, "base")]
        row = rq1(table)
        row["run"] = run
        rq1Rows.append(row)
        if run not in mr.RQ3_ONLY:
            rq2Rows += rq2(run, tables)
        rq3Rows += rq3(run, table)
    rq1Df = pd.DataFrame(rq1Rows).set_index("run")
    rq2Df = pd.DataFrame(rq2Rows)
    rq3Df = pd.DataFrame(rq3Rows)

    rq1Df.to_csv(RQ1_FILE)
    rq2Df.to_csv(RQ2_FILE, index=False)
    rq3Df.to_csv(RQ3_FILE, index=False)

    figFiles = makeFigures(tables[("main", "base")], rq3Df[rq3Df["run"] == "main"])
    writeReport(tables, params, checks, refFacts, rq1Df, rq2Df, rq3Df, figFiles)
    print(f"\nSaved {RQ1_FILE}, {RQ2_FILE}, {RQ3_FILE}, figures to {FIG_DIR}/ and {REPORT_FILE}")


if __name__ == "__main__":
    main()
