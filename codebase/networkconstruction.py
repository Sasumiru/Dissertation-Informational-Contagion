import sys

import networkx as nx
import pandas as pd
from datacleaner import loadMeta
from sklearn.metrics.pairwise import cosine_similarity #iimports

def buildGraph(sim, cutoff=0):
    G = nx.Graph() #empty graph
    G.add_nodes_from(sim.index) #one node per bank

    banks = list(sim.index)
    for i in range(len(banks)):
        for j in range(i + 1, len(banks)): #start after i so each pair only goes in once
            a = banks[i]
            b = banks[j]
            if sim.loc[a, b] >= cutoff: #cutoff 0 keeps every edge
                G.add_edge(a, b, weight=sim.loc[a, b]) #edge weight is the similarity score

    return G

def findCentrality(G):
    weightedDegree = dict(G.degree(weight="weight"))

    # betweenness needs distance not similarity so flip it
    distG = nx.Graph()
    distG.add_nodes_from(G.nodes())
    for a, b, data in G.edges(data=True):
        dist = 1.0 - data["weight"]
        if dist < 0: #can go slightly under 0 from rounding
            dist = 0.0
        distG.add_edge(a, b, distance=dist)

    # centrality section
    betweenness = nx.betweenness_centrality(distG, weight="distance")
    eigenvector = nx.eigenvector_centrality(G, weight="weight", max_iter=1000) #more tries so it works
    pagerank = nx.pagerank(G, weight="weight")

    results = pd.DataFrame({
        "weighted_degree": weightedDegree,
        "betweenness": betweenness,
        "eigenvector": eigenvector,
        "pagerank": pagerank,
    })
    return results

def main():
    sim = pd.read_csv(f"output/similarity_matrix.csv", index_col=0)
    sim.columns = sim.index #column names same as row names

    G = buildGraph(sim)
    print(f"Graph has {G.number_of_nodes()} banks and {G.number_of_edges()} edges")

    centrality = findCentrality(G)

    # second network with only the top 25% of edges, so centrality isnt built from the same numbers as the DV
    weights = [data["weight"] for a, b, data in G.edges(data=True)]
    cutoff = pd.Series(weights).quantile(0.75)
    GThresh = buildGraph(sim, cutoff)
    print(f"Thresholded graph (similarity >= {cutoff:.3f}) has {GThresh.number_of_edges()} edges")

    centralityThresh = findCentrality(GThresh).add_suffix("_thresh") #weighted_degree_thresh etc
    centrality = centrality.join(centralityThresh)

    meta = loadMeta(sim.index) #bank names, country and capital
    meta = meta.set_index("LEI_Code") #LEI as the index so it lines up with centrality

    metrics = centrality.join(meta, how="left")

    capCols = metrics[["cet1_ratio", "total_capital_ratio", "total_assets"]]
    noCapital = capCols.isna().any(axis=1) #True if any capital number is blank
    missing = metrics[noCapital].index
    if len(missing):
        print(f"{len(missing)} banks have no capital data: {list(missing)}")

    # save results
    metrics.index.name = "LEI_Code"
    metrics = metrics.sort_values("weighted_degree", ascending=False) #biggest first
    metrics.to_csv(f"output/network_metrics.csv")

    print(f"Saved network metrics for {len(metrics)} banks to output/")
    top10 = metrics[["Name", "weighted_degree", "eigenvector", "pagerank", "cet1_ratio"]].head(10)
    print("top 10 banks:")
    print(top10)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8") #so bank names with accents print
    sim = pd.read_csv(f"output/similarity_matrix.csv", index_col=0)
    sim.columns = sim.index
    print("sim shape:", sim.shape)
    print("sim first 5x5:")
    print(sim.iloc[:5, :5])
    print("sim NaNs:", sim.isna().sum().sum()) #should be 0
    G = buildGraph(sim)
    print("nodes, edges:", G.number_of_nodes(), G.number_of_edges())
    centrality = findCentrality(G)
    print("centrality head:")
    print(centrality.head())
    print("centrality summary:")
    print(centrality.describe())
    print("pagerank sum:", centrality["pagerank"].sum()) #should be 1
    main()
