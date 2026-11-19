"""Simulate a dated stream of serving batches with delayed labels (supplied; read it in L08-E1).

Every day samples ``batch_rows`` rows without replacement from the serving population
(the Lab 06 ``validation.csv``, never fitted by the monitored predictor). From
``start_day`` on, the chosen incident changes that day's batch. Each day folder holds

- ``serving.csv``: ``date,row_id,<features present>``, what the service receives;
- ``reality.csv``: ``date,row_id,high_revenue`` (0/1), the label that arrives later.

Taxonomy rows (module 6) the incidents imitate:

- ``none``: no change; use it to see the normal day-to-day noise.
- ``schema``: an upstream change drops the ``browser`` column (schema change).
- ``covariate``: the population moves toward heavy browsers; rows are resampled with
  weights ``rank_pct(pages_visited) ** 2 + 0.2`` and keep their own labels, so
  P(y | x) is unchanged (input distribution change).
- ``category``: 50% of ``ip_address_country`` set to one existing value (upstream source).
- ``new_category``: 30% of ``os`` set to a value the model never saw (schema/domain).
- ``concept``: within 50% of rows each feature is shuffled across those rows, so every
  marginal distribution is kept and the feature-label relationship breaks.
- ``corrupt``: the old ``drift_simulations`` helper's mean and std noise with the labels
  kept. It changes P(y | x), so it is not covariate shift (optional discussion). The old
  helper's ``shuffle_values`` loops over the undefined name ``shuffeled_part``,
  so calling it raises ``NameError``; the module 7 walkthrough calls it anyway.

The stream is deterministic for a seed: day ``d`` samples with ``random_state=seed + d``
and the incidents draw from one ``numpy.random.default_rng(seed)``.
"""

import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from highrev.monitoring import DATE, FEATURES, KEY, TARGET

INCIDENTS = ("none", "schema", "covariate", "category", "new_category", "concept", "corrupt")
DESCRIPTIONS = {
    "none": "no change",
    "schema": "column browser dropped",
    "covariate": "population resampled toward high pages_visited; labels follow their rows",
    "category": "50% of ip_address_country set to 'Germany'",
    "new_category": "30% of os set to the unseen value 'Unknown-42'",
    "concept": "each feature shuffled within 50% of rows; marginals kept",
    "corrupt": "noise added to pages_visited and age_first_order; labels kept",
}
CATEGORY_COLUMN, CATEGORY_VALUE, CATEGORY_SHARE = "ip_address_country", "Germany", 0.5
NEW_CATEGORY_COLUMN, NEW_CATEGORY_VALUE, NEW_CATEGORY_SHARE = "os", "Unknown-42", 0.3
CONCEPT_SHARE = 0.5
_MAX_SEED = 2**32 - 1  # pandas sampling uses numpy.random.RandomState


def covariate_weights(pool: pd.DataFrame) -> pd.Series:
    """Sampling weights of the covariate incident; a missing ``pages_visited`` weighs 0."""
    return (pool["pages_visited"].rank(pct=True) ** 2 + 0.2).fillna(0.0)


def _check(
    pool: pd.DataFrame,
    incident: str,
    days: int,
    start_day: int,
    batch_rows: int,
    seed: int,
    start_date: str,
) -> pd.DatetimeIndex:
    """Raise ValueError for anything that would fail later; nothing is written yet."""
    if incident not in INCIDENTS:
        raise ValueError(f"Unknown incident {incident!r}; choose one of: {', '.join(INCIDENTS)}")
    values = {"days": days, "start_day": start_day, "batch_rows": batch_rows, "seed": seed}
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer, got {value!r}")
    if days < 1:
        raise ValueError(f"days must be at least 1, got {days}")
    if not 1 <= start_day <= days:
        raise ValueError(f"start_day (incident_start_day) must be between 1 and {days}")
    if batch_rows < 1:
        raise ValueError(f"batch_rows must be at least 1, got {batch_rows}")
    if not 0 <= seed <= _MAX_SEED - days:
        raise ValueError(f"seed must be between 0 and {_MAX_SEED - days}, got {seed}")
    missing = [column for column in (KEY, *FEATURES, TARGET) if column not in pool]
    if missing:
        raise ValueError(f"The serving pool lacks columns: {', '.join(missing)}")
    if pool[KEY].isna().any() or pool[KEY].duplicated().any():
        raise ValueError(f"The serving pool needs a unique, non-missing {KEY}")
    labels = pool[TARGET]
    if labels.isna().any() or not set(labels.unique()) <= {0, 1}:
        raise ValueError(f"{TARGET} in the serving pool must be 0/1 or True/False")
    if batch_rows > len(pool):
        raise ValueError(
            f"batch_rows={batch_rows} exceeds the {len(pool)} rows of the serving pool; "
            "batches are sampled without replacement"
        )
    if incident == "covariate":
        usable = int((covariate_weights(pool) > 0).sum())
        if usable < batch_rows:
            raise ValueError(
                f"Weighted sampling without replacement needs at least batch_rows={batch_rows} "
                f"rows with a positive weight; the pool has {usable}"
            )
    if incident == "category" and CATEGORY_VALUE not in set(pool[CATEGORY_COLUMN].dropna()):
        raise ValueError(f"{CATEGORY_VALUE!r} must be an existing {CATEGORY_COLUMN} value")
    if incident == "new_category" and NEW_CATEGORY_VALUE in set(
        pool[NEW_CATEGORY_COLUMN].dropna().astype(str)
    ):
        raise ValueError(f"{NEW_CATEGORY_VALUE!r} must not occur in {NEW_CATEGORY_COLUMN}")
    try:
        return pd.date_range(start_date, periods=days, freq="D")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"start_date must be a date such as 2026-10-01: {exc}") from exc


