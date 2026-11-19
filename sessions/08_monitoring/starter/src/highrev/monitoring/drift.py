"""Distribution drift of one serving batch against the reference (layer B, supplied).

Evidently 0.7.23 ``DataDriftPreset`` chooses the method per column. With more than
1,000 reference rows that is the normed Wasserstein distance for numeric columns and
the Jensen-Shannon distance for categorical ones; for both, a larger value means more
drift. The threshold of each column comes from ``monitoring.drift_threshold``.

Boundary (checked in the installed Evidently 0.7.23 source,
``evidently/legacy/calculations/stattests/{wasserstein_distance_norm,jensenshannon}.py``):
a column is drifted when ``score >= threshold``, so a score exactly on the threshold
counts as drift. ``drifted`` below is read from Evidently's own per-column test result
(``include_tests=True``, status ``FAIL``), not recomputed here.

Results are read from ``snapshot.dict()["metrics"]`` by ``config.type``,
``config.column``, ``config.method`` and ``config.threshold``. The snapshot has no
``metric_id`` key in those entries; filtering on it silently returns nothing.
"""

from pathlib import Path

import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset
from pandas.api.types import is_numeric_dtype

from highrev.monitoring import CATEGORICAL, FEATURES, NUMERIC

MISSING_TOKEN = "<missing>"
_VALUE_DRIFT = "evidently:metric_v2:ValueDrift"
_DRIFTED_COUNT = "evidently:metric_v2:DriftedColumnsCount"


def _dataset(frame: pd.DataFrame, numeric: list[str], categorical: list[str]) -> Dataset:
    data = frame[numeric + categorical].copy()
    for column in categorical:
        # One explicit category for missing values; bools become "True"/"False".
        data[column] = data[column].astype("string").fillna(MISSING_TOKEN).astype(str)
    definition = DataDefinition(numerical_columns=numeric, categorical_columns=categorical)
    return Dataset.from_pandas(data, data_definition=definition)


def drift_summary(
    reference: pd.DataFrame,
    batch: pd.DataFrame,
    thresholds: dict,
    html_path: Path | None = None,
) -> dict:
    """Compare ``batch`` with ``reference`` on the feature columns present in both.

    A numeric feature that is not numeric in either frame is left out (the schema check
    reports it). ``thresholds`` maps each compared column to its drift threshold. Writes
    Evidently's HTML report only when ``html_path`` is given. Returns::

        {"columns": {column: {"method", "score", "threshold", "drifted"}},
         "drifted": [drifted columns in feature order], "drift_share": float}
    """
    numeric = [
        column
        for column in NUMERIC
        if column in reference
        and column in batch
        and is_numeric_dtype(reference[column])
        and is_numeric_dtype(batch[column])
    ]
    categorical = [column for column in CATEGORICAL if column in reference and column in batch]
    compared = numeric + categorical
    absent = [column for column in compared if column not in thresholds]
    if absent:
        raise ValueError(f"No drift threshold for: {', '.join(absent)}")
    if not compared:
        return {"columns": {}, "drifted": [], "drift_share": 0.0}

    preset = DataDriftPreset(
        columns=compared,
        per_column_threshold={column: float(thresholds[column]) for column in compared},
    )
    snapshot = Report([preset], include_tests=True).run(
        current_data=_dataset(batch, numeric, categorical),
        reference_data=_dataset(reference, numeric, categorical),
    )
    result = snapshot.dict()
    columns, share = {}, None
    for metric in result["metrics"]:
        config = metric["config"]
        if config["type"] == _VALUE_DRIFT:
            columns[config["column"]] = {
                "method": config["method"],
                "score": float(metric["value"]),
                "threshold": float(config["threshold"]),
            }
        elif config["type"] == _DRIFTED_COUNT:
            share = float(metric["value"]["share"])
    verdicts = {}
    for test in result.get("tests", []):
        params = test.get("metric_config", {}).get("params", {})
        if params.get("type") == _VALUE_DRIFT:
            if test["status"] not in ("SUCCESS", "FAIL"):
                raise RuntimeError(f"Evidently drift test {params['column']}: {test['status']}")
            verdicts[params["column"]] = test["status"] == "FAIL"
    lost = [column for column in compared if column not in columns or column not in verdicts]
    if lost or share is None:
        raise RuntimeError(f"Evidently returned no drift result for: {', '.join(lost) or 'share'}")
    ordered = [column for column in FEATURES if column in columns]
    if html_path is not None:
        Path(html_path).parent.mkdir(parents=True, exist_ok=True)
        snapshot.save_html(str(html_path))
    return {
        "columns": {column: {**columns[column], "drifted": verdicts[column]} for column in ordered},
        "drifted": [column for column in ordered if verdicts[column]],
        "drift_share": share,
    }
