import pandas as pd
import numpy as np
from math import sqrt
import json
from scipy.stats import ttest_ind, chi2_contingency


def read_data(path):
    return pd.read_csv(path)


def column(m, col):
    return m[col]


def norm(v):
    return sqrt(np.dot(v, v))


def contingency_table(x, y):
    xvals = list(set(x))
    yvals = list(set(y))
    contingency = np.array([np.zeros(len(xvals)) for _ in range(len(yvals))])
    for xv, yv in zip(x, y):
        xi = xvals.index(xv)
        yi = yvals.index(yv)
        contingency[xi][yi] += 1
    return contingency


def corr_str(x, y):
    contingency = contingency_table(x, y)
    chi2, p, dof, expected = chi2_contingency(contingency)
    return 1 - p


def correlation(v1, v2, f=corr_str):
    """v1 v2 are numpy vectors"""
    # Extract indices where they are defined
    validIndex = np.logical_and(~np.isnan(v1), ~np.isnan(v2))
    v1 = v1[validIndex]
    v2 = v2[validIndex]
    # What to do if one is zero?
    return f(v1, v2)


def correlation_matrix(df, cols=None):
    """df is a dataframe"""
    if not cols:
        cols = df.columns
    answer = []
    for col1 in cols:
        row = []
        for col2 in cols:
            if col1 == col2:
                row.append(np.double(0))
            else:
                row.append(correlation(df[col1], df[col2]))
        answer.append(row)
    return answer


def size(v):
    v = v[~np.isnan(v)]
    values = set(v)
    assert values == set([0.0, 1.0])
    return sum(v) / len(v)


def network_layout(corrs, sizes, labels):
    answer = {'nodes': [], 'edges': []}
    for id, size in enumerate(sizes):
        answer['nodes'].append({'id': 'n%s' % id,
                                'size': size,
                                'label': labels[id]})
    counter = 0
    for i, row in enumerate(corrs):
        for j, corr in enumerate(row):
            # Symmetric: only do one direction
            if i < j:
                answer['edges'].append(
                    {'id': 'e%s' % counter,
                     'source': 'n%s' % i,
                     'target': 'n%s' % j,
                     'weight': corr})
                counter += 1
    return answer


def data_network(df, cols):
    df = df[cols]
    corr = correlation_matrix(df)
    sizes = [size(df[col]) for col in cols]
    network = network_layout(corr, sizes, cols)
    return network


def data_tree(df, cols, name="root"):
    "Only use on categorical data"
    if cols:
        col = cols[0]
        rest = cols[1:]

        vals = set(v for v in df[col] if not np.isnan(v))
        children = []
        for val in vals:
            # %i is a massive hack
            children.append(
                data_tree(df[df[col] == val], rest, "%s: %i" % (col, val)))
        return {'name': name, 'children': children}
    else:
        return {'name':  name, 'size': len(df)}