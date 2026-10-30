# Pizza Panic — connect the experiment (4 bonus points)

A delivery company wants to warn customers when an order is likely to arrive
late. Missed late deliveries and unnecessary warnings both have a cost. Which
model settings would you recommend, and can someone reproduce your evidence?

You have completed Session 05 tracking in your own HighRev exercise repository,
including `record_parameters`, `record_metrics`, and `record_model` from
`highrev-mlops-course/sessions/05_tracking`. **We provide the experiment; you
integrate it into Kedro and explain what it tells you.**

## What you receive and complete

| Supplied | You complete |
| --- | --- |
| Assigned A–E dataset: `orders.csv` and `restaurants.csv` | DVC versioning of your assigned pair |
| Feature join, split, model search, metrics and plotting functions | **K1:** connect three Kedro nodes |
| Catalog skeleton and complete parameter values | **K2:** fill catalog types/paths and wire parameter inputs |
| Integration worksheet with function contracts | **K3:** register a named `pizza_panic` pipeline |
| Adapter importing your completed Session 05 logging functions | **K4:** execute your named pipeline through its Kedro session |
| [Evidence template](EVIDENCE_TEMPLATE.md) | Fill the tables, observations, recommendation and recovery evidence |

This synthetic dataset uses the supplied `late` target, not HighRev's
`high_revenue` target. Keep the supplied experiment logic and settings. Your
implementation work is the Kedro integration; no new classifier is required.

## 1. Prepare a bonus copy

Use Bash (Git Bash on Windows, Linux or WSL). Run commands one at a time and
stop on failure. Replace these example paths and values; choose new folders:

```bash
SOURCE_PROJECT="$HOME/course/my-completed-session-05"
BONUS_PACK="$HOME/Downloads/pizza_panic_bonus"
STUDENT_ID='S001'
DATASET_ID='A'  # Assigned by your teacher.
BONUS_ROOT="$HOME/course/pizza-${STUDENT_ID}"
REMOTE_ROOT="${BONUS_ROOT}-dvc-remote"
EVIDENCE_ROOT="${BONUS_ROOT}-evidence"
git -C "$SOURCE_PROJECT" status --short
```

Your source must be clean, with the completed Session 05 code and lockfile
committed. A clone contains committed work only.

```bash
git clone --no-hardlinks "$SOURCE_PROJECT" "$BONUS_ROOT"
cd "$BONUS_ROOT"
uv sync --locked
mkdir "$EVIDENCE_ROOT"
```

Copy the starter files using [INTEGRATION_TEMPLATE.md](INTEGRATION_TEMPLATE.md).
Merge the ignore snippet; preserve your completed `track_run.py`,
`tracking_support.py`, and existing registry. If matplotlib is absent from your
declared dependencies, add it with `uv add matplotlib` and include the resulting
dependency/lockfile changes in your commit. Subsequent clones use `uv sync --locked`.

Fill your evidence report **outside the project**, in `$EVIDENCE_ROOT`.
Uncommitted reports or screenshots inside the repository fail the clean-Git gate.
Keep this first terminal open: later commands reuse its variables.

## 2. Fill the Kedro template

Complete **K1–K4** using the integration worksheet. The intended graph is:

```text
pizza_orders + pizza_restaurants
              |
       prepare_features
              |
        pizza_features + params:pizza_settings
              |
          split_data
              |
         pizza_split + params:pizza_settings + params:pizza_selection
              |
       search_candidates
              |
      pizza_results + pizza_models
```

Kedro must load the raw inputs through its catalog, pass parameters to nodes,
and save results/models. The adapter must execute this named graph. A node that
launches a standalone search script does not satisfy the integration point.

Reuse your completed Session 05 logging functions. The supplied Pizza adapter
has a new catalog check and reuses the general provenance helpers. Finish all
four TODOs before recording evidence.

Put the bonus catalog and parameters in **`conf/pizza/`**, leaving HighRev's
`conf/base/` files unchanged. Kedro overlays this environment on shared base
configuration. Select it with `--env pizza` for CLI runs; the supplied tracking
adapter already selects `pizza` for search and recovery and records it in MLflow.

## 3. Version your assigned data

The new clone contains the old DVC pointer but normally no raw CSVs. Inspect
the raw directory first. If it contains HighRev files, preserve them outside
this bonus copy before proceeding. The directory must contain **only** your
assigned Pizza `orders.csv` and `restaurants.csv` after copying.

```bash
mkdir -p data/01_raw
ls -la data/01_raw
cp "$BONUS_PACK/datasets/$DATASET_ID/orders.csv" data/01_raw/
cp "$BONUS_PACK/datasets/$DATASET_ID/restaurants.csv" data/01_raw/
uv run --locked dvc add data/01_raw
mkdir "$REMOTE_ROOT"
uv run --locked dvc remote add --local --default pizza "$REMOTE_ROOT"
uv run --locked dvc push data/01_raw.dvc
sha256sum data/01_raw/orders.csv data/01_raw/restaurants.csv
```

