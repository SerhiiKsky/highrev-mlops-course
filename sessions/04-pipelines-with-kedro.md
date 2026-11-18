# Session 4 — Pipelines with Kedro

**Week 4 · Individual practical work**

> “Nobody knows which cells run in which order.”

The notebook runs for its author because intermediate objects already exist in memory.
A colleague starts a fresh process and cannot reconstruct the same execution. Your
Session 3 functions already describe the transformations; this session makes their
dependencies, inputs, parameters, and saved outputs explicit with Kedro.

By the end, you can build and inspect a dependency graph, connect existing Python
functions as nodes, move model options into YAML, distinguish memory from persisted
datasets, gate training behind raw-input validation, run a named pipeline in a new
process, reuse modeling through namespaces, apply a configuration environment, and
test the assembled CLI workflow. You will also add and test your own reporting node,
and explain what a reproducible run still needs beyond the graph.

Work independently in your **individual exercise repository**, continuing your own
Session 3 implementation. Keep the course checkout separate; it supplies only the
named starter files below. The final team project has a separate repository and
collaboration workflow. Exercises, checklist notes, and this self-check are ungraded.

If class time is short, the instructor may demonstrate Ex 6 and Ex 7 while you
complete the essential validation (Ex 4) and integration tests (Ex 8). In that case,
implement Ex 6 and Ex 7 yourself in the next supervised practical period and record
in your checklist which parts you implemented and which you only observed.

## Before class

Required starting state:

- Your importable `highrev.data_processing` and `highrev.modeling` modules implement
  the Session 3 contracts; `uv run --locked python -m highrev` runs successfully.
- The age, aggregation, target boundary, and modeling tests pass, including
  `tests/unit/test_modeling.py`. Keep your documented negative-quantity policy,
  your existing runner, your Session 3 integration tests, and your CI workflow.
- `data/01_raw/customers.csv` and `data/01_raw/orders.csv` are tracked in your
  exercise project. They stay tracked in Git until Session 5 introduces DVC.
- `pyproject.toml`, `uv.lock`, and your Python 3.12 declaration are present.
  Complete the dependency installation in Ex 2 before class where possible;
  internet access is needed for uncached packages. The teacher rehearsal uses an
  existing reference interpreter; it does not establish that a fresh uv environment
  has been rebuilt successfully on your machine.
- Update the separate course checkout to obtain [the supplied assets](04_kedro/README.md).

### Terminal setup

Commands below are written for **Bash** (Git Bash on Windows, or a macOS/Linux
terminal) and run from your **exercise project root** unless a step says otherwise.
Never run exercise commands in the course checkout. Replace the two placeholder
paths with your own locations. In Git Bash, a Windows path such as
`D:\work\highrev-exercise` is written `/d/work/highrev-exercise`.

```bash
cd "/path/to/your/highrev-exercise"           # your exercise project root
EXERCISE_ROOT="$(pwd)"
COURSE_ROOT="/path/to/highrev-mlops-course"   # your separate course checkout
S04="$COURSE_ROOT/sessions/04_kedro"
git -C "$COURSE_ROOT" pull --ff-only
test -f "$S04/README.md" && echo "course assets found"
```

The helper below copies one supplied file into your exercise project. It never
overwrites: if the destination already exists, it prints a diff so you can merge
by hand. Define it in every terminal you use for this session:

```bash
copy_asset() {
  # Usage: copy_asset <source under sessions/04_kedro> <destination in this project>
  if [ "$(pwd)" != "$EXERCISE_ROOT" ]; then
    echo "run copy_asset from $EXERCISE_ROOT" >&2
    return 1
  fi
  if [ ! -f "$S04/$1" ]; then
    echo "missing course asset: $S04/$1" >&2
    return 1
  fi
  if [ -e "$2" ]; then
    echo "exists, compare and merge by hand: $2"
    diff -u "$2" "$S04/$1"
    return 0
  fi
  mkdir -p "$(dirname "$2")" && cp "$S04/$1" "$2" && echo "copied: $2"
}
```

**Reopened terminal:** `cd` to your exercise root, then rerun both blocks above
(skip the `git pull` line if you already updated). Shell variables and functions do
not survive closing the terminal.

Record your starting commit and local changes, then check readiness:

```bash
git status --short
git rev-parse HEAD
uv sync --locked
uv run --locked pytest tests/unit -q
uv run --locked python -m highrev
```

If readiness fails, finish the relevant Session 3 checkpoint first. Ask the instructor
for help identifying the missing contract; replacing your functions with a completed
teacher solution would hide the problem.

## Concepts needed for the work

A **node** wraps an ordinary Python function and names its inputs and outputs. A
**pipeline** connects nodes through those names. Kedro uses the dependencies to choose
an allowed execution order: the order in which nodes appear in a Python list does not
define their order of execution. Independent nodes can run in either order.

A **directed acyclic graph (DAG)** makes each dependency explicit and forbids cycles.
A dataset name is an edge between producers and consumers, not necessarily a filename.
The **Data Catalog** maps selected names to storage and loading/saving behavior.
An uncatalogued intermediate normally uses a `MemoryDataset` for that run and
disappears when the process exits. A catalogued Parquet, pickle, or JSON output
can be loaded by a later process.

**Parameters** provide configuration as node inputs. For example, this unrelated node
passes a dataset and a configured limit to an ordinary two-argument function:

```python
from kedro.pipeline import node

node(
    func=filter_measurements,
    inputs=["measurements", "params:minimum_reading"],
    outputs="accepted_measurements",
    name="filter_measurements_node",
)
```

Input lists follow function argument order; an input dictionary can map function
argument names to dataset names. A list of output names unpacks a tuple returned by a
function. The **pipeline registry** gives pipelines CLI names; `__default__` is used
by `kedro run` without a pipeline selector.

| Concept | Meaning in this project |
|---|---|
| Namespace | A prefix applied to a reusable pipeline instance's nodes and outputs; selected inputs and parameters can be remapped so two instances share data but not outputs |
| Configuration environment | The `conf/base/` files plus one selected override directory, such as `conf/local/` (the default run environment) or `conf/development/` |
| Merge strategy | How an environment override combines with base values: replace the whole top-level entry, or merge nested keys ("soft") |
| Integration test | Runs real components together, here a fresh Kedro CLI process, and checks observable behavior |

Kedro's pipeline is different from the scikit-learn `Pipeline` returned by your model
builder. Kedro connects data preparation, fitting, and evaluation and handles catalog
I/O; the scikit-learn object keeps feature preprocessing with the fitted estimator.
Airflow, Prefect, and Dagster are broader workflow platforms with overlapping
capabilities; they can add scheduling and operational management. A local Kedro
command does not create a scheduled service. A small stable script can be sufficient
for a one-off task; a framework adds conventions and setup work that pay off when
several stages, configurations, and people share the workflow.

