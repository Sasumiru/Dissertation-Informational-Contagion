import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg") #no window, just save the png
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy import stats
import multiround as mr
from networkconstruction import buildGraph, findCentrality #imports
sys.stdout.reconfigure(encoding="utf-8")


TOP_N = 10 #size of the top and bottom tables, ties at the edge are all kept
CONTROLS = ["log_total_assets", "cet1_ratio", "direct_reach"] #partial correlation controls
RUNS = ["main"] + list(mr.ROBUSTNESS)
FIG_DIR = "output/figures"

# figure colours and ink
BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e6e5e1"
SHADE = "#efeeeb" #background band behind banks that are never hit
NOTE_INK = "#52514e" #annotation text
FIG_WIDTH = 6.5 #inches, fits the page width so text prints at its real size

plt.rcParams.update({ #one style for every figure
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.labelcolor": INK,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

CENT_LABELS = {"weighted_degree": "Weighted degree", "eigenvector": "Eigenvector",
               "pagerank": "PageRank", "betweenness": "Betweenness"}


def fmtR(x):
    return "n/a" if pd.isna(x) else f"{x:.2f}"

def fmtP(p):
    if pd.isna(p):
        return "n/a"
    return "<0.001" if p < 0.0005 else f"{p:.3f}" #anything that rounds to 0.000 shows as <0.001

def mdTable(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)

def spearman(a, b):
    common = a.index.intersection(b.index) #only banks in both samples
    a, b = a[common], b[common]
    if a.nunique() < 2 or b.nunique() < 2: #constant series has no rank correlation
        return np.nan, np.nan
    res = stats.spearmanr(a, b)
    return float(res[0]), float(res[1])

def topSet(series, largest=True):
    if largest:
        edge = series.nlargest(TOP_N).iloc[-1]
        return set(series[series >= edge].index) #keeps every bank tied with the 10th
    edge = series.nsmallest(TOP_N).iloc[-1]
    return set(series[series <= edge].index)

def partialSpearman(data, x, y):
    ranks = data[[x, y] + CONTROLS].rank(method="average") #rank everything first
    n = len(ranks)
    Z = np.column_stack([np.ones(n), ranks[CONTROLS].values]) #intercept + control ranks
    resX = ranks[x].values - Z @ np.linalg.lstsq(Z, ranks[x].values, rcond=None)[0] #ols residuals
    resY = ranks[y].values - Z @ np.linalg.lstsq(Z, ranks[y].values, rcond=None)[0]
    r = float(np.corrcoef(resX, resY)[0, 1])
    df = n - 2 - len(CONTROLS)
    t = r * np.sqrt(df / (1 - r ** 2))
    p = float(2 * stats.t.sf(abs(t), df)) #two sided
    return r, p, n

def rankRows(table, col, largest, cols):
    keep = sorted(topSet(table[col], largest))
    ranked = table.loc[keep].copy()
    ranked["rank"] = table[col].rank(ascending=False, method="average")[ranked.index] #1 = highest
    ranked = ranked.sort_values([col, "Name"], ascending=[not largest, True])
    return [[f"{r['rank']:g}", r["Name"], r["Country"]] + [int(r[c]) for c in cols] for _, r in ranked.iterrows()]

def styleAxes(ax):
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)

def makeFigures(mainT, rq3Main):
    os.makedirs(FIG_DIR, exist_ok=True)
    n = len(mainT)

    # fig 4.1, direct and indirect reach of every trigger
    d = mainT.sort_values(["total_reach", "direct_reach"], ascending=False).reset_index(drop=True)
    top = n - 1 #most banks a trigger can distress
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.4))
    ax.bar(np.arange(n), d["direct_reach"], width=0.85, color=BLUE, label="Direct reach (round 1)")
    ax.bar(np.arange(n), d["indirect_reach"], bottom=d["direct_reach"], width=0.85, color=ORANGE,
           label="Indirect reach (round 2 onwards)")
    started = int((d["total_reach"] > 0).sum())
    ax.axvspan(started - 0.5, n - 0.5, color=SHADE, lw=0) #grey band over triggers whose cascade never starts
    ax.text((started + n) / 2 - 0.5, top * 0.42, f"{n - started} banks:\ncascade\nnever starts",
            fontsize=8, color=NOTE_INK, ha="center", va="center")
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
    fig.savefig(f"{FIG_DIR}/fig4_1_reach_all_triggers.png", dpi=300, facecolor="white")
    plt.close(fig)

    # fig 4.2, exposure of every bank
    e = mainT.sort_values(["exposure", "Name"], ascending=[False, True]).reset_index(drop=True)
    never = e["exposure"] == 0
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.0))
    ax.bar(np.arange(n), e["exposure"], width=0.85, color=np.where(never, MUTED, BLUE))
    most = e.iloc[0]
    tiedTop = int((e["exposure"] == most["exposure"]).sum())
    if tiedTop > 1: #only name the bank if its the only one at the top
        label = f"Most exposed: {most['exposure']} ({tiedTop} banks)"
    else:
        label = f"{most['Name']}: most exposed ({most['exposure']})"
        if most["total_reach"] == 0:
            label += ",\nbut total reach of 0"
    ax.annotate(label, xy=(0, most["exposure"]), xytext=(n * 0.09, (n - 1) * 0.87), fontsize=8,
                color=NOTE_INK, arrowprops=dict(arrowstyle="-", color=NOTE_INK, lw=0.8))
    nNever = int(never.sum())
    ax.axvspan(n - nNever - 0.5, n - 0.5, color=SHADE, lw=0)
    why = " with no strong links" if (e.loc[never, "weighted_degree"] == 0).all() else "" #weighted degree 0 = no strong links
    ax.text(n - 0.5, (n - 1) * 0.87, f"Grey: {nNever} banks{why},\nnever distressed", fontsize=8, color=NOTE_INK,
            ha="right", va="top")
    ax.set_xlim(-1, n + 0.5)
    ax.set_ylim(0, (n - 1) * 0.95)
    ax.set_xticks([])
    ax.set_xlabel("Banks, ordered from most to least exposed")
    ax.set_ylabel("Simulations in which\nthe bank is distressed")
    styleAxes(ax)
    fig.tight_layout()
    fig.savefig(f"{FIG_DIR}/fig4_2_exposure_all_banks.png", dpi=300, facecolor="white")
    plt.close(fig)

    # fig 4.3, each centrality against indirect reach, strongest panel first
    order = rq3Main.sort_values("partial_rho", ascending=False)["centrality"]
    zero = mainT["indirect_reach"] == 0
    fig, axes = plt.subplots(2, 2, figsize=(FIG_WIDTH, 5.2))
    for ax, cent in zip(axes.flat, order):
        ax.scatter(mainT.loc[~zero, cent], mainT.loc[~zero, "indirect_reach"], s=14, color=BLUE, alpha=0.85,
                   lw=0, label="Indirect reach > 0")
        ax.scatter(mainT.loc[zero, cent], mainT.loc[zero, "indirect_reach"], s=14, facecolor="none",
                   edgecolor=MUTED, lw=0.7, label="Indirect reach = 0")
        r = rq3Main.set_index("centrality").loc[cent]
        ax.text(0.97, 0.30, f"ρ = {fmtR(r['spearman_rho'])}\npartial ρ = {fmtR(r['partial_rho'])}",
                transform=ax.transAxes, ha="right", va="center", fontsize=8, color=INK) #sits in the gap between 0 and the first nonzero reach
        ax.set_xlabel(f"{CENT_LABELS[cent]} (strong-link network)")
        ax.set_ylim(-5, (n - 1) * 0.95)
        ax.ticklabel_format(axis="x", style="plain")
        ax.xaxis.set_major_locator(MaxNLocator(4))
        styleAxes(ax)
    for ax in axes[:, 0]:
        ax.set_ylabel("Indirect reach (banks)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(f"{FIG_DIR}/fig4_3_centrality_vs_indirect.png", dpi=300, facecolor="white")
    plt.close(fig)

def main():
    params = pd.read_csv("output/run_parameters.csv")
    tables = {}
    for run, variant in zip(params["run"], params["variant"]):
        if run == "main" and variant == "base":
            path = "output/reach_exposure_main.csv"
        elif variant == "base":
            path = f"output/robustness/{run}.csv"
        else:
            path = f"output/variants/{run}_{variant}.csv"
        tables[(run, variant)] = pd.read_csv(path).set_index("LEI_Code")
    mainT = tables[("main", "base")]
    print(f"Loaded {len(tables)} runs")

    # validation section
    sim, meta, metrics = mr.loadInputs()
    mainP = params[(params["run"] == "main") & (params["variant"] == "base")].iloc[0]
    asym = params["max_abs_asymmetry"].max()
    diag = params["max_abs_diagonal"].max()
    badSum = sum(int((t["direct_reach"] + t["indirect_reach"] != t["total_reach"]).sum()) for t in tables.values())
    badExp = sum(t["exposure"].sum() != t["total_reach"].sum() for t in tables.values())
    selfHits = int(np.diag(pd.read_csv("output/cascade_rounds_main.csv", index_col=0).values).astype(bool).sum())

    badDirect = 0
    for run in RUNS:
        if run == "complete_centrality": #no other versions of this run
            continue
        direct = tables[(run, "base")]["direct_reach"]
        badDirect += int((direct != tables[(run, "linear")]["direct_reach"]).sum())
        badDirect += int((direct != tables[(run, "convex")]["direct_reach"]).sum())
        badDirect += int((direct != tables[(run, "single")]["total_reach"]).sum())

    recomputed = findCentrality(buildGraph(sim, mainP["strong_cutoff"]))[mr.CENTRALITIES]
    saved = metrics[[c + "_thresh" for c in mr.CENTRALITIES]]
    saved.columns = mr.CENTRALITIES
    centDiff = float((recomputed - saved).abs().max().max())
    public = mr.findPublicBanks(meta)

    checks = [
        ("Similarity matrix symmetric, diagonal 0", asym == 0 and diag == 0,
         f"max asymmetry {asym:.1e}, max diagonal {diag:.1e}, all {len(params)} runs"),
        ("direct + indirect = total", badSum == 0, f"{badSum} mismatches across {len(tables)} runs"),
        ("Sum of exposure = sum of total reach", badExp == 0, f"main: {mainT['exposure'].sum()} = {mainT['total_reach'].sum()}, {badExp} runs differ"),
        ("No trigger distresses itself", selfHits == 0, f"{selfHits} cases in cascade_rounds_main.csv (multiround asserts this for every run too)"),
        ("Direct reach same across logistic, linear, convex (and = single-round total)", badDirect == 0, f"{badDirect} mismatches"),
        ("Recomputed centrality = _thresh columns in network_metrics.csv", centDiff < 1e-10, f"max difference {centDiff:.1e}"),
        ("Four public-sector banks found", len(public) == 4, "; ".join(public.values())),
    ]
    print("\n--- validation ---")
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    if not all(ok for _, ok, _ in checks):
        raise SystemExit("A validation check failed, stopping before writing results")

    # summaries, comparisons and correlations for every run
    rq1Rows, rq2Rows, rq3Rows = [], [], []
    for run in RUNS:
        table = tables[(run, "base")]
        rho, p = spearman(table["total_reach"], table["exposure"])
        rq1Rows.append({
            "n_banks": len(table),
            "mean_total_reach": table["total_reach"].mean(),
            "zero_total_reach": int((table["total_reach"] == 0).sum()),
            "zero_indirect_reach": int((table["indirect_reach"] == 0).sum()),
            "rho_reach_exposure": rho,
            "p_reach_exposure": p,
            "run": run,
        })

        if run != "complete_centrality":
            allMeasures = ["direct_reach", "indirect_reach", "total_reach", "exposure"]
            comparisons = [ #(name, reference table, other table, measures)
                ("linear", table, tables[(run, "linear")], allMeasures),
                ("convex", table, tables[(run, "convex")], allMeasures),
                ("single", table, tables[(run, "single")], ["total_reach", "exposure"]), #single round has no indirect reach
            ]
            if run != "main":
                comparisons.append(("main_spec", mainT, table, ["total_reach", "exposure"]))
            for comparison, ref, other, measures in comparisons:
                for measure in measures:
                    rho, p = spearman(ref[measure], other[measure])
                    common = ref.index.intersection(other.index)
                    refTop = topSet(ref.loc[common, measure])
                    otherTop = topSet(other.loc[common, measure])
                    rq2Rows.append({
                        "run": run,
                        "comparison": comparison,
                        "measure": measure,
                        "spearman_rho": rho,
                        "p_value": p,
                        "top10_overlap": len(refTop & otherTop),
                        "reference_top10_size": len(refTop),
                        "other_top10_size": len(otherTop),
                        "n_banks": len(common),
                    })

        for cent in mr.CENTRALITIES:
            rho, p = spearman(table[cent], table["indirect_reach"])
            pr, pp, n = partialSpearman(table, cent, "indirect_reach")
            rq3Rows.append({
                "run": run,
                "network": "complete" if run == "complete_centrality" else "strong",
                "centrality": cent,
                "n_banks": n,
                "spearman_rho": rho,
                "p_value": p,
                "partial_rho": pr,
                "partial_p_value": pp,
            })

    rq1 = pd.DataFrame(rq1Rows).set_index("run")
    rq2 = pd.DataFrame(rq2Rows)
    rq3 = pd.DataFrame(rq3Rows)

    # save results
    rq1.to_csv("output/rq1_summary.csv")
    rq2.to_csv("output/rq2_comparisons.csv", index=False)
    rq3.to_csv("output/rq3_correlations.csv", index=False)
    makeFigures(mainT, rq3[rq3["run"] == "main"])
    print("Saved rq1_summary.csv, rq2_comparisons.csv, rq3_correlations.csv and figures to output/")

    # report section
    m = rq1.loc["main"]
    L = ["# Results report", "",
         f"Main spec: {mainP['n_banks']} banks, {mr.MAPPING} mapping, s0 = {mainP['s0']:.4f}, tau = {mainP['tau']:.4f} "
         f"({mr.TAU_PCT}th pct), strong-link cut-off = {mainP['strong_cutoff']:.4f} ({mr.STRONG_PCT}th pct, "
         f"{mainP['n_strong_links']} links), delta = {mr.DELTA}.", ""]

    L += ["## Validation", "", mdTable(["Check", "Result", "Numbers"],
          [[name, "PASS" if ok else "FAIL", detail] for name, ok, detail in checks]), ""]

    descRows = []
    for col in ["total_reach", "direct_reach", "indirect_reach", "exposure", "rounds"]:
        s = mainT[col]
        descRows.append([col, f"{s.mean():.2f}", f"{s.median():g}", int(s.min()), int(s.max()), f"{s.std():.2f}", int((s == 0).sum())]) #sample sd
    L += ["## Descriptive statistics", "", mdTable(["Measure", "Mean", "Median", "Min", "Max", "Std dev", "Zeros"], descRows), ""]

    reachCols = ["total_reach", "direct_reach", "indirect_reach", "rounds"]
    reachHead = ["Rank", "Bank", "Country", "Total", "Direct", "Indirect", "Rounds"]
    expHead = ["Rank", "Bank", "Country", "Exposure"]
    L += ["## Rankings", "",
          f"{int(m['zero_total_reach'])} of {int(m['n_banks'])} triggers have total reach 0, {int(m['zero_indirect_reach'])} have indirect reach 0. "
          f"rho(total reach, exposure) = {fmtR(m['rho_reach_exposure'])} (p {fmtP(m['p_reach_exposure'])}). Ranks are average ranks, ties with 10th kept.", "",
          "**Top 10 by total reach**", "", mdTable(reachHead, rankRows(mainT, "total_reach", True, reachCols)), "",
          "**Bottom 10 by total reach**", "", mdTable(reachHead, rankRows(mainT, "total_reach", False, reachCols)), "",
          "**Top 10 by exposure**", "", mdTable(expHead, rankRows(mainT, "exposure", True, ["exposure"])), "",
          "**Bottom 10 by exposure**", "", mdTable(expHead, rankRows(mainT, "exposure", False, ["exposure"])), ""]

    sub = rq2[rq2["run"] == "main"]
    L += ["## Mapping and rounds comparison", "",
          "Spearman rho between the main ranking and each alternative, top-10 overlap counts ties.", "",
          mdTable(["Comparison", "Measure", "rho", "p-value", "Top-10 overlap"],
                  [[r["comparison"], r["measure"], fmtR(r["spearman_rho"]), fmtP(r["p_value"]),
                    f"{r['top10_overlap']}/{r['reference_top10_size']}"] for _, r in sub.iterrows()]), ""]

    sub = rq3[rq3["run"] == "main"]
    L += ["## Centrality and indirect reach", "",
          f"Strong-link network. Partial rho controls for {', '.join(CONTROLS)}.", "",
          mdTable(["Centrality", "rho", "p-value", "Partial rho", "Partial p-value"],
                  [[CENT_LABELS[r["centrality"]], fmtR(r["spearman_rho"]), fmtP(r["p_value"]), fmtR(r["partial_rho"]),
                    fmtP(r["partial_p_value"])] for _, r in sub.iterrows()]), ""]

    robRows = []
    for run in RUNS:
        r = rq1.loc[run]
        vsMain = rq2[(rq2["run"] == run) & (rq2["comparison"] == "main_spec") & (rq2["measure"] == "total_reach")]
        partials = rq3[rq3["run"] == run].set_index("centrality")["partial_rho"]
        robRows.append([run, f"{r['mean_total_reach']:.2f}", int(r["zero_total_reach"]), fmtR(r["rho_reach_exposure"]),
                        fmtR(vsMain["spearman_rho"].iloc[0]) if len(vsMain) else "-"] + [fmtR(partials[c]) for c in mr.CENTRALITIES])
    L += ["## Robustness", "",
          "Each run changes one setting from the main spec. complete_centrality only changes the centrality network.", "",
          mdTable(["Run", "Mean total reach", "Zero reach", "rho(reach, exposure)", "Total reach rho vs main"]
                  + [f"Partial rho {CENT_LABELS[c]}" for c in mr.CENTRALITIES], robRows), ""]

    with open("output/results_report.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    print("Saved output/results_report.md")


if __name__ == "__main__":
    main()
