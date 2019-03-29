""" Data processing module. """

# Imports

import networkx as nx
from networkit import linkprediction as lp, nxadapter
from functools import partial
import pandas as pd


# Define local functions

def assign_label(pair, graph):
    u, v = pair[0], pair[1]
    return (int(graph.hasEdge(u, v)))


def concatenate(node_set, label):
    dataset = pd.DataFrame({'nodes': node_set, 'label': label})
    return dataset


def main():
    """
    Create training and testing graphs, compute feature engineering
    and save datasets.
    """

    # Graph import
    G = nx.read_edgelist('data/graph.txt', comments='#')
    valid_graph = nxadapter.nx2nk(G)

    # Training and test graphs creation
    test_graph = lp.RandomLinkSampler.byPercentage(valid_graph, 0.9)
    train_graph = lp.RandomLinkSampler.byPercentage(test_graph, 0.7)

    # Training and testing sets creation
    testing_set = lp.MissingLinksFinder(test_graph).findAtDistance(2)
    training_set = lp.MissingLinksFinder(train_graph).findAtDistance(2)

    # Label creation
    y_train = list(map(partial(assign_label, graph=test_graph), training_set))
    y_test = list(map(partial(assign_label, graph=valid_graph), testing_set))

    # Concatenation of labels with samples
    train = concatenate(training_set, y_train)
    test = concatenate(testing_set, y_test)
    trainingSet = train.nodes.values
    testingSet = test.nodes.values

    # Feature engineering
    trainLPs = [
        lp.CommonNeighborsIndex(train_graph), lp.JaccardIndex(train_graph),
        lp.AdamicAdarIndex(train_graph), lp.ResourceAllocationIndex(train_graph),
        lp.PreferentialAttachmentIndex(train_graph), lp.AdjustedRandIndex(train_graph),
        lp.NeighborhoodDistanceIndex(train_graph), lp.TotalNeighborsIndex(train_graph),
        lp.SameCommunityIndex(train_graph), lp.UDegreeIndex(train_graph),
        lp.VDegreeIndex(train_graph)
    ]

    testLPs = [
        lp.CommonNeighborsIndex(test_graph), lp.JaccardIndex(test_graph),
        lp.AdamicAdarIndex(test_graph), lp.ResourceAllocationIndex(test_graph),
        lp.PreferentialAttachmentIndex(test_graph), lp.AdjustedRandIndex(test_graph),
        lp.NeighborhoodDistanceIndex(test_graph), lp.TotalNeighborsIndex(test_graph),
        lp.SameCommunityIndex(test_graph), lp.UDegreeIndex(test_graph), lp.VDegreeIndex(test_graph)
    ]

    X_train = lp.getFeatures(trainingSet, *trainLPs)
    X_test = lp.getFeatures(testingSet, *testLPs)

    # Concatenate features with samples and labels
    features = ['CN', 'JC', 'AA', 'RA', 'PA', 'AR', 'ND', 'TN', 'SC', 'UD', 'VD']
    train_features = pd.DataFrame(X_train, columns=features)
    test_features = pd.DataFrame(X_test, columns=features)
    train = pd.concat([train, train_features], axis=1)
    test = pd.concat([test, test_features], axis=1)

    # Export files as csv
    train.to_csv('data/train.csv', sep=';', header=True, decimal='.', encoding='utf-8', index=False)
    test.to_csv('data/test.csv', sep=';', header=True, decimal='.', encoding='utf-8', index=False)


if __name__ == "main":
    main()