Commit your bonus source, catalog/parameters, registry edit, ignores,
`pyproject.toml`, `uv.lock`, and DVC metadata. Inspect staged changes first;
raw CSVs, environments, databases and generated models must not be committed.
If existing ignore rules hide the pointer, use `git add -f data/01_raw.dvc`.

```bash
git status --short
uv run --locked dvc status data/01_raw.dvc
git rev-parse HEAD
cat data/01_raw.dvc
```

Git must be clean; DVC must report unchanged data. Record the Git commit, both
CSV SHA256 hashes, and the pointer's `outs[0].md5` directory hash (ending in
`.dir`). Do not re-save the raw CSVs through Excel.

## 4. Search and fill your report

First verify your Kedro graph, then record the search:

```bash
export KEDRO_DISABLE_TELEMETRY=1
export MLFLOW_TRACKING_URI='sqlite:///mlflow.db'
export MLFLOW_REGISTRY_URI='sqlite:///mlflow.db'
uv run --locked kedro run --env pizza --pipeline pizza_panic
uv run --locked python -m highrev.pizza_run --name "${STUDENT_ID}-${DATASET_ID}-search"
```

Three `C` values × five thresholds produce **15 candidate child runs under one
parent run**. All candidates use the same stratified 60/20/20 train/validation/test
split. Only train and validation data are used; do not use the reserved test
partition to choose a candidate.

Open a second Bash terminal. Use the actual bonus path, since variables are not
shared between terminals:

```bash
cd "$HOME/course/pizza-S001"
uv run --locked mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000 --workers 1
```

Select `pizza-panic-bonus`. The parent contains `comparison/auc_vs_f1.png` and
the comparison CSV. Each child contains settings, validation metrics,
configuration/report/model artifacts, Git commit, DVC hash, and the
`kedro.pipeline` and `kedro.env=pizza` tags. Confirm all runs finished.

Fill the report's candidate table and observation. Choose one candidate using
F1 and ROC AUC, with precision and recall to explain missed late deliveries
versus false warnings. Look for a pattern where candidates share one metric
but differ on another. There is no required winning setting.

The logged sklearn model produces probabilities; your chosen **threshold is a
separate part of the decision policy**. Record both. Its default `predict()`
does not apply an arbitrary selected threshold.

## 5. Recover and repeat your selected candidate

Return to the first terminal. Keep the original remote available. The new
clone should contain neither raw CSVs nor a copied DVC cache before the pull:

```bash
RECOVERED_ROOT="${BONUS_ROOT}-recovered"
git clone --no-hardlinks "$BONUS_ROOT" "$RECOVERED_ROOT"
cd "$RECOVERED_ROOT"
uv sync --locked
ls data
uv run --locked dvc remote add --local --default pizza "$REMOTE_ROOT"
uv run --locked dvc pull data/01_raw.dvc
sha256sum data/01_raw/orders.csv data/01_raw/restaurants.csv
git status --short
uv run --locked dvc status data/01_raw.dvc
uv run --locked python -m highrev.pizza_run --name "${STUDENT_ID}-${DATASET_ID}-recovered" --reproduce --c 0.5 --threshold 0.5
```

Replace the example C/threshold with your selected values. Runtime overrides
do not require a source edit. Expect one new parent and one candidate child.
Compare the original and recovered **child** runs: commit, raw hashes, DVC hash,
selected C/threshold, split/model settings, and all validation metrics must
match (absolute tolerance `1e-8` in your locked environment). Run IDs and the
search/reproduce mode will differ.

The clone has its own MLflow database. In the second terminal, stop the first
UI with Ctrl+C, change into the recovery clone, and start the same UI command
using `--port 5001`. Keep both databases and artifacts until grading.

## Submit

- Your committed bonus repository or Git bundle and exact commit SHA.
- Your filled [evidence template](EVIDENCE_TEMPLATE.md), including candidate
  comparison, plot, recommendation and fresh-clone recovery evidence.
- A graph screenshot or execution log showing the three Kedro nodes, supported
  by the source/catalog/registry changes in your submission.

Optional portable source bundle:

```bash
git -C "$BONUS_ROOT" bundle create "$EVIDENCE_ROOT/submission.bundle" HEAD
```

Submit through the teacher's designated channel. The bundle carries code and
metadata; it does not carry your MLflow database or DVC remote.

## Grading — 4 bonus points

| Points | What earns them |
| ---: | --- |
| **1** | Correct data versioning and traceable MLflow runs |
| **1** | Completed candidate search, scatterplot, and meaningful observation |
| **1** | Evidence-based recommendation and reproducible selected run |
| **1** | Working Kedro integration: catalog inputs/outputs, parameterized nodes, registered pipeline, and execution through the tracking adapter |

You are graded on integration, evidence and reasoning, not the highest score.
