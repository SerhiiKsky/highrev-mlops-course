"""Schema check of one serving batch against the model's training data (layer B).

``reference_domain`` is supplied. ``check_schema`` is the L08-E2 TODO.
"""

import pandas as pd

from highrev.monitoring import CATEGORICAL, DATE, FEATURES, KEY, NUMERIC

IGNORED = (DATE, KEY)


def reference_domain(reference: pd.DataFrame) -> dict:
    """Describe what the model was trained on (supplied).

    Input: the reference frame (Lab 06 ``fit.csv``). Output::

        {
            "features": [...FEATURES...],
            "numeric": ["pages_visited", "age_first_order"],
            "categorical": {
                "gender": {"values": ["F", "M"], "missing": True},
                "campaign": {"values": ["False", "True"], "missing": False},
                ...
            },
        }

    ``values`` are the sorted non-missing values as strings (``campaign`` is a bool
    column, so its values are ``"False"`` and ``"True"``); ``missing`` says whether the
    reference itself had missing values in that column.
    """
    absent = [column for column in FEATURES if column not in reference]
    if absent:
        raise ValueError(f"The reference lacks feature columns: {', '.join(absent)}")
    return {
        "features": list(FEATURES),
        "numeric": list(NUMERIC),
        "categorical": {
            column: {
                "values": sorted(reference[column].dropna().astype(str).unique().tolist()),
                "missing": bool(reference[column].isna().any()),
            }
            for column in CATEGORICAL
        },
    }


def check_schema(batch: pd.DataFrame, domain: dict, open_columns=()) -> list[str]:
    """L08-E2 TODO. Return the schema problems of one serving batch; ``[]`` means ok.

    Inputs: ``batch``, one ``serving.csv`` read with ``dtype={"row_id": str}``,
    ``domain`` from ``reference_domain`` and ``open_columns``, the categorical columns
    listed in ``monitoring.open_domain_columns`` (``ip_address_country``: new countries
    are expected, so its unseen values are reported by validate as information, not as
    a problem). Ignore the columns ``date`` and ``row_id``.
    Return one readable string per problem, each naming its column:

    1. a feature in ``domain["features"]`` that the batch lacks (missing column);
    2. a batch column that is not a feature (unexpected column);
    3. a column of ``domain["numeric"]`` whose dtype is not numeric
       (``pandas.api.types.is_numeric_dtype``);
    4. for each column of ``domain["categorical"]``: the non-missing values, compared as
       strings (``astype(str)``), that are not in ``values``; name each unseen value
       with its number of rows. Skip this unseen-value check for ``open_columns``.
       Missing values are a problem only when the reference had none (``missing`` is
       False), in every categorical column; then report how many rows are missing.

    A missing column is reported once, under 1, not again under 3 or 4. Report in this
    order: missing columns, unexpected columns, then the remaining checks column by
    column in feature order. Do not modify ``batch``. Example::

        ["missing column: browser", "os: values not in the reference: 'Unknown-42' (150 rows)"]
    """
    raise NotImplementedError("L08-E2: implement check_schema in src/highrev/monitoring/schema.py")