def _apply(batch: pd.DataFrame, incident: str, rng: np.random.Generator) -> pd.DataFrame:
    """Change one day's batch (already sampled from the pool) according to the incident."""
    out = batch.copy()
    if incident == "none":
        return out
    if incident == "schema":
        return out.drop(columns=["browser"])
    if incident == "category":
        rows = out.sample(frac=CATEGORY_SHARE, random_state=int(rng.integers(1_000_000))).index
        out.loc[rows, CATEGORY_COLUMN] = CATEGORY_VALUE
        return out
    if incident == "new_category":
        rows = out.sample(frac=NEW_CATEGORY_SHARE, random_state=int(rng.integers(1_000_000))).index
        out.loc[rows, NEW_CATEGORY_COLUMN] = NEW_CATEGORY_VALUE
        return out
    if incident == "concept":
        rows = out.sample(frac=CONCEPT_SHARE, random_state=int(rng.integers(1_000_000))).index
        for column in FEATURES:
            shuffled = out.loc[rows, column].sample(
                frac=1, random_state=int(rng.integers(1_000_000))
            )
            out.loc[rows, column] = shuffled.to_numpy()
        return out
    if incident == "corrupt":
        pages, age = out["pages_visited"], out["age_first_order"]
        out["pages_visited"] = pages + rng.normal(0.4 * pages.mean(), 0.04, len(out))
        out["age_first_order"] = age + rng.normal(0.0, 0.5 * age.std(), len(out))
        return out
    raise ValueError(f"Unknown incident {incident!r}")  # covariate is sampled, not applied


def generate(
    pool: pd.DataFrame,
    out_root: Path,
    incident: str,
    *,
    days: int,
    start_day: int,
    batch_rows: int,
    seed: int,
    start_date: str = "2026-10-01",
) -> Path:
    """Write ``out_root/<incident>/<YYYY-MM-DD>/{serving,reality}.csv`` and return the folder.

    Refuses an existing ``out_root/<incident>``. Validates every argument and builds every
    batch before writing, writes into a temporary sibling folder and renames it, so a
    failure never leaves a partial stream.
    """
    target = Path(out_root) / incident
    dates = _check(pool, incident, days, start_day, batch_rows, seed, start_date)
    if target.exists():
        raise FileExistsError(
            f"{target.as_posix()} already exists. Inspect it before you remove anything. "
            f"To keep it, choose a new name: --out {Path(out_root).as_posix()}/<new-name> "
            f"writes <new-name>/{incident}."
        )
    pool = pool.reset_index(drop=True).copy()
    pool[TARGET] = pool[TARGET].astype("int64")  # Lab 06 CSVs encode it as True/False
    rng = np.random.default_rng(seed)
    batches = {}
    for day, date in enumerate(dates, start=1):
        if day >= start_day and incident == "covariate":
            batch = pool.sample(
                n=batch_rows, weights=covariate_weights(pool), random_state=seed + day
            )
            batch = batch.reset_index(drop=True)
        else:
            batch = pool.sample(n=batch_rows, random_state=seed + day).reset_index(drop=True)
            if day >= start_day:
                batch = _apply(batch, incident, rng)
        batch.insert(0, DATE, date.date().isoformat())
        batches[date.date().isoformat()] = batch

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{incident}-", suffix=".tmp", dir=target.parent))
    try:
        for date, batch in batches.items():
            folder = staging / date
            folder.mkdir()
            features = [column for column in FEATURES if column in batch]
            batch[[DATE, KEY, *features]].to_csv(
                folder / "serving.csv", index=False, lineterminator="\n"
            )
            batch[[DATE, KEY, TARGET]].to_csv(
                folder / "reality.csv", index=False, lineterminator="\n"
            )
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return target
