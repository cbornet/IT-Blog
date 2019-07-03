""" Classifier module. """

# Imports

from collections import Counter

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

import pickle


# Define local functions

def preprocess_df(df):
    processed_df = df.copy()
    zero = Counter(processed_df.label.values)[0]
    un = Counter(processed_df.label.values)[1]
    n = zero - un
    processed_df['SC'] = processed_df['SC'].astype('category')
    processed_df['label'] = processed_df['label'].astype('category')
    processed_df = pd.get_dummies(processed_df, columns=['SC'])
    processed_df = processed_df.drop(
        processed_df[processed_df.label == 0].sample(n=n, random_state=1).index)
    return processed_df.sample(frac=1)


def get_X_y(df):
    X = df.drop(['label', 'nodes'], axis=1)
    y = df['label']
    return X, y


def main():
    """ Import data, compute pre-processing, classify
        and save results.
    """

    # Data import + fix the class imbalance issue
    train = preprocess_df(pd.read_csv('data/train.csv', sep=";", decimal=".", encoding="utf-8"))
    test = preprocess_df(pd.read_csv('data/test.csv', sep=";", decimal=".", encoding="utf-8"))

    # Data Pre-processing
    X_train, y_train = get_X_y(train)
    X_test, y_test = get_X_y(test)

    # Prediction
    params = {'n_estimators': 300, 'max_depth': 4, 'loss': 'deviance', 'learning_rate': 0.03,
              'subsample': 0.8, 'verbose': 2}
    clf = GradientBoostingClassifier(**params)
    clf.fit(X_train, y_train)

    xgb_pred = clf.predict_proba(X_test)
    fi = np.array([X_train.columns, clf.feature_importances_])

    # Save results with pickle
    with open('data/y_test.pkl', 'wb') as f:
        pickle.dump(np.array(y_test), f)

    with open('data/xgb_pred.pkl', 'wb') as f:
        pickle.dump(xgb_pred, f)

    with open('data/ra_pred.pkl', 'wb') as f:
        pickle.dump(X_test['RA'].values, f)

    with open('data/aa_pred.pkl', 'wb') as f:
        pickle.dump(X_test['AA'].values, f)

    with open('data/jc_pred.pkl', 'wb') as f:
        pickle.dump(X_test['JC'].values, f)

    with open('data/cn_pred.pkl', 'wb') as f:
        pickle.dump(X_test['CN'].values, f)

    with open('data/fi.pkl', 'wb') as f:
        pickle.dump(fi, f)

if __name__ == "main":
    main()