Kedro does not automatically know that a saved dataset is current. A successful
partial run can consume an older file. Reproducibility still depends on the data,
code, environment, parameters, and deterministic behavior of your functions.

## Lesson route

| Block | Participation |
|---|---|
| Ex 1 — Explain and sketch the workflow | Individual |
| Opening demonstration: functions, nodes, catalog, registry | Instructor |
| Ex 2 — Bootstrap Kedro and the catalog | Individual |
| Ex 3 — Wire functions and model options | Individual |
| Break | Everyone |
| Ex 4 — Validate inputs and report class balance | Instructor demonstration, then individual |
| Ex 5 — Select and debug a pipeline | Individual |
| Ex 6 — Reuse modeling with namespaces | Instructor trace, then individual |
| Break | Everyone |
| Ex 7 — Apply environment overrides | Instructor demonstration, then individual |
| Ex 8 — Test the assembled pipeline | Individual, required |
| Wrap-up and Session 5 handoff | Everyone |

## Ex 1 — Explain and sketch the workflow

**Purpose:** identify what must exist before each operation can run, and what Kedro
will and will not do for you. **Start:** your working Session 3 modules and a
successful readiness run.

1. Copy the checklist into your exercise project, then fill in your starting commit,
   data identity, and baseline metrics from the readiness run.

   | Supplied asset | Destination |
   |---|---|
   | [pipeline-checklist.md](04_kedro/pipeline-checklist.md) | `notes/session-04.md` |

   ```bash
   copy_asset pipeline-checklist.md notes/session-04.md
   sha256sum data/01_raw/customers.csv data/01_raw/orders.csv
   ```

   On macOS, use `shasum -a 256` in place of `sha256sum`.

2. Sketch the graph from raw `orders` and `customers` through aggregation, customer
   features, labeling, split, fit, and evaluation, ending in saved artifacts. Include
   parameters as inputs and the direct `test_set` edge from splitting to evaluation.
3. Mark which objects exist only in the current Python process. Choose an intermediate
   that would let training restart without repeating raw data preparation.
4. Add a proposed raw-validation gate. Explain which downstream edges must consume
   its outputs so that a failure actually prevents training.
5. Predict whether fitting can start before the split, and whether evaluating can
   start before fitting. Explain each answer using an input dependency. State what
   Kedro does here and what an external scheduler would add.

**Check and keep:** your own sketch and reasoning in the checklist. You can trace
every input needed by evaluation and explain why placing validation first in a
Python list is insufficient. There is no code to change yet. During the opening
demonstration, compare your sketch with the displayed graph and revise any missing
dependency; keep the sketch for comparison with Kedro-Viz in Ex 5.

**If stuck:** start from `evaluate_model` and work backwards, asking "which function
produces this argument?" until you reach a raw CSV or a parameter.

## Ex 2 — Bootstrap Kedro and the catalog

**Purpose:** give Kedro a project, configuration, and storage boundary.
**Start:** Ex 1 and a working Session 3 package.

1. Copy only the Ex 2 files from the [asset inventory](04_kedro/README.md). Leave
   the Ex 4 and Ex 8 files and the optional parity scaffold in the course checkout
   until their exercise starts: unfinished test skeletons would break your passing
   suite. Keep your Session 3 `data_processing.py`, `modeling.py`, `runner.py`, and
   `__main__.py`; the pipeline package lives alongside them.

   | Supplied asset | Destination | Purpose |
   |---|---|---|
   | [settings.py](04_kedro/starter/src/highrev/settings.py) | `src/highrev/settings.py` | Explicit `base`/`local` environments and soft merging of nested parameters |
   | [pipeline_registry.py](04_kedro/starter/src/highrev/pipeline_registry.py) | `src/highrev/pipeline_registry.py` | Registry stub for Ex 3; `comparison` is added in Ex 6 |
   | [pipelines/\_\_init\_\_.py](04_kedro/starter/src/highrev/pipelines/__init__.py) | `src/highrev/pipelines/__init__.py` | Pipeline package marker |
   | [data_processing/\_\_init\_\_.py](04_kedro/starter/src/highrev/pipelines/data_processing/__init__.py) | `src/highrev/pipelines/data_processing/__init__.py` | Package marker |
   | [data_processing/pipeline.py](04_kedro/starter/src/highrev/pipelines/data_processing/pipeline.py) | `src/highrev/pipelines/data_processing/pipeline.py` | Stub: Ex 3 wiring, Ex 4 validation and reporting |
   | [modeling/\_\_init\_\_.py](04_kedro/starter/src/highrev/pipelines/modeling/__init__.py) | `src/highrev/pipelines/modeling/__init__.py` | Package marker |
   | [modeling/pipeline.py](04_kedro/starter/src/highrev/pipelines/modeling/pipeline.py) | `src/highrev/pipelines/modeling/pipeline.py` | Stub: Ex 3 wiring, Ex 6 shared split and template |
   | [catalog.yml](04_kedro/starter/conf/base/catalog.yml) | `conf/base/catalog.yml` | Raw inputs and persisted outputs |
   | [parameters.yml](04_kedro/starter/conf/base/parameters.yml) | `conf/base/parameters.yml` | Preparation/split defaults, `model_options`, `models.low_c`, `models.high_c` |

   ```bash
   copy_asset starter/src/highrev/settings.py src/highrev/settings.py
   copy_asset starter/src/highrev/pipeline_registry.py src/highrev/pipeline_registry.py
   copy_asset starter/src/highrev/pipelines/__init__.py src/highrev/pipelines/__init__.py
   copy_asset starter/src/highrev/pipelines/data_processing/__init__.py src/highrev/pipelines/data_processing/__init__.py
   copy_asset starter/src/highrev/pipelines/data_processing/pipeline.py src/highrev/pipelines/data_processing/pipeline.py
   copy_asset starter/src/highrev/pipelines/modeling/__init__.py src/highrev/pipelines/modeling/__init__.py
   copy_asset starter/src/highrev/pipelines/modeling/pipeline.py src/highrev/pipelines/modeling/pipeline.py
   copy_asset starter/conf/base/catalog.yml conf/base/catalog.yml
   copy_asset starter/conf/base/parameters.yml conf/base/parameters.yml
   ```

2. Merge [config-snippets.toml](04_kedro/config-snippets.toml) into your existing
   `pyproject.toml` by hand; never replace the file or duplicate a TOML table.
   Preserve your build backend, `src/` package discovery, Python requirement,
   dependencies, Ruff, and pytest settings. Check that exactly one table exists:

   ```bash
   grep -c '^\[tool\.kedro\]' pyproject.toml
   ```

   The expected output is `1`.
