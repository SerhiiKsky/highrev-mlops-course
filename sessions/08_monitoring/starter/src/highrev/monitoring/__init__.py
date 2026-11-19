"""Lab 08 monitoring: serving stream, schema and drift checks, retraining signal.

The monitored model is the promoted AutoGluon predictor in ``lab07/model``. It was
trained on the Lab 06 ``fit.csv`` partition, so that file is the reference profile;
``validation.csv`` (never fitted) is the serving population of the simulator.
"""

# Lab 07 feature order (lab07/lab07/contracts.py). Keep both lists identical.
FEATURES = [
    "pages_visited",
    "age_first_order",
    "gender",
    "campaign",
    "ip_address_country",
    "browser",
    "os",
]
NUMERIC = ["pages_visited", "age_first_order"]
CATEGORICAL = [column for column in FEATURES if column not in NUMERIC]
TARGET = "high_revenue"
KEY = "row_id"
DATE = "date"
