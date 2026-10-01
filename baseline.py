"""HighRev baseline: predict which T-shirt shop customers become high-revenue.

This is the project as the course receives it: one script, exported from a notebook, that
reads two CSV files, builds features, trains a logistic regression, prints a score, and
saves a pickle. It works. It is also the starting point for every incident in the course.

Run it once, then read the "COURSE NOTE" comments. Each one names the session that turns
that line into something a team can live with.

    pip install pandas scikit-learn user-agents   # COURSE NOTE (session 2): which versions?
    python baseline.py
"""

import pickle
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler, OneHotEncoder
from user_agents import parse as parse_user_agent

# COURSE NOTE (session 4): paths, thresholds, and model settings live in the code. Kedro
# moves them to a catalog and a parameters file so a run can be described without reading
# Python.
CUSTOMERS_PATH = "data/01_raw/customers.csv"
ORDERS_PATH = "data/01_raw/orders.csv"
MODEL_PATH = "model.pickle"
HIGH_REVENUE_THRESHOLD = 300
MAX_AGE = 100
TEST_SIZE = 0.2
RANDOM_STATE = 42

# COURSE NOTE (session 5): the CSVs are committed to Git today because there is nowhere else
# to put them. DVC gives data its own version history and keeps Git small.
customers = pd.read_csv(CUSTOMERS_PATH, dtype={"customerID": str})
orders = pd.read_csv(ORDERS_PATH, dtype={"customer_id": str})

# ---------------------------------------------------------------- orders -> per customer
# COURSE NOTE (session 3): the cleaning rules below are correct and untested. A refactor that
# changes "/ 365" to "// 365" raises no error and silently moves the AUC. Session 3 turns
# these blocks into functions with unit tests.
orders["tshirt_category"] = orders["tshirt_category"].replace(
    {
        "Bl Tshirt F": "Black T-Shirt F",
        "Bl Tshirt M": "Black T-Shirt M",
        "Wh Tshirt M": "White T-Shirt M",
        "Wh Tshirt F": "White T-Shirt F",
    }
)
orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["total"] = orders["tshirt_quantity"] * orders["tshirt_price"]
orders_by_customer = orders.groupby("customer_id").agg(
    {"order_date": "min", "total": "sum", "pages_visited": "mean", "order_id": "count"}
)

# ---------------------------------------------------------------- customers + features
df = pd.merge(customers, orders_by_customer, left_on="customerID", right_index=True, how="inner")

# Three birthdates fall on February 29 of a non-leap year. Nobody remembers why.
df["birthdate"] = pd.to_datetime(
    df["birthdate"].replace({"1993/2/29": "1993/2/28", "1947/2/29": "1947/2/28", "1965/2/29": "1965/2/28"})
)
df["age_first_order"] = (df["order_date"] - df["birthdate"]).dt.days / 365
df = df[df["age_first_order"] < MAX_AGE].copy()

parsed = df["user_agent"].map(parse_user_agent)
df["browser"] = parsed.map(lambda ua: ua.browser.family)
df["os"] = parsed.map(lambda ua: ua.os.family)

# Target: did the customer spend more than the threshold in total?
df["high_revenue"] = np.where(df["total"] > HIGH_REVENUE_THRESHOLD, True, False)

NUMERIC = ["pages_visited", "age_first_order"]
CATEGORICAL = ["gender", "campaign", "ip_address_country", "browser", "os"]
TARGET = "high_revenue"

# ---------------------------------------------------------------- train / test
train, test = train_test_split(
    df[NUMERIC + CATEGORICAL + [TARGET]],
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=df[TARGET],
)


def _as_str(frame: pd.DataFrame) -> pd.DataFrame:
    """Categoricals arrive as bool, int, or str depending on the source; normalize to str."""
    return frame.astype("string").fillna("missing").astype(object)


# The model owns its preprocessing. This is the one design decision in the file worth
# keeping as is: the serving code (session 8) will send raw fields and never re-implement
# feature logic.
model = Pipeline(
    [
        (
            "preprocess",
            ColumnTransformer(
                [
                    (
                        "num",
                        Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", MinMaxScaler())]),
                        NUMERIC,
                    ),
                    (
                        "cat",
                        Pipeline(
                            [
                                ("as_str", FunctionTransformer(_as_str, feature_names_out="one-to-one")),
                                ("onehot", OneHotEncoder(handle_unknown="ignore")),
                            ]
                        ),
                        CATEGORICAL,
                    ),
                ]
            ),
        ),
        # About 9% of customers are high-revenue. Without class weighting the model says "no"
        # to everyone, scores 91% accuracy, and is useless.
        ("classifier", LogisticRegression(C=1.0, max_iter=500, class_weight="balanced")),
    ]
)
model.fit(train[NUMERIC + CATEGORICAL], train[TARGET].astype(int))

# ---------------------------------------------------------------- evaluate
proba = model.predict_proba(test[NUMERIC + CATEGORICAL])[:, 1]
pred = (proba >= 0.5).astype(int)
y = test[TARGET].astype(int)

# COURSE NOTE (session 6): these numbers are printed and lost. Run them twice with different
# settings and nobody can say which model is better, or which one is in production. MLflow
# records the run, the parameters, the metrics, and the artifact, and names a champion.
print(f"{datetime.now():%Y-%m-%d %H:%M}  n_test={len(y)}")
print(f"ROC AUC  {roc_auc_score(y, proba):.3f}")
print(f"accuracy {accuracy_score(y, pred):.3f}")
print(f"f1       {f1_score(y, pred):.3f}")

# COURSE NOTE (sessions 8 to 12): a pickle on a laptop is not a product. Serving (8), a
# container (9), CI/CD (10), monitoring (11), and a cluster (12) are what turn it into one.
with open(MODEL_PATH, "wb") as fh:
    pickle.dump(model, fh)
print(f"saved {MODEL_PATH}")
