import os
import sys
import numpy as np
import pandas as pd
from attacksim import riskLinear, riskConvex, riskLogistic
from networkconstruction import buildGraph, findCentrality #imports
sys.stdout.reconfigure(encoding="utf-8")


# main spec
MAPPING = "logistic" #main mapping, linear and convex are robustness
DELTA = 0.5 #decay, risk passed on in round r is multiplied by DELTA ** (r - 1)
TAU_PCT = 90 #distress threshold = this percentile of all pairwise f(s)
STRONG_PCT = 75 #strong link cut-off = this percentile of all pairwise similarities
LATER_ROUNDS = "strong" #which links rounds 2+ travel along, "strong" or "full"
CENTRALITY_SOURCE = "strong" #"strong" = strong-link network, "complete" = every edge

# mapping settings, same values as attacksim
STEEPNESS = 10
LINEAR_SENS = 0.5
CONVEX_K = 2

# public sector banks, matched by name in bank_metadata.csv
PUBLIC_BANKS = ["BNG Bank", "SFIL", "Kommuninvest", "Kuntarahoitus"]

CENTRALITIES = ["weighted_degree", "eigenvector", "pagerank", "betweenness"]
VARIANTS = ["linear", "convex", "single"] #rq2 versions of each run, single = round 1 only, main mapping

SIM_FILE = "output/similarity_matrix.csv"
METRICS_FILE = "output/network_metrics.csv"
META_FILE = "output/bank_metadata.csv"
MAIN_FILE = "output/reach_exposure_main.csv"
ROUNDS_FILE = "output/cascade_rounds_main.csv"
PARAMS_FILE = "output/run_parameters.csv"
ROBUST_DIR = "output/robustness"
VARIANT_DIR = "output/variants"

# robustness runs, each one changes ONE setting from the main spec
ROBUSTNESS = {
    "no_public_banks": {"dropPublic": True},
    "strong_link_70": {"strongPct": 70},
    "strong_link_80": {"strongPct": 80},
    "complete_centrality": {"centralitySource": "complete"}, #rq3 only, cascade same as main
    "delta_1.0": {"delta": 1.0},
    "delta_0.3": {"delta": 0.3},
    "delta_0.7": {"delta": 0.7},
    "tau_95": {"tauPct": 95},
    "later_rounds_full": {"laterRounds": "full"},
}
RQ3_ONLY = ["complete_centrality"] #no rq2 variants needed for these

OUT_COLS = ["LEI_Code", "Name", "Country", "direct_reach", "indirect_reach", "total_reach", "rounds",
            "exposure"] + CENTRALITIES + ["log_total_assets", "cet1_ratio"]


def loadInputs():
    sim = pd.read_csv(SIM_FILE, index_col=0)
    sim.columns = sim.index #column names same as row names
    meta = pd.read_csv(META_FILE).set_index("LEI_Code")
    metrics = pd.read_csv(METRICS_FILE, index_col=0)
    return sim, meta, metrics

def findPublicBanks(meta):
    matched = {}
    for name in PUBLIC_BANKS:
        hits = meta[meta["Name"].str.contains(name, case=False, regex=False)]
        if len(hits) != 1: #has to be exactly one bank per name
            raise ValueError(f"'{name}' matched {len(hits)} banks: {list(hits['Name'])}")
        matched[hits.index[0]] = hits["Name"].iloc[0]
    if len(matched) != len(PUBLIC_BANKS):
        raise ValueError(f"expected {len(PUBLIC_BANKS)} public banks, found {len(matched)}")
    return matched

def pairValues(mat):
    upper = np.triu_indices(len(mat), k=1) #upper triangle, each pair once, no diagonal
    return np.asarray(mat)[upper]

def zeroDiagonal(sim):
    S = sim.values.astype(float).copy()
    np.fill_diagonal(S, 0.0) #a bank isnt linked to itself
    return S

