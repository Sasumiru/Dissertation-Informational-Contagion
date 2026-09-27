import sys
import networkx as nx
import numpy as np
import pandas as pd
from datacleaner import loadMeta
from sklearn.metrics.pairwise import cosine_similarity #iimports
sys.stdout.reconfigure(encoding="utf-8")


TESTBANK = "0W2PZJM8XOY22M4GG883"  #  first bank in similarity_matrix.csv

# mapping functions, similarity -> risk, all give a score between 0 and 1
def riskLinear(sim, sensitivity):
    return sim * sensitivity

def riskConvex(sim, k=2):
    return sim ** k #only really similar banks get much risk

def riskLogistic(sim, midpoint=0.5, steepness=10):
    return 1 / (1 + np.exp(-steepness * (sim - midpoint))) #s shaped, never exactly 0 or 1

def runSim(sim: pd.DataFrame, trigger: str, mappingFn, **kwargs) -> pd.DataFrame:
    similarity = sim.loc[trigger].drop(index=trigger)
    assert similarity.between(0, 1).all(), "similarity out of [0,1]" #negatives would break sim ** k
    risk = mappingFn(similarity, **kwargs)
    assert risk.between(0, 1).all(), "risk out of [0,1]"
    result = pd.DataFrame({
        "similarity_to_trigger": similarity,
        "transmitted_risk": risk,
    })
    result.index.name = "LEI_Code"
    return result.sort_values("transmitted_risk", ascending=False)

def summarise(result):
    risk = result["transmitted_risk"]
    top10Share = risk.nlargest(10).sum() / risk.sum() #only one thats comparable across mappings
    return {
        "mean_risk": risk.mean(),
        "total_risk": risk.sum(),
        "top10_share": top10Share,
    }

def runAllBanks(sim, midpoint):
    rows = []
    for trigger in sim.index: #every bank gets a turn as the trigger
        linear = runSim(sim, trigger, riskLinear, sensitivity=0.5)
        convex = runSim(sim, trigger, riskConvex, k=2)
        logistic = runSim(sim, trigger, riskLogistic, midpoint=midpoint, steepness=10)
        rows.append({
            "LEI_Code": trigger,
            "top10_share_linear": summarise(linear)["top10_share"],
            "top10_share_convex": summarise(convex)["top10_share"],
            "top10_share_logistic": summarise(logistic)["top10_share"],
        })
    return pd.DataFrame(rows).set_index("LEI_Code")

def main():
    sim = pd.read_csv(f"output/similarity_matrix.csv", index_col=0)
    print(f"Loaded similarity matrix: {sim.shape[0]} x {sim.shape[1]} banks")
    print(f"Trigger bank: {TESTBANK} (in matrix: {TESTBANK in sim.index})")

    # logistic midpoint from the whole matrix so its the same curve whichever bank is the trigger
    pairs = []
    banks = list(sim.index)
    for i in range(len(banks)):
        for j in range(i + 1, len(banks)): 
            pairs.append(sim.iloc[i, j])
    midpoint = np.median(pairs)

    # run each mapping
    results = {
        "linear": runSim(sim, TESTBANK, riskLinear, sensitivity=0.5),
        "convex": runSim(sim, TESTBANK, riskConvex, k=2),
        "logistic": runSim(sim, TESTBANK, riskLogistic, midpoint=midpoint, steepness=10),
    }

    allRisk = pd.DataFrame({"similarity to trigger": sim.loc[TESTBANK].drop(index=TESTBANK)}) #risk columns line up on LEI
    summary = []
    for name, result in results.items():
        allRisk[f"risk_{name}"] = result["transmitted_risk"]
        row = summarise(result)
        row["mapping"] = name
        summary.append(row)

        print(f"\n--- {name} ---")
        print(f"Range: min={result['transmitted_risk'].min():.4f}, max={result['transmitted_risk'].max():.4f}")
        print("top 5 banks receiving risk:")
        print(result["transmitted_risk"].head().to_string())

    allRisk.index.name = "LEI_Code"
    allRisk = allRisk.sort_values("similarity to trigger", ascending=False)

    summary = pd.DataFrame(summary).set_index("mapping")
    print(f"\n--- summary (even spread would be top10_share = {10 / len(allRisk):.3f}) ---")
    print(summary)

    # sanity check not a result, all mappings go up with similarity so ranks have to match
    spearman = allRisk.corr(method="spearman")
    print(f"\nmonotonicity check (all spearman = 1): {np.allclose(spearman.values, 1)}")

    # save results
    allRisk.to_csv(f"output/attack_single_test.csv")
    summary.to_csv(f"output/attack_mapping_summary.csv")
    print(f"\nSaved risk for {len(allRisk)} banks and mapping summary to output/")

    # all banks as the trigger, one row per bank
    allBanks = runAllBanks(sim, midpoint)
    allBanks.to_csv(f"output/attack_results.csv")
    print(f"\nSaved top10_share for {len(allBanks)} trigger banks to output/attack_results.csv")
    print(allBanks.describe())
    print("\ncorrelation between mappings:") #high = choice of mapping doesnt matter much
    print(allBanks.corr())
    print(allBanks.sort_values('top10share_logistic', ascending=False).head(3))


if __name__ == "__main__":
    main()