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

PUBLIC_BANKS = ["BNG Bank", "SFIL", "Kommuninvest", "Kuntarahoitus"] #matched by name in bank_metadata.csv
CENTRALITIES = ["weighted_degree", "eigenvector", "pagerank", "betweenness"]

# robustness runs, each one changes ONE setting from the main spec
ROBUSTNESS = {
    "no_public_banks": {"dropPublic": True},
    "strong_link_70": {"strongPct": 70},
    "strong_link_80": {"strongPct": 80},
    "complete_centrality": {"centralitySource": "complete"}, #centrality only, cascade same as main
    "delta_1.0": {"delta": 1.0},
    "delta_0.3": {"delta": 0.3},
    "delta_0.7": {"delta": 0.7},
    "tau_95": {"tauPct": 95},
    "later_rounds_full": {"laterRounds": "full"},
}

# other versions of each run, single = round 1 only with the main mapping
VARIANTS = {
    "linear": {"mapping": "linear"},
    "convex": {"mapping": "convex"},
    "single": {"singleRound": True},
}

OUT_COLS = ["LEI_Code", "Name", "Country", "direct_reach", "indirect_reach", "total_reach", "rounds",
            "exposure"] + CENTRALITIES + ["log_total_assets", "cet1_ratio"]


def loadInputs():
    sim = pd.read_csv("output/similarity_matrix.csv", index_col=0)
    sim.columns = sim.index #column names same as row names
    meta = pd.read_csv("output/bank_metadata.csv").set_index("LEI_Code")
    metrics = pd.read_csv("output/network_metrics.csv", index_col=0)
    return sim, meta, metrics

def findPublicBanks(meta):
    matched = {}
    for name in PUBLIC_BANKS:
        hits = meta[meta["Name"].str.contains(name, case=False, regex=False)]
        if len(hits) != 1: #has to be exactly one bank per name
            raise ValueError(f"'{name}' matched {len(hits)} banks: {list(hits['Name'])}")
        matched[hits.index[0]] = hits["Name"].iloc[0]
    return matched

def pairValues(mat):
    upper = np.triu_indices(len(mat), k=1) #upper triangle, each pair once, no diagonal
    return np.asarray(mat)[upper]

def runCascade(F, links, trigger, tau, delta, maxRounds=None):
    risk = F[trigger].copy() #round 1, everyone gets f(s_ij) through the full network
    risk[trigger] = 0.0 #trigger never receives risk
    roundHit = np.zeros(len(F), dtype=int) #round each bank is first distressed, 0 = never

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

def runSpec(sim, meta, metrics, mapping=MAPPING, delta=DELTA, tauPct=TAU_PCT, strongPct=STRONG_PCT,
            laterRounds=LATER_ROUNDS, centralitySource=CENTRALITY_SOURCE, dropPublic=False, singleRound=False):
    if dropPublic:
        public = list(findPublicBanks(meta))
        sim = sim.drop(index=public, columns=public)

    S = sim.values.astype(float).copy()
    np.fill_diagonal(S, 0.0) #a bank isnt linked to itself

    # risk mapping, s0 recomputed for each sample
    s0 = np.median(pairValues(S))
    if mapping == "logistic":
        F = riskLogistic(S, midpoint=s0, steepness=STEEPNESS)
    elif mapping == "linear":
        F = riskLinear(S, sensitivity=LINEAR_SENS)
    else:
        F = riskConvex(S, k=CONVEX_K)
    np.fill_diagonal(F, 0.0) #no risk to itself
    tau = np.percentile(pairValues(F), tauPct) #separate tau for each mapping

    cutoff = np.percentile(pairValues(S), strongPct) #numpy default linear interpolation
    strong = S >= cutoff
    np.fill_diagonal(strong, False)
    if laterRounds == "strong":
        links = strong
    else:
        links = ~np.eye(len(S), dtype=bool) #every link except itself

    # cascade from every trigger, row = trigger, column = bank
    maxRounds = 1 if singleRound else None
    roundMat = np.array([runCascade(F, links, t, tau, delta, maxRounds) for t in range(len(F))])

    hit = roundMat > 0
    out = pd.DataFrame(index=pd.Index(sim.index, name="LEI_Code"))
    out["direct_reach"] = (roundMat == 1).sum(axis=1)
    out["indirect_reach"] = (roundMat >= 2).sum(axis=1)
    out["total_reach"] = hit.sum(axis=1)
    out["rounds"] = roundMat.max(axis=1) #last round with a newly distressed bank, 0 if none
    out["exposure"] = hit.sum(axis=0) #column sums, times bank j got distressed by the other triggers

    # centrality section
    recompute = dropPublic or strongPct != STRONG_PCT #cut-off or sample changed so rebuild the network
    if centralitySource == "complete":
        cent = metrics[CENTRALITIES]
    elif recompute:
        cent = findCentrality(buildGraph(sim, cutoff))[CENTRALITIES]
    else:
        cent = metrics[[c + "_thresh" for c in CENTRALITIES]]
        cent.columns = CENTRALITIES

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

def main():
    sim, meta, metrics = loadInputs()
    print(f"Loaded similarity matrix: {sim.shape[0]} x {sim.shape[1]} banks")

    print("public sector banks matched:")
    for lei, name in findPublicBanks(meta).items():
        print(f"  {name} ({lei})")

    os.makedirs("output/robustness", exist_ok=True)
    os.makedirs("output/variants", exist_ok=True)

    runs = {"main": {}}
    runs.update(ROBUSTNESS)
    paramRows = []
    for run, settings in runs.items():
        variants = {"base": {}}
        if run != "complete_centrality": #cascade same as main so no other versions needed
            variants.update(VARIANTS)

        for variant, extra in variants.items():
            table, roundMat, params = runSpec(sim, meta, metrics, **settings, **extra)
            paramRows.append({"run": run, "variant": variant, **params})

            # save results
            if run == "main" and variant == "base":
                table.to_csv("output/reach_exposure_main.csv", index=False)
                pd.DataFrame(roundMat, index=sim.index, columns=sim.index).to_csv("output/cascade_rounds_main.csv") #first distress round, row = trigger
                mainTable, mainParams = table, params
            elif variant == "base":
                table.to_csv(f"output/robustness/{run}.csv", index=False)
            else:
                table.to_csv(f"output/variants/{run}_{variant}.csv", index=False)
        print(f"  ran {run} ({len(variants)} versions)")

    pd.DataFrame(paramRows).to_csv("output/run_parameters.csv", index=False)

    p = mainParams
    print(f"\nmain spec: s0={p['s0']:.4f}, tau={p['tau']:.4f}, cut-off={p['strong_cutoff']:.4f}, "
          f"strong links={p['n_strong_links']}")
    print(f"mean total_reach={mainTable['total_reach'].mean():.2f}, "
          f"zero total_reach={(mainTable['total_reach'] == 0).sum()}, max rounds={mainTable['rounds'].max()}")
    print(f"\nSaved {len(paramRows)} runs to output/reach_exposure_main.csv, output/robustness/ and output/variants/")


if __name__ == "__main__":
    main()