3. Install the pinned dependencies, which updates `pyproject.toml` and `uv.lock`:

   ```bash
   uv add "kedro==1.7.0" "kedro-datasets[pandas-csvdataset,pandas-parquetdataset,pickle-pickledataset,json-jsondataset]==9.6.0"
   uv sync --locked
   uv run --locked kedro --version
   git diff --stat -- pyproject.toml uv.lock
   uv run --locked python -m highrev
   ```

   Review the lockfile diff. If shared dependencies such as pandas or scikit-learn
   changed, record the modular runner's result under this new lock before
   attributing any later metric difference to Kedro wiring.
4. Create the local configuration directory with a marker file. Kedro refuses to run
   when the default `conf/local/` directory is missing, and Git does not track empty
   directories, so a clean clone needs the marker:

   ```bash
   mkdir -p conf/local
   touch conf/local/.gitkeep
   ```

   Add these rules to `.gitignore` unless equivalent rules already exist; preserve
   your existing ignores and do not ignore `data/01_raw/`:

   ```text
   data/02_intermediate/
   data/03_primary/
   data/06_models/
   data/08_reporting/
   conf/local/*
   !conf/local/.gitkeep
   ```

   Then verify what Git will ignore. Paths need not exist yet:

   ```bash
   git check-ignore -v data/03_primary/customers_labeled.parquet data/06_models/classifier.pickle data/08_reporting/metrics.json conf/local/credentials.yml
   git check-ignore -q data/01_raw/orders.csv && echo "WARNING: raw orders are ignored" || echo "raw orders still tracked (expected)"
   git check-ignore -q conf/local/.gitkeep && echo "WARNING: marker is ignored" || echo "conf/local/.gitkeep can be tracked (expected)"
   ```

5. Read `conf/base/catalog.yml`, `conf/base/parameters.yml`, and
   `src/highrev/settings.py`. Identify the CSV loading settings that keep customer
   identifiers as strings and explain why the aggregate index must survive a Parquet
   round trip. Note `base_env`, `default_run_env`, and the soft parameter merge; Ex 7
   explains why they are explicit.

| Name | Storage role |
|---|---|
| `customers`, `orders` | Raw CSV inputs, explicit string identifiers |
| `orders_by_customer` | Persisted Parquet aggregate, `data/02_intermediate/orders_by_customer.parquet` |
| `customers_prepared` | Intermediate in memory |
| `customers_labeled` | Persisted Parquet input for modeling, `data/03_primary/customers_labeled.parquet` |
| `train_set`, `test_set` | Split frames in memory |
| `classifier` | Fitted scikit-learn pipeline via PickleDataset, `data/06_models/classifier.pickle` |
| `metrics` | JSON evaluation report, `data/08_reporting/metrics.json` |

6. Confirm that Kedro discovers the project:

   ```bash
   uv run --locked kedro registry list
   ```

   **Expected failure:** a traceback ending in `NotImplementedError: Ex 3: register
   the two graphs and their composition`. This proves that Kedro found your project
   and imported your registry stub. If you instead see that `registry` or `run` is
   not a command, Kedro did not find the project.

**Check and keep:** Kedro prints version 1.7.0; you can explain every catalog entry,
the four scalar parameters (`max_age`, `high_revenue_threshold`, `test_size`,
`random_state`), and the `model_options` group. Your unit tests still pass. Keep the
copied files, the merged `pyproject.toml`, `uv.lock`, `.gitignore`, and
`conf/local/.gitkeep`. You commit them at the end of Ex 3.

**If stuck:** see the recovery table for project discovery, duplicate TOML tables,
and missing dataset classes. Do not edit business logic to fix a setup problem.

## Ex 3 — Wire functions and model options

**Purpose:** express the dependency graph while preserving tested behavior, and move
the estimator settings into YAML so later sessions can change them without code
edits. **Start:** Ex 2, your Session 3 functions, and the pipeline/registry stubs.

### A. Make your model options configurable

No replacement modeling implementation is supplied. **Edit your own
`src/highrev/modeling.py`:**

1. Give `build_model` and `train_model` an optional `model_options=None` argument.
   Calls without it must keep the Session 3 baseline settings `C=1.0`,
   `max_iter=500`, `class_weight="balanced"` and the same behavior. When options are
   supplied, each supplied key replaces the matching default and reaches the
   `LogisticRegression` constructor; omitted keys keep their defaults. Do not mutate
   the caller's dictionary. Keep fitted preprocessing inside the scikit-learn
   `Pipeline`, and keep `train_model` passing its options to `build_model` rather
   than holding a second hard-coded `C`.
2. In your existing `tests/unit/test_modeling.py`, add a focused test that a
   non-default `C` reaches the final estimator of the returned scikit-learn
   `Pipeline`, and that a call without options keeps the baseline settings.
3. Keep your runner unchanged and confirm its baseline still works:

   ```bash
   uv run --locked pytest tests/unit -q
   uv run --locked python -m highrev
   ```

### B. Build the six core nodes

Implement `create_pipeline()` in both pipeline modules. Import and wrap your existing
functions; move no business logic into pipeline definitions. Use exactly these node
and dataset names so later CLI selectors, tests, and Session 5 match your graph.
The argument names are the Session 3 contracts; if yours differ, map your own names.

| Pipeline | Node name | Function argument ← Kedro input | Outputs |
|---|---|---|---|
| data_processing | `prepare_orders` | `orders` ← `orders` | `orders_by_customer` |
| data_processing | `prepare_customers` | `customers` ← `customers`; `orders_by_customer` ← `orders_by_customer`; `max_age` ← `params:max_age` | `customers_prepared` |
| data_processing | `label_customers` | `customers_prepared` ← `customers_prepared`; `threshold` ← `params:high_revenue_threshold` | `customers_labeled` |
| modeling | `split_data` | `labeled` ← `customers_labeled`; `test_size` ← `params:test_size`; `random_state` ← `params:random_state` | `train_set`, `test_set` |
| modeling | `train_model` | `train` ← `train_set`; `model_options` ← `params:model_options` | `classifier` |
| modeling | `evaluate_model` | `model` ← `classifier`; `test` ← `test_set` | `metrics` |

Use an input list in argument order or an input dictionary, as shown in the concepts
section; a dictionary is clearer when argument and dataset names differ:

```python
node(
    filter_measurements,
    inputs={"frame": "measurements", "limit": "params:minimum_reading"},
    outputs="accepted_measurements",
    name="filter_measurements_node",
)
```

