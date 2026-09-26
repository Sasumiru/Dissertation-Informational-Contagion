import sys

import networkx as nx
import pandas as pd
from datacleaner import loadCapital

def graph(sim):
    G = nx.Graph()  #Creating a graph

    G.add_nodes_from(sim.index)  # Nodes one per bank LEI

    banks = list(sim.index)
    for i in range(len(banks)):
        for j in range(i + 1, len(banks)):  # j starts after i so each pair is only added once
            a = banks[i]
            b = banks[j]
            G.add_edge(a, b, weight=sim.loc[a, b])  # "Edge Attributes": weight = similarity score

    return G

