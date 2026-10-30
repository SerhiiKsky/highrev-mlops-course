"""Supplied experiment logic. Students connect these functions through Kedro."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = [
    "distance_km", "rain", "rush_hour", "traffic_level", "items_count",
    "typical_prep_min", "kitchen_capacity",
]
CATEGORICAL = ["zone", "cuisine"]


def prepare_features(orders: pd.DataFrame, restaurants: pd.DataFrame) -> pd.DataFrame:
    """Join the two catalog inputs; retain features and the supplied late target."""
    data = orders.merge(restaurants, on="restaurant_id", how="left", validate="many_to_one")
    required = NUMERIC + CATEGORICAL + ["late"]
    missing = set(required) - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if data[required].isna().any().any():
        raise ValueError("Missing feature or target values")
    if set(data["late"].unique()) != {0, 1}:
        raise ValueError("late must contain both binary classes")
    return data[required].copy()


def split_data(features: pd.DataFrame, settings: dict) -> dict:
    """Create a fixed stratified 60/20/20 split; reserve the test set."""
    X, y = features[NUMERIC + CATEGORICAL], features["late"].astype(int)
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=settings["test_size"],
        random_state=settings["split_seed"], stratify=y,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=settings["validation_fraction_of_remaining"],
        random_state=settings["split_seed"], stratify=y_temp,
    )
    return dict(X_train=X_train, X_val=X_val, X_test=X_test,
                y_train=y_train, y_val=y_val, y_test=y_test)


def search_candidates(split: dict, settings: dict, selection: dict) -> tuple:
    """Return the candidate table and fitted sklearn pipelines indexed by C.

    Reads only train/validation data. Search: 15 rows. Reproduce: one row.
    Kedro handles loading/saving; this function never opens raw CSV files.
    """
    if selection["mode"] == "search":
        configs = [(c, t) for c in settings["c_values"] for t in settings["thresholds"]]
    elif selection["mode"] == "reproduce":
        configs = [(selection["c"], selection["threshold"])]
    else:
        raise ValueError("selection.mode must be search or reproduce")
    if not configs or any(
        not np.isfinite(c) or c <= 0 or not np.isfinite(t) or not 0 <= t <= 1
        for c, t in configs
    ):
        raise ValueError("Use finite C > 0 and thresholds between 0 and 1")
    rows, models = [], {}
    for c in sorted({float(c) for c, _ in configs}):
        model = Pipeline([
            ("preprocess", ColumnTransformer([
                ("num", StandardScaler(), NUMERIC),
                ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ])),
            ("model", LogisticRegression(
                C=c, max_iter=settings["max_iter"], random_state=settings["split_seed"],
            )),
        ])
        model.fit(split["X_train"], split["y_train"])
        models[c] = model
        probabilities = model.predict_proba(split["X_val"])[:, 1]
        for current_c, threshold in configs:
            if current_c != c:
                continue
            predicted = (probabilities >= threshold).astype(int)
            y = split["y_val"]
            rows.append({
                "C": c, "threshold": float(threshold),
                "val_roc_auc": float(roc_auc_score(y, probabilities)),
                "val_f1": float(f1_score(y, predicted, zero_division=0)),
                "val_precision": float(precision_score(y, predicted, zero_division=0)),
                "val_recall": float(recall_score(y, predicted, zero_division=0)),
                "val_predicted_late": int(predicted.sum()),
            })
    return pd.DataFrame(rows), models


def comparison_figure(results: pd.DataFrame):
    """Supplied reporting helper, called by the tracking adapter after Kedro."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))
    dots = ax.scatter(results["val_roc_auc"], results["val_f1"],
                      c=results["threshold"], cmap="viridis", s=80)
    for row in results.to_dict("records"):
        ax.annotate(f"C={row['C']}, t={row['threshold']}",
                    (row["val_roc_auc"], row["val_f1"]), fontsize=6,
                    xytext=(3, 3), textcoords="offset points")
    ax.set(xlabel="Validation ROC AUC", ylabel="Validation F1",
           title=f"{len(results)} candidates — same data split")
    ax.grid(alpha=.2)
    fig.colorbar(dots, ax=ax, label="Decision threshold")
    fig.tight_layout()
    return fig