1. Return a Kedro `Pipeline` from each module. For the split, declare **two** output
   names so Kedro unpacks the returned tuple. In the modeling module, leave
   `create_split_pipeline()` and `create_training_pipeline()` as unused stubs until
   Ex 6; calling them now raises `NotImplementedError`.
2. Implement `register_pipelines()` with keys `data_processing`, `modeling`, and
   `__default__`. The default composes both pipelines. Keep the supplied parameter
   defaults `max_age: 100`, `high_revenue_threshold: 300`, `test_size: 0.2`,
   `random_state: 42` and the default `model_options`.
3. Execute from the project root:

   ```bash
   uv run --locked kedro registry list
   uv run --locked kedro run
   cat data/08_reporting/metrics.json
   uv run --locked python -c "import pandas as pd; print(len(pd.read_parquet('data/03_primary/customers_labeled.parquet')))"
   uv run --locked python -m highrev
   ```

4. Compare metrics and row counts with your modular runner under the same lock,
   data, and parameters. Investigate discrepancies; do not loosen assertions to
   force agreement.
5. Commit the checkpoint. Review the staged list and adjust the paths to your
   project; never stage files under `data/` other than the tracked raw CSVs:

   ```bash
   git status --short
   git add -- pyproject.toml uv.lock .gitignore conf/base conf/local/.gitkeep src/highrev tests/unit notes/session-04.md
   git diff --cached --stat
   git commit -m "Wire Session 3 functions into Kedro pipelines"
   ```

**Check and keep:** `kedro registry list` shows `__default__`, `data_processing`, and
`modeling`; the log reports `Completed 6 out of 6 tasks`; the result matches the
runner within a justified numeric tolerance; Session 3 tests and your new
model-options test pass. Generated model and data files remain ignored. Session 5
depends on this `model_options` wiring: its tracking adapter refuses to run unless
training receives `params:model_options` with `C`, `max_iter`, and `class_weight`.

**If stuck:** a `NotImplementedError` names the stub you have not replaced. A
`TypeError` about arguments usually means an input list is in the wrong order or a
dictionary key does not match the function's argument name.

**Break.**

## Ex 4 — Validate inputs and report class balance

**Purpose:** make invalid raw data unable to reach training, and extend the graph with
a useful, tested report. **Start:** the six-node pipeline works and is committed.

Copy the Ex 4 files now. They are contracts and test requirements; you implement
two pure functions that neither read nor write files.

| Supplied asset | Destination | Purpose |
|---|---|---|
| [validation.py](04_kedro/starter/src/highrev/validation.py) | `src/highrev/validation.py` | Raw-input validation contract and required column sets |
| [reporting.py](04_kedro/starter/src/highrev/reporting.py) | `src/highrev/reporting.py` | Class-balance reporting contract |
| [test_validation.py](04_kedro/starter/tests/unit/test_validation.py) | `tests/unit/test_validation.py` | Validation test requirements; you write the assertions |
| [test_reporting.py](04_kedro/starter/tests/unit/test_reporting.py) | `tests/unit/test_reporting.py` | Report test requirements; you write the assertions |

```bash
copy_asset starter/src/highrev/validation.py src/highrev/validation.py
copy_asset starter/src/highrev/reporting.py src/highrev/reporting.py
copy_asset starter/tests/unit/test_validation.py tests/unit/test_validation.py
copy_asset starter/tests/unit/test_reporting.py tests/unit/test_reporting.py
uv run --locked pytest tests/unit/test_validation.py tests/unit/test_reporting.py -q
```

**Expected at this point:** four failing tests, each with `NotImplementedError`. Do
not commit until they are replaced by your own passing assertions.

### A. Validate raw inputs before preparation

1. Implement `validate_inputs(customers, orders)` using the supplied
   `CUSTOMER_COLUMNS` and `ORDER_COLUMNS`. Reject missing columns, empty tables,
   null or blank customer identifiers, and nonnumeric or nonfinite `tshirt_quantity`
   or `tshirt_price`. Raise a `ValueError` whose message names the table and the
   field. Return the two frames in customer/order order without changing values.
2. The course data already contains repeated customer IDs: preserve them.
   Deduplication is a separate business decision. Keep the Session 3
   negative-quantity policy in `prepare_orders`; do not silently change that
   contract. Missing values in optional features can still be handled by the
   model's imputer. This is a limited schema check, not a data-quality system.
3. Add node `validate_inputs` with inputs `customers`, `orders` and outputs
   `validated_customers`, `validated_orders`. Change **both** preparation consumers:
   `prepare_orders` takes `validated_orders`; `prepare_customers` takes
   `validated_customers` and `orders_by_customer`. These edges enforce the gate.
   Leave the validated frames in memory and keep the raw catalog entries.
4. Replace the requirements in `tests/unit/test_validation.py` with your own
   assertions on small fixtures: accepted values and input preservation (including
   repeated IDs), a missing column, an invalid identifier, an empty table, and a bad
   quantity or price. Check the specific error, for example with
   `pytest.raises(ValueError, match=...)`; "some exception occurred" is insufficient.

### B. Add a reporting branch

1. Implement `report_class_balance(customers_labeled)` in `src/highrev/reporting.py`.
   Its `high_revenue` column must contain non-null boolean labels only. Return a
   JSON-compatible dictionary with `rows`, `positive`, `negative` as native Python
   integers and `positive_rate` as a native float. Reject an empty target or invalid
   labels with `ValueError`; do not silently turn strings or integers into booleans.
   Decide and document the error for a missing target column. Leave the input
   unchanged.
2. Add node `report_class_balance` to the data-processing pipeline, taking
   `customers_labeled` and producing `class_balance`. Add a `json.JSONDataset`
   catalog entry for `class_balance` with filepath
   `data/08_reporting/class_balance.json`. This node and the modeling split share an
   input; neither depends on the other's output.
3. Replace the requirements in `tests/unit/test_reporting.py` with your own
   assertions: a hand-calculated mixed example, all-positive and all-negative
   examples, empty input, null and nonboolean labels, native JSON serialization, and
   input immutability. Do not calculate expected counts by calling the function
   being tested.
4. Run the focused tests, the completed unit suite, quality checks, and the graph:

   ```bash
   uv run --locked pytest tests/unit/test_validation.py tests/unit/test_reporting.py -q
   uv run --locked pytest tests/unit -q
   uv run --locked ruff check .
   uv run --locked ruff format --check .
   uv run --locked kedro run
   cat data/08_reporting/class_balance.json
   ```

5. Commit the named source, catalog, test, and notes paths, as in Ex 3.

