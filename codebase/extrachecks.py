import sys
import numpy as np
import pandas as pd
from scipy import stats
from attacksim import riskLogistic #imports
sys.stdout.reconfigure(encoding="utf-8")


SIM_FILE = "output/similarity_matrix.csv"
SHARES_FILE = "output/bank_sector_shares.csv"
MAIN_FILE = "output/reach_exposure_main.csv"
PARAMS_FILE = "output/run_parameters.csv"
REPORT_FILE = "output/results_report.md"
OUT_FILE = "output/extra_checks.csv"

REAL_ESTATE = "12" #nace code 12 = L real estate activities
STEEPNESS = 10 #same as multiround
TAU_PCT = 90
CONTROLS = ["log_total_assets", "cet1_ratio", "direct_reach"]
CENTRALITIES = ["weighted_degree", "eigenvector", "pagerank", "betweenness"]


def upperValues(mat):
    i, j = np.triu_indices(len(mat), k=1) #each pair once, no diagonal
    return mat[i, j]

def medianCosine(shares):
    X = shares.div(shares.sum(axis=1), axis=0).fillna(0).values #back to shares after dropping a column
    norms = np.linalg.norm(X, axis=1)
    norms[norms == 0] = 1 #stops dividing by zero
    C = (X @ X.T) / np.outer(norms, norms)
    return float(np.median(upperValues(C)))

def partialSpearman(data, x, y, controls):
    ranks = data[[x, y] + controls].rank()
    Z = np.column_stack([np.ones(len(ranks)), ranks[controls].values]) #intercept + control ranks
    resX = ranks[x].values - Z @ np.linalg.lstsq(Z, ranks[x].values, rcond=None)[0]
    resY = ranks[y].values - Z @ np.linalg.lstsq(Z, ranks[y].values, rcond=None)[0]
    r = float(np.corrcoef(resX, resY)[0, 1])
    df = len(ranks) - 2 - len(controls)
    t = r * np.sqrt(df / (1 - r ** 2))
    p = float(2 * stats.t.sf(abs(t), df)) #two sided
    return r, p, len(ranks)

def fmtP(p):
    return "<0.001" if p < 0.0005 else f"{p:.3f}"

def main():
    sim = pd.read_csv(SIM_FILE, index_col=0)
    S = sim.values.astype(float)
    np.fill_diagonal(S, 0.0)
    mainT = pd.read_csv(MAIN_FILE).set_index("LEI_Code")
    params = pd.read_csv(PARAMS_FILE)
    p = params[(params["run"] == "main") & (params["variant"] == "base")].iloc[0]
    rows = []

    # zero reach banks vs banks with no close lookalike
    F = riskLogistic(S, midpoint=p["s0"], steepness=STEEPNESS)
    np.fill_diagonal(F, 0.0)
    maxRisk = pd.Series(F.max(axis=1), index=sim.index) #biggest risk any one bank could get from a single trigger
    noLookalike = set(maxRisk[maxRisk < p["tau"]].index)
    zeroReach = set(mainT[mainT["total_reach"] == 0].index)
    sCut = np.percentile(upperValues(S), TAU_PCT) #same threshold on the similarity scale
    rows.append({"check": "zero_reach_equals_no_lookalike", "value": float(noLookalike == zeroReach),
                 "detail": f"{len(zeroReach)} zero reach banks, {len(noLookalike)} with no match above "
                           f"similarity {sCut:.4f}, {len(zeroReach & noLookalike)} in both"})

    # median similarity with and without real estate
    shares = pd.read_csv(SHARES_FILE, index_col=0)
    shares.columns = shares.columns.astype(str)
    rows.append({"check": "median_similarity_with_real_estate", "value": medianCosine(shares),
                 "detail": "should match s0 in run_parameters.csv"})
    rows.append({"check": "median_similarity_without_real_estate",
                 "value": medianCosine(shares.drop(columns=REAL_ESTATE)),
                 "detail": "real estate dropped, shares re-normalised"})
    rows.append({"check": "real_estate_share_min", "value": float(shares[REAL_ESTATE].min()), "detail": ""})
    rows.append({"check": "real_estate_share_max", "value": float(shares[REAL_ESTATE].max()), "detail": ""})

    # rq3 again but only banks that start a cascade
    casc = mainT[mainT["direct_reach"] > 0]
    rho, pVal = stats.spearmanr(casc["direct_reach"], casc["indirect_reach"])
    rows.append({"check": "cascading_rho_direct_vs_indirect", "value": float(rho),
                 "detail": f"n = {len(casc)}, p {fmtP(pVal)}"})
    for cent in CENTRALITIES:
        r, pp, n = partialSpearman(casc, cent, "indirect_reach", CONTROLS)
        rows.append({"check": f"cascading_partial_{cent}", "value": r, "detail": f"n = {n}, p {fmtP(pp)}"})

    # h1, similarity vs total reach
    Sn = S.copy(); np.fill_diagonal(Sn, np.nan)
    simStats = pd.DataFrame({"mean_similarity": np.nanmean(Sn, axis=1),
                             "n_strong_links": (Sn >= p["strong_cutoff"]).sum(axis=1),
                             "max_similarity": np.nanmax(Sn, axis=1)}, index=sim.index)
    h1 = mainT.join(simStats)
    for sub, tag in [(h1, "all"), (h1[h1["direct_reach"] > 0], "cascading")]:
        for col in simStats.columns:
            rho, pVal = stats.spearmanr(sub[col], sub["total_reach"])
            rows.append({"check": f"h1_{tag}_{col}_vs_total_reach", "value": float(rho),
                         "detail": f"n = {len(sub)}, p {fmtP(pVal)}"})
    # save results
    out = pd.DataFrame(rows)
    out.to_csv(OUT_FILE, index=False)
    print(out.to_string(index=False))

    # add to the end of the report, replacing an old extra checks section if its there
    with open(REPORT_FILE, encoding="utf-8") as f:
        report = f.read().split("\n## Extra checks")[0].rstrip("\n")
    lines = ["", "", "## Extra checks", "", "| Check | Value | Detail |", "|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['check']} | {r['value']:.4f} | {r['detail']} |")
    with open(REPORT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(report + "\n".join(lines) + "\n")
    print(f"\nSaved {OUT_FILE} and added the section to {REPORT_FILE}")


if __name__ == "__main__":
    main()