def buildRisk(S, mapping):
    s0 = np.median(pairValues(S)) #logistic midpoint, recomputed for each sample
    if mapping == "logistic":
        F = riskLogistic(S, midpoint=s0, steepness=STEEPNESS)
    elif mapping == "linear":
        F = riskLinear(S, sensitivity=LINEAR_SENS)
    elif mapping == "convex":
        F = riskConvex(S, k=CONVEX_K)
    else:
        raise ValueError(f"unknown mapping {mapping}")
    F = np.array(F, dtype=float)
    np.fill_diagonal(F, 0.0) #no risk to itself
    return F, s0

def strongLinks(S, strongPct):
    cutoff = np.percentile(pairValues(S), strongPct) #numpy default linear interpolation
    strong = S >= cutoff
    np.fill_diagonal(strong, False)
    return strong, cutoff

def runCascade(F, links, trigger, tau, delta, maxRounds=None):
    n = len(F)
    risk = F[trigger].copy() #round 1, everyone gets f(s_ij) through the full network
    risk[trigger] = 0.0 #trigger never receives risk
    roundHit = np.zeros(n, dtype=int) #round each bank is first distressed, 0 = never

    new = np.flatnonzero(risk >= tau)
    new = new[new != trigger]
    roundHit[new] = 1

    r = 1
    while len(new) and (maxRounds is None or r < maxRounds):
        r += 1
        passed = (F[new] * links[new]).sum(axis=0) * delta ** (r - 1) #newly distressed pass on once
        passed[trigger] = 0.0
        risk += passed #cumulative across rounds

        new = np.flatnonzero((risk >= tau) & (roundHit == 0))
        new = new[new != trigger]
        roundHit[new] = r

    assert roundHit[trigger] == 0, "trigger counted as distressed"
    return roundHit

def runAllTriggers(F, links, tau, delta, maxRounds=None):
    rows = []
    for trigger in range(len(F)): #every bank gets a turn as the trigger
        rows.append(runCascade(F, links, trigger, tau, delta, maxRounds))
    return np.array(rows) #row = trigger, column = bank

def bankOutcomes(roundMat, banks):
    hit = roundMat > 0
    out = pd.DataFrame(index=pd.Index(banks, name="LEI_Code"))
    out["direct_reach"] = (roundMat == 1).sum(axis=1)
    out["indirect_reach"] = (roundMat >= 2).sum(axis=1)
    out["total_reach"] = hit.sum(axis=1)
    out["rounds"] = roundMat.max(axis=1) #last round with a newly distressed bank, 0 if none
    out["exposure"] = hit.sum(axis=0) #column sums, times bank j distressed by the other triggers
    return out

def getCentrality(sim, metrics, cutoff, source, recompute):
    if source == "complete":
        return metrics[CENTRALITIES].copy() #non _thresh columns
    if recompute: #cut-off or sample changed so rebuild like networkconstruction.py
        return findCentrality(buildGraph(sim, cutoff))[CENTRALITIES]
    cent = metrics[[c + "_thresh" for c in CENTRALITIES]].copy()
    cent.columns = CENTRALITIES
    return cent

