import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score #imports
sys.stdout.reconfigure(encoding="utf-8")


MAPPINGS = ["logistic", "convex", "linear"] #logistic is the main one, other two are the robustness check
CENTRALITIES = ["weighted_degree", "betweenness", "eigenvector", "pagerank"]
CONTROLS = ["cet1_ratio", "log_assets"]

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

def runOLS(data, centrality, dv):
    cols = [centrality] + CONTROLS
    X = standardise(data, cols)
    X = sm.add_constant(X) #adds the intercept
    y = data[dv]
    model = sm.OLS(y, X).fit(cov_type="HC1") #robust standard errors
    return model

def runClassifier(data, centrality, dv):
    cols = [centrality] + CONTROLS
    X = standardise(data, cols)
    y = data[dv] > data[dv].median() #True = more concentrated than the median bank
    y = y.astype(int) #True/False to 1/0

    # leave one out: take one bank out, train on the rest, predict the one taken out, repeat for every bank
    probs = []
    for i in range(len(X)):
        trainX = X.drop(X.index[i])
        trainY = y.drop(y.index[i])
        testX = X.iloc[[i]] #double brackets so it stays a table with one row

        clf = LogisticRegression()
        clf.fit(trainX, trainY)
        prob = clf.predict_proba(testX)[0][1] #chance this bank is a 1
        probs.append(prob)

    # cant get an auc from one bank so score all the predictions together at the end
    auc = roc_auc_score(y, probs)
    return auc

def runAll(data, sampleName, mapping):
    dv = "top10_share_" + mapping
    rows = []
    for network in ["complete", "thresholded"]:
        for centrality in CENTRALITIES: #one model each, they are too correlated to go in together
            if network == "complete":
                col = centrality
            else:
                col = centrality + "_thresh"

            model = runOLS(data, col, dv)
            auc = runClassifier(data, col, dv)
            rows.append({
                "mapping": mapping,
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
    print(f"Loaded {len(data)} banks")

    for lei in AGENCIES:
        if lei not in data.index:
            print(f"agency not found in data: {AGENCIES[lei]}")

    # collinearity check
    print("\n--- correlation between centralities, complete network ---")
    print(data[CENTRALITIES].corr().round(2))
    threshCols = []
    for centrality in CENTRALITIES:
        threshCols.append(centrality + "_thresh")
    print("\n--- correlation between centralities, thresholded network ---")
    print(data[threshCols].corr().round(2))

    noAgencyData = data.drop(index=list(AGENCIES)) #same data without the 4 agencies

    # run every model for every mapping, full sample and without the agencies
    allResults = []
    for mapping in MAPPINGS:
        allResults.append(runAll(data, "full", mapping))
        allResults.append(runAll(noAgencyData, "no_agencies", mapping))
    allResults = pd.concat(allResults)

    # main results are the logistic mapping
    mainResults = allResults[allResults["mapping"] == "logistic"]
    pd.set_option("display.width", 200)
    print("\n--- logistic mapping (main results) ---")
    print(mainResults.round(3).to_string(index=False))

    # mapping robustness, only the thresholded network matters since the complete one is inflated
    thresh = allResults[allResults["network"] == "thresholded"]
    thresh = thresh.sort_values(["centrality", "mapping", "sample"])
    print("\n--- mapping robustness, thresholded network ---")
    print(thresh[["centrality", "mapping", "sample", "coef_centrality", "p_centrality"]].round(3).to_string(index=False))

    # save results
    mainResults.to_csv(f"output/regression_results.csv", index=False)
    allResults.to_csv(f"output/mapping_robustness.csv", index=False)
    print(f"\nSaved {len(mainResults)} models to output/regression_results.csv")
    print(f"Saved {len(allResults)} models to output/mapping_robustness.csv")


if __name__ == "__main__":
    main()