**Check and keep:** the default run reports `Completed 8 out of 8 tasks`; your report
agrees with the persisted labels (`rows` equals the labeled row count from Ex 3);
valid boolean cases pass and invalid inputs are rejected with specific errors. The
unit tests establish both contracts on their chosen inputs; the full run shows that
your nodes execute. Ex 8 proves that a raw schema failure blocks the assembled
training workflow. Do not edit your raw CSVs to test the gate.

**If stuck:** if training would still run after a validation failure, trace the
edges: both `prepare_orders` and `prepare_customers` must consume validated outputs.
If JSON saving fails, convert counts and rate to native Python scalars.

## Ex 5 — Select and debug a pipeline

**Purpose:** discover which inputs a selected graph needs in a fresh process, and why
a successful partial run can use stale data. **Start:** a successful eight-node
default run from Ex 4.

### A. Selected runs and missing inputs

1. Run the named modeling pipeline in a **new CLI process**:

   ```bash
   uv run --locked kedro run --pipelines=modeling
   ```

   Explain why this works: the prior full run persisted `customers_labeled`, which
   the selected pipeline can load. The log reports three nodes. Record which
   validation and preparation nodes did not run.
2. Predict this command, then run it and save the relevant error:

   ```bash
   uv run --locked kedro run --from-nodes=train_model
   echo "exit code: $?"
   ```

   **Expected failure:** a nonzero exit and `ValueError: Pipeline input(s)` naming
   `train_set` and `test_set`. They existed only in the previous process. Selecting a
   downstream node does not recreate its upstream memory datasets. Recover by
   running the whole modeling pipeline, whose `split_data` node produces those frames:

   ```bash
   uv run --locked kedro run --pipelines=modeling
   ```

3. Demonstrate a missing persisted input safely. Use a disposable copy that contains
   only your code, configuration, and raw data, so no working artifact is renamed or
   deleted. The copy uses your exercise project's environment:

   ```bash
   SCRATCH_ROOT="$(mktemp -d)"
   cp -R src conf pyproject.toml uv.lock "$SCRATCH_ROOT/"
   mkdir -p "$SCRATCH_ROOT/data/01_raw"
   cp data/01_raw/customers.csv data/01_raw/orders.csv "$SCRATCH_ROOT/data/01_raw/"
   cd "$SCRATCH_ROOT"
   uv run --locked --project "$EXERCISE_ROOT" kedro run --pipelines=modeling
   echo "exit code: $?"
   uv run --locked --project "$EXERCISE_ROOT" kedro run --pipelines=data_processing
   uv run --locked --project "$EXERCISE_ROOT" kedro run --pipelines=modeling
   cd "$EXERCISE_ROOT"
   ```

   **Expected:** the first modeling run fails with a `DatasetError` naming
   `customers_labeled`, because no labeled Parquet exists in the fresh copy. Data
   processing then creates it and modeling succeeds. Copy your own implementation,
   never the teacher solution. The copy is disposable; remove it when finished with
   `rm -rf -- "${SCRATCH_ROOT:?}"` after you have returned to `$EXERCISE_ROOT`.

   *Alternative:* in your exercise project, temporarily **rename only the generated
   `customers_labeled` Parquet file**, after confirming its path in the catalog.
   Never rename or remove raw inputs. Restore it immediately after the failure:

   ```bash
   LABELED=data/03_primary/customers_labeled.parquet
   test -f "$LABELED" && test ! -e "$LABELED.bak" && mv "$LABELED" "$LABELED.bak"
   uv run --locked kedro run --pipelines=modeling
   echo "exit code: $?"
   mv "$LABELED.bak" "$LABELED"
   uv run --locked kedro run --pipelines=modeling
   ```

   The guard refuses to rename if a backup already exists, so a repeated attempt
   cannot overwrite your only copy. If the last command fails, run `ls data/03_primary`
   and restore the `.bak` file before doing anything else.
4. Inspect the graph. If the optional visualization dependency can be installed,
   run it in a **second terminal** at your exercise root:

   ```bash
   uv add --dev "kedro-viz==12.4.0"
   uv sync --locked
   uv run --locked kedro viz run
   ```

   Compare the displayed graph with your Ex 1 sketch. Stop the server with Ctrl+C
   when finished. A drawing of the node names and dataset edges, plus your CLI logs,
   is an acceptable fallback if visualization is unavailable.

### B. Change a parameter and expose a stale artifact

5. Save the current results **before** the next run overwrites their files. The copy
   folder lies inside the ignored `data/08_reporting/` directory. Record code commit,
   data identity, parameters, Python/package versions, and lockfile state in your
   checklist, adding rows to its Ex 5 table as needed.

   ```bash
   mkdir -p data/08_reporting/s04-baseline
   cp data/08_reporting/metrics.json data/08_reporting/class_balance.json data/08_reporting/s04-baseline/
   ```

6. Predict what happens to the class counts when the revenue threshold increases.
   Then execute the **full** pipeline with a CLI override, save its results, and
   confirm the YAML default is unchanged:

   ```bash
   uv run --locked kedro run --params=high_revenue_threshold=500
   mkdir -p data/08_reporting/s04-threshold500
   cp data/08_reporting/metrics.json data/08_reporting/class_balance.json data/08_reporting/s04-threshold500/
   grep high_revenue_threshold conf/base/parameters.yml
   ```

   Record the new class counts and metrics. Explain that this changes the target
   definition and can change the stratified split. A higher score here is not a fair
   claim that the model improved on the same task. The CLI override applies to this
   invocation only and does not rewrite the saved default of 300.
7. Now run only modeling, without the override, and compare with the threshold-500
   results:

   ```bash
   uv run --locked kedro run --pipelines=modeling
   diff data/08_reporting/s04-threshold500/metrics.json data/08_reporting/metrics.json && echo "same as threshold-500 run"
   ```

   The run succeeds although the YAML says 300: modeling loaded the persisted
   `customers_labeled` that was built with threshold 500. A successful selected run
   proves that its inputs were available, not that they were rebuilt from the
   current configuration.
8. Restore the default artifact state with a full run, then launch a separate
   modeling process and compare its metrics with the restored full run and with
   your baseline:

   ```bash
   uv run --locked kedro run
   mkdir -p data/08_reporting/s04-restored
   cp data/08_reporting/metrics.json data/08_reporting/class_balance.json data/08_reporting/s04-restored/
   uv run --locked kedro run --pipelines=modeling
   diff data/08_reporting/s04-restored/metrics.json data/08_reporting/metrics.json && echo "fresh modeling process matches restored run"
   diff data/08_reporting/s04-baseline/class_balance.json data/08_reporting/class_balance.json && echo "class balance matches baseline"
   ```

   If values differ slightly rather than exactly, state the tolerance and conditions
   you used. A process restart with local files is evidence of fresh-process
   execution; it does not establish a clean-clone or second-machine reproduction.

