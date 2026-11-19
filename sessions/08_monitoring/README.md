# Lab 08 student assets

Start with the [student brief](../08-drift-and-monitoring.md). Work in your own
individual exercise project, never in the course checkout or the team project.
The brief's "Before class" section has the exact copy commands. They refuse to
overwrite existing files; compare and merge instead.

| Course asset | Destination in your exercise project | Purpose | Your work |
| --- | --- | --- | --- |
| [starter/src/highrev/monitoring/](starter/src/highrev/monitoring/) | `src/highrev/monitoring/` | Monitoring package, run as `python -m highrev.monitoring simulate / validate / decide / act` in the project environment | `check_schema` (E2), three tests (E4) |
| `__init__.py`, `__main__.py` | same folder | Feature lists, `row_id` key, command line; reads the `monitoring` parameters | read |
| `simulate.py` | same folder | Ten dated serving batches from `validation.csv`, with one incident from day 6 | read (E1) |
| `schema.py` | same folder | `reference_domain` (supplied) and `check_schema` | **implement** (E2) |
| `drift.py`, `validate.py` | same folder | Evidently drift report per batch, `schema.json` and `drift.json` per day | read |
| `retrain.py` | same folder | Retraining tests and the supplied `decide` | **implement** three tests (E4); benchmark optional |
| `act.py` | same folder | Prints what retraining would involve; runs nothing | read (E5) |
| [starter/tests/unit/test_monitoring.py](starter/tests/unit/test_monitoring.py) | `tests/unit/test_monitoring.py` | Simulator, schema and boundary tests | add one test (E4) |
| [starter/lab07/lab07/score_batches.py](starter/lab07/lab07/score_batches.py) | `lab07/lab07/score_batches.py` | Scores each batch with your AutoGluon model; identity and schema-verdict helpers supplied | **implement** `score_batch` (E3) |
| [starter/lab07/tests/test_score_batches.py](starter/lab07/tests/test_score_batches.py) | `lab07/tests/test_score_batches.py` | Fake-predictor tests for `score_batch` | read |
| [lab07-provenance/verify_provenance.py](lab07-provenance/verify_provenance.py) | `lab07/lab07/verify_provenance.py` (replaces the Lab 07 file) | Release gate that checks the model against its own recorded lineage | read; the brief explains why |
| [parameters-snippet.yml](parameters-snippet.yml) | append to `conf/base/parameters.yml` | Every monitoring number: batch size, seed, per-column thresholds, open-domain columns, floor, `k` | change one drift threshold from evidence (E2) |
| [incident-table.md](incident-table.md) | `notes/session-08.md` | Predictions and results per incident; your threshold and rule | fill in |
| [checklist.md](checklist.md) | read, or append to your notes | Ungraded self-check | tick |

Ruff checks `src/highrev/monitoring` and `tests` with your Session 3 settings, so
your code must pass `ruff check` and `ruff format --check`. `lab07/` stays
excluded, as in Lab 07. Generated data is not committed: `data/05_serving/` (added
to `.gitignore` by the setup) and `data/08_reporting/` (ignored since Session 4).

## Files the commands write

| Command (project root) | Writes |
| --- | --- |
| `simulate --comparison "$run/comparison" --incident <name> [--out data/05_serving/<folder>]` | `data/05_serving/<name>/<date>/serving.csv` (`date,row_id` and features) and `reality.csv` (`date,row_id,high_revenue`) |
| `validate --comparison "$run/comparison" --stream data/05_serving/<name> [--html <date>]` | `data/08_reporting/monitoring/<name>/<date>/schema.json`, `drift.json`, optional `drift.html` |
| `(cd lab07 && uv run --locked python -m lab07.score_batches --model model --stream ../data/05_serving/<name> --reports ../data/08_reporting/monitoring/<name>)` | `data/08_reporting/monitoring/<name>/scores.csv` |
| `decide --reports data/08_reporting/monitoring/<name> [--until <date>]` | `retrain_signal.json` (or `retrain_signal_<date>.json`) |
| `act --signal <signal file>` | nothing; prints commands |

`simulate` refuses an existing stream (`--out` gives a new parent folder; reports mirror it under `data/08_reporting/monitoring/`); `validate`, scoring and `decide` rewrite
their own outputs and are safe to repeat.

## API cards

### check_schema

`check_schema(batch, domain, open_columns=()) -> list[str]` (project environment).
The docstring in `schema.py` gives the exact order and message format; the
supplied tests check them.

- `batch`: one day's `serving.csv`. Skip `date` and `row_id`. Do not modify it.
- `domain`: from the supplied `reference_domain(fit)`: `features`, `numeric`, and for
  each categorical column its known `values` (as strings) and whether the reference
  had `missing` values.
- Report, one string each and naming the column: a missing feature column; an
  unexpected extra column; a numeric column whose dtype is not numeric
  (`pandas.api.types.is_numeric_dtype`); categorical values not in `values`
  (compare `astype(str)`), with their row counts (`Series.value_counts`); missing
  values in a categorical column whose reference had none. A missing column is reported once.
- For a column in `open_columns`, unseen values are **not** problems; the supplied
  validator reports them as `unseen_open`.
- Return `[]` for a valid batch. The check reports; the caller decides.

### score_batch

`score_batch(predictor, serving, reality) -> dict` (AutoGluon environment)

- Join `serving[["row_id", *FEATURES]]` and `reality[["row_id", TARGET]]` on
  `row_id`, one to one. `DataFrame.merge(..., validate="one_to_one")` refuses
  duplicates, but an inner merge silently drops unmatched rows: compare lengths
  and raise `ValueError` naming serving, reality and matched counts.
- `predictor.predict_proba(merged[FEATURES])` returns a DataFrame with one column
  per class; the high-revenue probability is column `1`.
- `sklearn.metrics.roc_auc_score(y, probability)`; `accuracy_score(y, probability >= 0.5)`.
- Return `{"n", "roc_auc", "accuracy", "mean_probability", "positive_rate"}` as
  plain Python numbers. Reading files, identity and `scores.csv` are supplied.

### Retraining tests

Each returns `{"fired": bool, "limit": float}`, or `{"fired": False, "limit": None}`
(`NOT_EVALUATED`) when the history is too short. Higher ROC AUC is better;
`fired` is `current < limit`, strictly. The supplied `decide` quotes the limits
in the signal's `reason`.

- `hard_test(current, floor)`: the limit is the floor.
- `parametric_test(current, history, k, min_history=3)`: the limit is `k` standard
  deviations below the mean of `history`. Use the *sample* standard deviation:
  `numpy.std` takes a `ddof` argument; find which value gives the sample version.
- `iqr_test(current, history, min_history=4)`: the limit is Tukey's lower fence,
  Q1 − 1.5 × (Q3 − Q1). `numpy.quantile` returns quartiles; keep its default method.
- Optional `benchmark_test(current, history)`: the limit is the best earlier
  reading; not part of `decide`.
- With fewer readings than `min_history`, return `NOT_EVALUATED` (defined in the module).

`history` holds the earlier scored batches' ROC AUC values, oldest first, without
the current batch. Return plain `bool` and `float`, not numpy types.
