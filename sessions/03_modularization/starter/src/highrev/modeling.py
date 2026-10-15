"""Exercise 2: separate modeling responsibilities without changing the baseline."""

import pandas as pd
from sklearn.pipeline import Pipeline

NUMERIC = ["pages_visited", "age_first_order"]
CATEGORICAL = ["gender", "campaign", "ip_address_country", "browser", "os"]
TARGET = "high_revenue"


def _as_str(frame: pd.DataFrame) -> pd.DataFrame:
    """Preserve baseline categorical normalization; keep this helper importable."""
    raise NotImplementedError("Ex 2: move the baseline normalization helper")


def build_model() -> Pipeline:
    """Return the unfitted baseline preprocessing and classifier pipeline."""
    raise NotImplementedError("Ex 2: extract model construction")


def split_data(
    labeled: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return train and test frames with declared features and TARGET, stratified by TARGET."""
    raise NotImplementedError("Ex 2: extract the deterministic split")


def train_model(train: pd.DataFrame) -> Pipeline:
    """Build and fit a model on train only; do not mutate train."""
    raise NotImplementedError("Ex 2: extract fitting")


def evaluate_model(model: Pipeline, test: pd.DataFrame) -> dict[str, float]:
    """Return roc_auc, accuracy, f1 using the baseline probability and decision rules."""
    raise NotImplementedError("Ex 2: extract evaluation")