**Check and keep:** your checklist records one successful selected run, both
intentional failures with their recovery, and baseline, threshold-500, stale-modeling,
and restored-default results with a reasoned explanation. You can explain the
difference between selecting `modeling` and starting at `train_model`, and why
modeling alone neither validates today's raw inputs nor guarantees a fresh labeled
artifact. No temporary renames remain, raw data are unchanged, and the default
threshold 300 is in effect. Commit the `kedro-viz` lock change if you installed it.

**If stuck:** a missing `train_set` after `--from-nodes` is expected; recover with
`--pipelines=modeling`. A missing labeled Parquet is expected only in the disposable
copy or while renamed; otherwise run the full default pipeline.

## Ex 6 — Reuse modeling with namespaces

**Purpose:** compare two model configurations on exactly the same rows, labels, and
split without copying code or overwriting artifacts. **Start:** a working default
graph, configurable model functions from Ex 3, and threshold 300 restored in Ex 5.

1. In `src/highrev/pipelines/modeling/pipeline.py`, implement
   `create_split_pipeline()` containing only the `split_data` node, and
   `create_training_pipeline()` as a reusable template containing only `train_model`
   and `evaluate_model`. Keep `create_pipeline()` as their ordinary composition so
   the default and selected `modeling` pipelines still work.
