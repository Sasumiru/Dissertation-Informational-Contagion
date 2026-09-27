import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict #imports
sys.stdout.reconfigure(encoding="utf-8")


DV = "top10_share_logistic" #swap to _linear or _convex for the robustness check
CENTRALITIES = ["weighted_degree", "betweenness", "eigenvector", "pagerank"]
CONTROLS = ["cet1_ratio", "log_assets"]
NETWORKS = {"complete": "", "thresholded": "_thresh"} #column suffix for each network

# municipal funding agencies, not normal commercial banks so they get dropped in the robustness check
AGENCIES = {
    "529900GGYMNGRQTDOO93": "BNG Bank",
    "549300HFEHJOXGE4ZE63": "SFIL",
    "EV2XZWMLLXF2QRX0CD47": "Kommuninvest",
    "529900HEKOENJHPNN480": "Kuntarahoitus",
}

def loadData():
    metrics = pd.read_csv(f"output/network_metrics.csv", index_col=0)
    attack = pd.read_csv(f"output/attack_results.csv", index_col=0)
    data = metrics.join(attack, how="inner") #only keeps banks in both files
    data["log_assets"] = np.log(data["total_assets"]) #assets are really skewed so log them
    return data

def standardise(data, cols):
    return (data[cols] - data[cols].mean()) / data[cols].std() #so coefficients are comparable

def runOLS(data, centrality):
    cols = [centrality] + CONTROLS
    X = sm.add_constant(standardise(data, cols))
    y = data[DV]
    model = sm.OLS(y, X).fit(cov_type="HC1") #robust standard errors
    return model

def runClassifier(data, centrality):
    cols = [centrality] + CONTROLS
    X = standardise(data, cols)
    y = (data[DV] > data[DV].median()).astype(int) #1 = more concentrated than the median bank

    # leave one out, train on every other bank and predict the one left out
    # cant get an auc from one bank so collect all the predictions first then score them together
    probs = cross_val_predict(LogisticRegression(), X, y, cv=LeaveOneOut(), method="predict_proba")[:, 1]
    return roc_auc_score(y, probs)

def runAll(data, sampleName):
    rows = []
    for network, suffix in NETWORKS.items():
        for centrality in CENTRALITIES: #one model each, they are too correlated to go in together
            col = centrality + suffix
            model = runOLS(data, col)
            auc = runClassifier(data, col)
            rows.append({
                "sample": sampleName,
                "network": network,
                "centrality": centrality,
                "coef_centrality": model.params[col],
                "p_centrality": model.pvalues[col],
                "coef_cet1": model.params["cet1_ratio"],
                "p_cet1": model.pvalues["cet1_ratio"],
                "coef_assets": model.params["log_assets"],
                "p_assets": model.pvalues["log_assets"],
                "r2": model.rsquared,
                "n": int(model.nobs),
                "auc": auc,
            })
    return pd.DataFrame(rows)

def main():
    data = loadData()
    print(f"Loaded {len(data)} banks, DV = {DV}")

    missing = [name for lei, name in AGENCIES.items() if lei not in data.index]
    if len(missing):
        print(f"agencies not found in data: {missing}")

    # collinearity check
    for network, suffix in NETWORKS.items():
        cols = [c + suffix for c in CENTRALITIES]
        print(f"\n--- correlation between centralities, {network} network ---")
        print(data[cols].corr().round(2).to_string())

    # full sample then without the agencies
    full = runAll(data, "full")
    noAgencies = runAll(data.drop(index=list(AGENCIES), errors="ignore"), "no_agencies")
    results = pd.concat([full, noAgencies])

    pd.set_option("display.width", 200)
    print("\n--- full sample ---")
    print(full.drop(columns="sample").round(3).to_string(index=False))
    print("\n--- without the 4 agencies ---")
    print(noAgencies.drop(columns="sample").round(3).to_string(index=False))

    # save results
    results.to_csv(f"output/regression_results.csv", index=False)
    print(f"\nSaved {len(results)} models to output/regression_results.csv")


if __name__ == "__main__":
    main()