def runSpec(sim, meta, metrics, mapping=MAPPING, delta=DELTA, tauPct=TAU_PCT, strongPct=STRONG_PCT,
            laterRounds=LATER_ROUNDS, centralitySource=CENTRALITY_SOURCE, dropPublic=False, singleRound=False):
    if dropPublic:
        public = findPublicBanks(meta)
        sim = sim.drop(index=list(public), columns=list(public))

    S = zeroDiagonal(sim)
    F, s0 = buildRisk(S, mapping)
    tau = np.percentile(pairValues(F), tauPct) #separate tau for each mapping
    strong, cutoff = strongLinks(S, strongPct)

    if laterRounds == "strong":
        links = strong
    elif laterRounds == "full":
        links = ~np.eye(len(S), dtype=bool) #every link except itself
    else:
        raise ValueError(f"unknown laterRounds {laterRounds}")

    maxRounds = 1 if singleRound else None
    roundMat = runAllTriggers(F, links, tau, delta, maxRounds)
    out = bankOutcomes(roundMat, sim.index)

    recompute = dropPublic or strongPct != STRONG_PCT
    cent = getCentrality(sim, metrics, cutoff, centralitySource, recompute)
    out = out.join(cent)
    out = out.join(meta[["Name", "Country", "cet1_ratio", "total_assets"]])
    out["log_total_assets"] = np.log(out["total_assets"])
    out = out.reset_index()[OUT_COLS]

    params = {
        "n_banks": len(S),
        "mapping": mapping,
        "model": "single_round" if singleRound else "multi_round",
        "delta": delta,
        "tau_pct": tauPct,
        "strong_pct": strongPct,
        "later_rounds": laterRounds,
        "centrality_source": centralitySource,
        "centrality_recomputed": recompute and centralitySource != "complete",
        "dropped_public_banks": dropPublic,
        "s0": s0,
        "tau": tau,
        "strong_cutoff": cutoff,
        "n_strong_links": int(strong.sum() // 2),
        "max_abs_asymmetry": float(np.abs(S - S.T).max()),
        "max_abs_diagonal": float(np.abs(np.diag(S)).max()),
    }
    return out, roundMat, params

def variantSettings(variant):
    if variant == "single":
        return {"singleRound": True}
    return {"mapping": variant}

def runEverything(sim, meta, metrics):
    results = {} #(run, variant) -> (table, roundMat, params)
    runs = {"main": {}}
    runs.update(ROBUSTNESS)
    for run, settings in runs.items():
        results[(run, "base")] = runSpec(sim, meta, metrics, **settings)
        if run in RQ3_ONLY:
            continue
        for variant in VARIANTS: #same run, other mapping or single round
            results[(run, variant)] = runSpec(sim, meta, metrics, **settings, **variantSettings(variant))
    return results

def outputPath(run, variant):
    if run == "main" and variant == "base":
        return MAIN_FILE
    if variant == "base":
        return f"{ROBUST_DIR}/{run}.csv"
    return f"{VARIANT_DIR}/{run}_{variant}.csv"

def paramTable(results):
    rows = []
    for (run, variant), (_, _, params) in results.items():
        row = {"run": run, "variant": variant}
        row.update(params)
        rows.append(row)
    return pd.DataFrame(rows)

def main():
    sim, meta, metrics = loadInputs()
    print(f"Loaded similarity matrix: {sim.shape[0]} x {sim.shape[1]} banks")

    public = findPublicBanks(meta)
    print("public sector banks matched:")
    for lei, name in public.items():
        print(f"  {name} ({lei})")

    os.makedirs(ROBUST_DIR, exist_ok=True)
    os.makedirs(VARIANT_DIR, exist_ok=True)

    results = runEverything(sim, meta, metrics)
    for (run, variant), (table, _, _) in results.items():
        table.to_csv(outputPath(run, variant), index=False)

    # first distress round for every trigger (row) and bank (column), main spec
    mainRounds = results[("main", "base")][1]
    pd.DataFrame(mainRounds, index=sim.index, columns=sim.index).to_csv(ROUNDS_FILE)

    params = paramTable(results)
    params.to_csv(PARAMS_FILE, index=False)

    mainTable = results[("main", "base")][0]
    p = results[("main", "base")][2]
    print(f"\nmain spec: s0={p['s0']:.4f}, tau={p['tau']:.4f}, cut-off={p['strong_cutoff']:.4f}, "
          f"strong links={p['n_strong_links']}")
    print(f"mean total_reach={mainTable['total_reach'].mean():.2f}, "
          f"zero total_reach={(mainTable['total_reach'] == 0).sum()}, max rounds={mainTable['rounds'].max()}")
    print(f"\nSaved {len(results)} runs to {MAIN_FILE}, {ROBUST_DIR}/ and {VARIANT_DIR}/")


if __name__ == "__main__":
    main()