2. In `src/highrev/pipeline_registry.py`, instantiate the training template twice
   with namespaces `low_c` and `high_c`, using the `namespace`, `inputs`, and
   `parameters` arguments of Kedro's `Pipeline`. Expose `train_set` and `test_set`
   as shared inputs so they are not prefixed. Remap `model_options` to
   `models.low_c` and `models.high_c` respectively. Consult the
   [namespace guide](https://docs.kedro.org/en/1.7.0/build/namespaces/).
3. Register `comparison` as `data_processing` + the shared split + `low_c` +
   `high_c`. Do not put a split inside each variant. Leave outputs namespaced so the
   names do not collide. The supplied parameter groups use `C: 0.1` and `C: 10.0`;
   `max_iter` and `class_weight` match the default.
4. Add these four entries to `conf/base/catalog.yml`:

   | Dataset | Type | Filepath |
   |---|---|---|
   | `low_c.classifier` | `pickle.PickleDataset` | `data/06_models/low_c/classifier.pickle` |
   | `high_c.classifier` | `pickle.PickleDataset` | `data/06_models/high_c/classifier.pickle` |
   | `low_c.metrics` | `json.JSONDataset` | `data/08_reporting/low_c/metrics.json` |
   | `high_c.metrics` | `json.JSONDataset` | `data/08_reporting/high_c/metrics.json` |

5. Run and inspect the comparison, then confirm the ordinary pipelines still work:

   ```bash
   uv run --locked kedro registry list
   uv run --locked kedro run --pipelines=comparison
   cat data/08_reporting/low_c/metrics.json data/08_reporting/high_c/metrics.json
   for f in data/06_models/low_c/classifier.pickle data/06_models/high_c/classifier.pickle; do
     uv run --locked python -c "import pickle, sys; m = pickle.load(open(sys.argv[1], 'rb')); print(sys.argv[1], m[-1].get_params()['C'])" "$f"
   done
   uv run --locked kedro run
   ```

   Load only pickles that your own pipeline has just produced. In Kedro-Viz, select
   the `comparison` pipeline and expand both namespaces.

**Check and keep:** the comparison log reports `Completed 10 out of 10 tasks` with
`split_data` running once; the fitted variants report C 0.1 and 10.0; four distinct
model/report files exist and the default `classifier` and `metrics` paths are
untouched by the variants. Explain why the ten-node graph has one split and two
training/evaluation branches. Low C means stronger regularization, not a smaller
sample. Record scores without claiming a production winner from one held-out
comparison. Changing `high_revenue_threshold` would change the task, as Ex 5 showed,
so keep it at 300. Commit the source and catalog changes.

**If stuck:** two different test sets mean a split is inside the template; move it
out. An output collision or a missing catalog file usually means a template output
was listed in `inputs` or a catalog name lacks its namespace prefix.

**Break.**

## Ex 7 — Apply environment overrides

**Purpose:** select a different configuration without editing code, and see exactly
which values merge and which entries are replaced. **Start:** working model
configuration and the supplied `settings.py`.

These files are **not supplied**; create them yourself in your editor after
creating their directory:

```bash
mkdir -p conf/development
```

1. Create `conf/development/parameters.yml` with a `model_options` group containing
   only `C: 0.25`.
2. Create `conf/development/catalog.yml`. Override `classifier` and `metrics` with
   complete entries: keep their dataset types and change their paths to
   `data/06_models/development/classifier.pickle` and
   `data/08_reporting/development/metrics.json`.
3. Read `src/highrev/settings.py`. The explicit `"parameters": "soft"` merge keeps
   `max_iter` and `class_weight` from base while replacing only `C`. Without it, a
   nested override can replace the whole `model_options` group. Catalog merging keeps
   replacement behavior, so each overridden entry repeats both `type` and `filepath`.
   `--env=development` loads base + development; it does not also layer `local`.
4. Run both environments and inspect each saved estimator:

   ```bash
   uv run --locked kedro run --env=development
   uv run --locked kedro run
   for f in data/06_models/development/classifier.pickle data/06_models/classifier.pickle; do
     uv run --locked python -c "import pickle, sys; p = pickle.load(open(sys.argv[1], 'rb'))[-1].get_params(); print(sys.argv[1], p['C'], p['max_iter'], p['class_weight'])" "$f"
   done
   ls data/06_models/development data/08_reporting/development
   ```

5. Record which paths changed. The labeled data and the class report still use base
   paths because their preparation settings were unchanged. Compare this with the
   Ex 5 `--params` override, which applied to one invocation without any file.

**Check and keep:** base + development yields `C=0.25`, `max_iter=500`,
`class_weight=balanced` in `data/06_models/development/classifier.pickle`; the
ordinary run yields `C=1.0` at `data/06_models/classifier.pickle`. This exercise
does not establish safe concurrent execution or complete environment isolation.
Commit the two nonsecret development files; keep credentials in ignored
`conf/local/`, never in committed configuration. Finish with the ordinary
`kedro run` above so the default artifacts are current.

**If stuck:** if `max_iter` or `class_weight` disappears under development, check the
merge strategy in `settings.py`. A `DatasetError` about a missing `type` means a
catalog override repeated only `filepath`.

## Ex 8 — Test the assembled pipeline

**Purpose:** prove automatically, in a fresh process and a fresh directory, that the
full graph produces consistent artifacts and that invalid raw data cannot reach
training. **Start:** the validated default graph from Ex 4 passes its unit tests.
This exercise is required.

Copy the integration scaffold **now**, not earlier: its unfinished tests fail by
design.

| Supplied asset | Destination | Purpose |
|---|---|---|
| [test_kedro_pipeline.py](04_kedro/starter/tests/integration/test_kedro_pipeline.py) | `tests/integration/test_kedro_pipeline.py` | Required tests: isolated-project fixture and CLI helper supplied; assertions are your work |

```bash
copy_asset starter/tests/integration/test_kedro_pipeline.py tests/integration/test_kedro_pipeline.py
uv run --locked pytest tests/integration/test_kedro_pipeline.py -q
```

**Expected at this point:** two failing tests with `NotImplementedError`. The
`isolated_project` fixture copies your `src`, `conf`, `pyproject.toml`, and both raw
CSVs into a temporary project; `invoke_kedro` runs `kedro run` there in a new
process and returns its exit code and output. Keep all outputs in that temporary
project.

1. Implement `test_full_pipeline_writes_consistent_artifacts`: require exit code
   zero, a saved classifier, the metric names your `evaluate_model` returns with
   values in their valid ranges, and report counts that match the saved labeled
   table. Include the command's stdout/stderr in assertion messages so setup
   problems are visible.
2. Implement `test_invalid_schema_stops_before_training`: remove `tshirt_price` only
   from the temporary orders CSV and run the full CLI. Require a nonzero exit and
   your specific validation error naming `orders` and `tshirt_price`. Prove that no
   training node executed (Kedro logs a `Running node:` line for each node it
   starts) and that no model or metrics appeared. The fresh directory prevents stale artifacts
   from making this test falsely pass. Without your gate, preparation would probably
   fail too, but with a different error; that is why the assertion requires your
   validation message.
3. Run each test, the full suites, and quality checks:

   ```bash
   uv run --locked pytest tests/integration/test_kedro_pipeline.py::test_full_pipeline_writes_consistent_artifacts -q
   uv run --locked pytest tests/integration/test_kedro_pipeline.py::test_invalid_schema_stops_before_training -q
   uv run --locked pytest tests/unit tests/integration -q
   uv run --locked ruff check .
   uv run --locked ruff format --check .
   uv run --locked kedro run
   git status --short
   ```

Do not replace assertions with skips or accept an unrelated import error as the
expected validation failure. Preserve your Session 3 integration tests and CI
workflow. Commit the test file only after both tests pass; a committed placeholder
would fail your existing CI.

**Check and keep:** two meaningful CLI integration tests pass, all earlier tests
still pass, and your original raw CSVs and working artifacts are unchanged
(`git status --short` shows no raw-data change). This proves that invalid data cannot
reach training in the full graph. It does not prove future model quality, or
freshness when someone deliberately selects a downstream pipeline that omits
validation, as in Ex 5.

**If stuck:** a timeout or import error inside the test is a setup failure; print
the captured output. If the fixture cannot find `data/01_raw`, run pytest from the
exercise root.

### Optional extension — automate parity evidence, or finish it later

The Ex 8 tests and the manual fresh-process checks in Ex 5 are the essential class
checkpoint. The teacher's completed rehearsal provides a reference proof of full
direct-function parity; writing that entire automated proof is additional student
work.

When time permits, copy the optional
[parity scaffold](04_kedro/extensions/test_kedro_parity.py) from the course
checkout to `tests/integration/test_kedro_parity.py` in your exercise project. It is
a separate file from the required Ex 8 `test_kedro_pipeline.py`, so the required
tests stay untouched. Create the parent directory if needed; compare and merge if
the destination already exists. Implement the copied requirements before running
the full suite or committing the new test file: unfinished placeholders would fail
the existing Session 3 CI.

```bash
copy_asset extensions/test_kedro_parity.py tests/integration/test_kedro_parity.py
```

1. Copy configuration and raw CSVs into a temporary project and use your importable
   package in fresh Kedro CLI processes. Keep every generated artifact inside that
   temporary project. Prove that modeling fails specifically for a missing
   `customers_labeled` input, then succeeds after preparation. Check exit codes
   and the relevant error so an import/setup failure cannot satisfy the test.
2. Check registry names and graph connections. Run the default pipeline and compare
   its saved labeled frame, predictions, and metrics with direct calls of your
   Session 3 functions using identical inputs and parameters. Rounded scores alone
   are insufficient. Verify report counts against the labeled frame, metric
   names/ranges, and a loadable fitted classifier. Use actual functions rather
   than mocked node outputs.

Select an integration test only after you have authored its assertions:

```bash
uv run --locked pytest tests/integration/test_kedro_parity.py::test_modeling_requires_persisted_input -q
uv run --locked pytest tests/integration/test_kedro_parity.py::test_kedro_matches_direct_functions -q
```

Run the complete integration suite once all copied placeholders are implemented.
Record an unfinished extension as pending; it does not block the core Session 4
checkpoint or erase the manual observations you collected.

## Expected results

Sample log lines come from the teacher rehearsal with Kedro 1.7.0; wording can vary
slightly between versions. Metric values depend on your data and implementation and
are never compared with a rehearsal number.

| Exercise | Expected result |
|---|---|
| Ex 1 | A sketch tracing every evaluation input to raw CSVs or parameters, with memory/persisted boundaries and a validation gate whose outputs feed preparation |
| Ex 2 | `kedro --version` reports 1.7.0; `kedro registry list` fails with the Ex 3 `NotImplementedError`; generated paths ignored, raw CSVs and `conf/local/.gitkeep` trackable |
| Ex 3 | Registry lists `__default__`, `data_processing`, `modeling`; `Completed 6 out of 6 tasks`; metrics agree with `python -m highrev`; model-options test passes |
| Ex 4 | Four stub tests fail on copy, then pass with your assertions; `Completed 8 out of 8 tasks`; `class_balance.json` rows equal the labeled row count |
| Ex 5 | Modeling runs three nodes; `--from-nodes=train_model` fails on `train_set`/`test_set`; modeling in a fresh copy fails on `customers_labeled` and recovers; threshold 500 changes class counts; modeling without the override reproduces the threshold-500 metrics; restored run matches baseline |
| Ex 6 | `comparison` listed; `Completed 10 out of 10 tasks` with one `split_data`; fitted C 0.1 and 10.0; four distinct variant files |
| Ex 7 | Development estimator C 0.25, max_iter 500, class_weight balanced under `development/` paths; ordinary run C 1.0 at base paths |
| Ex 8 | Two stub failures on copy; then both integration tests, the full suite, and Ruff pass; raw CSVs unchanged |
| Optional extension | Parity and persisted-input tests pass, or the extension is recorded as pending |

## Expected observations and recovery

| Observation | Interpretation and first recovery step |
|---|---|
| Kedro cannot locate a project, or `run` is not a command | Run at the exercise root; inspect the merged `[tool.kedro]` table and package name. |
| `MissingConfigException` for `conf/local` | Recreate `conf/local/` with its `.gitkeep` marker and check that the marker is not ignored. |
| `NotImplementedError` | A student function, registry, pipeline, or test is still a requirement stub; complete the named exercise. |
| Duplicate TOML table | Merge fragment keys into the existing table rather than pasting another header. |
| Dataset class or Parquet engine missing | Install the specified kedro-datasets extras, update the lock, then sync with `--locked`. |
| Join unexpectedly loses customers | Inspect CSV identifier dtypes and aggregate index preservation; do not cast IDs to integers. |
| A specific validation `ValueError` naming a table and field | Inspect that input's schema; never edit raw CSVs to make a test pass. |
| Training still runs despite a validation failure | Check that both preparation nodes consume validated outputs. |
| Missing `train_set` after `--from-nodes` | Run `--pipelines=modeling` so the split executes in the same process. |
| Missing labeled Parquet for modeling | Restore the renamed file, or run data processing or the full pipeline from the raw inputs. |
| Success with surprising old results | A partial run can load stale artifacts; rerun the full graph with the intended parameters. |
| Report is rejected by JSON serialization | Convert counts and rate to native Python scalars in the reporting function. |
| Changed metrics after dependency installation | Compare both execution paths under the same new lock before diagnosing wiring. |
| Single-class or undersized split | Check the threshold, labels, and data; retain stratification and use enough examples per class in tests. |
| Namespace output collision or two test sets | Keep outputs namespaced with distinct filepaths; split once outside the template. |
| Missing nested parameter fields under an environment | Inspect the soft parameter merge in `settings.py`; repeat full catalog entries. |
| Old output files remain after a failure | Inspect the exit code and log; the Ex 8 fresh temporary project proves artifact creation. |
| `--pipeline` deprecation warning | Use `--pipelines=` as shown; `--pipeline` is deprecated in Kedro 1.7. |
| Visualization cannot start | Use the registry and a graph sketch; pipeline execution and the checklist remain required. |

## Wrap-up and next preparation

Restore the default state, update your exercise README, and commit:

1. Confirm that `conf/base/parameters.yml` still has `high_revenue_threshold: 300`,
   `random_state: 42`, and the default `model_options`, and that no `.bak` file or
   temporary copy remains in your project. Run `uv run --locked kedro run` once more.
2. Update your exercise README with the Kedro commands (`kedro run`,
   `kedro run --pipelines=comparison`, `kedro run --env=development`), the named
   pipelines, parameter defaults, test commands, and artifact locations. Keep
   Session 3's modular command available.
3. Review and commit named source, test, configuration, lock, README, and checklist
   paths. No remote push is required here.

   ```bash
   git diff
   git status --short
   git add -- README.md pyproject.toml uv.lock conf/base conf/development src/highrev tests notes/session-04.md
   git diff --cached --stat
   git commit -m "Complete Session 4 Kedro pipeline"
   ```

   Leave `conf/development` out of `git add` if Ex 7 is still pending, and do not
   stage an unfinished `tests/integration/test_kedro_parity.py`; check the staged
   list before committing.

Self-check (ungraded):

- [ ] I can explain every input and output in the graph and why list order is insufficient.
- [ ] My six original nodes call my existing Session 3 functions without duplicating logic.
- [ ] `build_model` and `train_model` accept `model_options`; calls without it keep Session 3 behavior, and a test proves a non-default C reaches the estimator.
- [ ] Raw validation is enforced through dataset edges; validation and reporting have meaningful unit tests.
- [ ] My catalog distinguishes persisted artifacts from intermediates in memory.
- [ ] I observed selected-run success, missing-memory and missing-persisted-input failures, and recovery.
- [ ] My notes preserve results before overwriting and distinguish a changed target from improved modeling.
- [ ] Two namespaces share one split and save distinct artifacts, or I recorded that implementation as pending after an instructor demonstration.
- [ ] I can explain the development override and its effective values, or I recorded it as pending.
- [ ] The required full-run and invalid-schema integration tests pass with my own assertions.
- [ ] Code, base and development configuration, tests, `conf/local/.gitkeep`, and lockfile are tracked; generated artifacts and credentials are ignored; raw inputs remain tracked.

**Session 5 handoff.** Session 5 assumes a runnable default Kedro pipeline in the
base environment that reads `data/01_raw/orders.csv` and `data/01_raw/customers.csv`
and saves `data/06_models/classifier.pickle` and `data/08_reporting/metrics.json`;
tested functions; a locked environment; and the default threshold restored.
**The Ex 3 `model_options` wiring is required:** the Session 5 tracking adapter
refuses to run unless `params:model_options` contains `C`, `max_iter`, and
`class_weight`, and it changes `model_options.C` to compare runs, so `train_model`
must use that value. Finish missing pipeline wiring and model options first, then
validation, reporting, and the Ex 8 tests. Ex 6 and Ex 7 are not prerequisites for
Session 5, but finish them in the next supervised period if they are pending. The
parity tests are an optional extension. Record any unfinished core checkpoint
honestly so the instructor can help you recover.

Optional ungraded individual research, kept outside the team project: explain how
you would identify the exact two raw CSV versions that produced a model after those
CSVs change. Distinguish saving a model from recording its data lineage. Session 5
introduces DVC to address this missing piece.

## Reading

- [Kedro documentation](https://docs.kedro.org/en/stable/): nodes, pipelines,
  project configuration, parameters, and pipeline selection.
- [Kedro namespaces](https://docs.kedro.org/en/1.7.0/build/namespaces/).
- [Configuration and merge behavior](https://docs.kedro.org/en/1.7.0/configure/advanced_configuration/).
- [Kedro datasets documentation](https://docs.kedro.org/projects/kedro-datasets/en/stable/):
  CSV, Parquet, pickle, and JSON dataset types and their load/save settings.
- [Kedro-Viz documentation](https://docs.kedro.org/projects/kedro-viz/en/stable/):
  optional graph inspection.
- [Kedro and Airflow](https://docs.kedro.org/en/1.7.0/deploy/supported-platforms/airflow/):
  architecture context; no deployment is required in this lesson.

Project expectations live in [PROJECT.md](../PROJECT.md); only the
[final project rubric](../FINAL_PROJECT_RUBRIC.md) defines grading and contribution evidence.
