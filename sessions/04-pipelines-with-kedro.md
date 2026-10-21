# Session 4 — Pipelines with Kedro

> “Nobody knows which cells run in which order.”

Continue your **HighRev classification project** from Session 3. You will make its
dependencies explicit, put model options in YAML, validate raw data before training,
reuse modeling through namespaces, apply an environment override, and test the full
CLI workflow. Work individually in your exercise repository; read and copy named
assets from the separate course checkout. The final team project stays separate.

**Full route: 240 minutes, including two breaks.** In a compact 180-minute lesson,
the instructor demonstrates namespaces and environment overrides while you complete
the core pipeline and required integration checks. Finish independent implementation
of those additions in the next supervised practical period. Record what you actually
implemented and ran. Exercises and evidence notes are ungraded.

## Before class

Your Week 3 exercise must have importable preparation/modeling functions, passing
behavior tests, a working `python -m highrev` command, both tracked raw CSVs,
`pyproject.toml`, `uv.lock`, and Python 3.12. Keep your documented invalid-quantity
policy. Resolve missing data or unfinished extraction first.

Commands below run from your **exercise root**, not the course checkout. Python/uv
commands work in PowerShell or a POSIX shell; copying instructions use the exact
destinations in the [asset inventory](04_kedro/README.md). Merge files that already
exist instead of overwriting your implementation. Copy tests at their named exercise,
not all at once, so future placeholders do not break an earlier working checkpoint.

```powershell
git status --short
git rev-parse HEAD
uv sync --locked
uv run --locked pytest tests/unit -q
uv run --locked python -m highrev
```

Install the Ex 2 dependencies before class if possible. Fresh package installation
requires registry access or a complete cache. The teacher has verified execution
in an existing reference environment; a clean installation on your machine is a
separate readiness check.

## Concepts you will use

| Concept | Meaning in this project |
|---|---|
| Node | Ordinary Python function plus named inputs and outputs |
| Pipeline / DAG | Dependencies between nodes; the Python list order does not define execution order |
| Data Catalog | Maps logical dataset names to loaders, savers, paths, and formats |
| MemoryDataset | Intermediate value that disappears when that process exits |
| Parameters | Configuration injected as `params:<name>` inputs |
| Registry | Named runnable graphs; `__default__` is the normal CLI entry point |
| Namespace | Prefix for a reusable pipeline instance's nodes and datasets, with selected inputs/parameters remapped |
| Configuration environment | Base configuration plus a selected override directory |
| Integration test | Runs actual components together and checks their observable behavior |

pandas performs table transformations. The scikit-learn Pipeline keeps fitted
preprocessing with the estimator. Kedro connects the broader workflow and handles
catalog I/O. Airflow, Prefect, and Dagster are broader workflow platforms with
overlapping capabilities; they can provide scheduling and operational management.
A local Kedro command does not create a scheduled service. MLflow, Docker, and
cloud infrastructure address additional responsibilities later in this course.

Kedro is useful when multiple stages, data boundaries, configurations, and people
benefit from common structure. A small stable script can be sufficient for a
one-off task; a framework also adds conventions and setup work. A successful Kedro
run does not prove that a persisted intermediate is current or record all provenance.

## Ex 1 — Explain and sketch the workflow

**Time: 10 minutes. Start:** working Week 3 modules.

1. Copy the [evidence template](04_kedro/pipeline-evidence.md) to `notes/session-04.md`.
2. Draw orders/customers → preparation → labels → split → training/evaluation →
   artifacts. Include the direct `test_set` edge from splitting to evaluation.
3. Mark which inputs/outputs survive closing Python. Add a proposed raw validation
   gate and explain which downstream edges must consume its outputs.
4. Explain what Kedro does here and what an external scheduler would add.

**Check:** you can trace every input needed by evaluation and explain why placing
validation first in a list is insufficient. Retain the sketch for comparison with Viz.
The instructor's twenty-minute demonstration follows this exercise.

## Ex 2 — Bootstrap Kedro and the catalog

**Time: 15 minutes. Start:** completed Ex 1 and Week 3 readiness.

1. Copy only the inventory's **Ex 2** files. They add settings, registry/pipeline
   scaffolds, catalog, and parameters alongside your existing modules.
2. Merge `config-snippets.toml` into the existing `pyproject.toml`. Keep your build
   backend, source discovery, dependencies, Ruff and pytest configuration. Do not
   duplicate a TOML table.
3. Add the required runtime packages and create the local configuration directory:

   ```powershell
   uv add "kedro==1.7.0" "kedro-datasets[pandas-csvdataset,pandas-parquetdataset,pickle-pickledataset,json-jsondataset]==9.6.0"
   uv sync --locked
   uv run --locked python -c "from pathlib import Path; Path('conf/local').mkdir(parents=True, exist_ok=True)"
   uv run --locked kedro --version
   ```

4. Review the lockfile change. Rerun the unchanged modular command under the new
   environment before attributing a score difference to pipeline wiring.
5. Trace each catalog entry to its file. CSV customer identifiers load as strings;
   Parquet preserves the prepared data's types/index more directly than CSV.
   Ignore generated directories `data/02_intermediate`, `data/03_primary`,
   `data/06_models`, and `data/08_reporting`. Keep raw CSVs tracked until Week 5.
   Keep local credentials ignored and base configuration tracked.

**Check:** Kedro imports, both raw files exist, and you understand which datasets
persist. Registry/pipeline placeholders are not yet runnable. The supplied settings
explicitly use base/local environments and soft parameter merging; Ex 7 explains why.

## Ex 3 — Wire functions and model options

**Time: 25 minutes. Start:** Ex 2 scaffolds and your existing functions.

First make your `build_model` and `train_model` functions accept an optional
`model_options=None` argument. Calls without it retain Week 3 defaults:
`C=1.0`, `max_iter=500`, `class_weight='balanced'`. When options are supplied,
they reach the LogisticRegression constructor. Keep fitted preprocessing inside
the sklearn Pipeline. Add a small test proving that a non-default `C` reaches the
estimator. Keep your runner unchanged and confirm its baseline still works.

Build the six core nodes using this contract:

| Node | Function arguments ← Kedro inputs | Outputs |
|---|---|---|
| `prepare_orders` | `orders` ← `orders` | `orders_by_customer` |
| `prepare_customers` | `customers` ← `customers`; `orders_by_customer` ← same name; `max_age` ← `params:max_age` | `customers_prepared` |
| `label_customers` | `customers_prepared` ← same name; `threshold` ← `params:high_revenue_threshold` | `customers_labeled` |
| `split_data` | `labeled` ← `customers_labeled`; `test_size` ← `params:test_size`; `random_state` ← `params:random_state` | `train_set`, `test_set` |
| `train_model` | `train` ← `train_set`; `model_options` ← `params:model_options` | `classifier` |
| `evaluate_model` | `model` ← `classifier`; `test` ← `test_set` | `metrics` |

Use input dictionaries when argument and dataset names differ. A list of output
names unpacks the function's returned tuple. Here is an unrelated mapping example:

```python
node(
    filter_measurements,
    inputs={"frame": "measurements", "limit": "params:minimum_reading"},
    outputs="accepted_measurements",
    name="filter_measurements",
)
```

Return a Pipeline from each module. Register `data_processing`, `modeling`, and
their `__default__` composition. Leave the later template-extraction stubs unused
until Ex 6. Keep the parameter defaults in the supplied YAML.

```powershell
uv run --locked kedro registry list
uv run --locked kedro run
uv run --locked python -m highrev
```

**Check:** six nodes execute and default metrics agree with the direct runner
under the same inputs/environment. Existing tests remain green. Source/configuration
and the lockfile are retained; generated artifacts stay ignored.

**Break: 10 minutes.**

## Ex 4 — Validate inputs and report class balance

**Time: 35 minutes. Start:** six-node pipeline works.

Copy the inventory's **Ex 4** files now: validation/reporting stubs and their unit
tests. Implement two pure functions; neither reads or writes files.

### A. Validate raw inputs before preparation

Implement `validate_inputs(customers, orders)` using the supplied required-column
sets. Reject missing columns, empty tables, null/blank customer identifiers, and
nonnumeric/nonfinite quantities or prices. Raise a `ValueError` naming the table
and field. Return the two frames in customer/order order without changing values.

The course data already has repeated customer IDs: preserve them. Deduplication
is a separate business decision. Keep the Week 3 negative-quantity policy in
`prepare_orders`; do not silently change that contract. Optional feature missing
values can still be handled by the model's imputer. This is a limited schema check.

Add node `validate_inputs` with raw inputs `customers`, `orders` and outputs
`validated_customers`, `validated_orders`. Change **both** preparation consumers:
`prepare_orders` takes `validated_orders`; `prepare_customers` takes
`validated_customers` and the aggregate. These edges enforce the gate. Leave the
validated frames in memory and keep the raw catalog entries.

Write focused tests with small fixtures: accepted values/input preservation,
missing column, invalid identifier, empty input, and bad quantity/price. Check a
specific error; “some exception occurred” is insufficient.

### B. Add a reporting branch

Implement `report_class_balance(customers_labeled)`. Return native JSON-compatible
values for `rows`, `positive`, `negative`, `positive_rate`; reject an empty or
null/nonboolean target with `ValueError`. Leave the input unchanged. Write tests
from hand-countable labels, including single-class and invalid cases.

Add node `report_class_balance` after labeling. Catalog its output `class_balance`
as a `json.JSONDataset` at `data/08_reporting/class_balance.json`. This branch and
the modeling split share an input; neither depends on the other's output.

```powershell
uv run --locked pytest tests/unit/test_validation.py tests/unit/test_reporting.py -q
uv run --locked pytest tests/unit -q
uv run --locked kedro run
```

**Check:** eight nodes execute on valid data; unit tests reveal invalid inputs.
Ex 8 will prove that a raw schema failure blocks the assembled training workflow.

## Ex 5 — Select and debug a pipeline

**Time: 20 minutes. Start:** a successful eight-node full run.

1. Run `uv run --locked kedro run --pipelines=modeling`. Explain why this fresh
   process can load the persisted `customers_labeled` file and run only three nodes.
2. Predict and run `uv run --locked kedro run --from-nodes=train_model`. Explain
   the missing `train_set`/`test_set`: they existed only in the earlier process.
   Recover by running the entire named modeling pipeline.
3. In a separate disposable copy containing only code/configuration/raw data,
   run modeling first. It should fail because the labeled Parquet does not exist.
   Run `--pipelines=data_processing`, then `--pipelines=modeling`; observe recovery.
   Copy your own implementation, not the teacher solution. A fresh-copy fixture
   in Ex 8 automates this isolation approach.
4. Inspect the graph with Viz if installed:

   ```powershell
   uv add --dev "kedro-viz==12.4.0"
   uv run --locked kedro viz run
   ```

   Stop the server with Ctrl+C. If unavailable, use your diagram and actual CLI logs.

**Check:** explain missing memory versus a missing persisted file, and why modeling
alone does not validate today's raw inputs or ensure the prepared artifact is fresh.
Keep the failure/recovery observations; your original raw data remains unchanged.

## Ex 6 — Reuse modeling with namespaces

**Time: 30 minutes. Start:** working default graph and configurable model functions.

1. Extract `create_split_pipeline()` and `create_training_pipeline()` in the
   modeling pipeline module. The first contains only splitting. The second is
   a template containing only training and evaluation. Keep `create_pipeline()`
   as their ordinary composition so default and selected modeling still work.
2. In the registry, instantiate the training template twice with namespaces
   `low_c` and `high_c`. Expose `train_set` and `test_set` as shared inputs.
   Remap `model_options` to `models.low_c` and `models.high_c` respectively.
   Consult the [namespace API](https://docs.kedro.org/en/1.7.0/build/namespaces/).
3. Register `comparison = data_processing + shared_split + low_c + high_c`.
   Do not put a split inside each variant. Leave outputs namespaced so names do
   not collide. The supplied parameter groups use C=0.1 and C=10; other options match.
4. Add these four catalog entries using the indicated dataset types:

   | Dataset | Type | Filepath |
   |---|---|---|
   | `low_c.classifier` | `pickle.PickleDataset` | `data/06_models/low_c/classifier.pickle` |
   | `high_c.classifier` | `pickle.PickleDataset` | `data/06_models/high_c/classifier.pickle` |
   | `low_c.metrics` | `json.JSONDataset` | `data/08_reporting/low_c/metrics.json` |
   | `high_c.metrics` | `json.JSONDataset` | `data/08_reporting/high_c/metrics.json` |

5. Run `uv run --locked kedro run --pipelines=comparison`. Inspect both reports
   and the two namespaces in Viz. Explain why the ten-node graph includes one
   split and two training/evaluation branches. Low C means stronger regularization.

**Check:** both variants use the same split and target, and their artifacts do not
overwrite one another. Record scores without claiming a production winner from one
comparison. Changing `high_revenue_threshold` would change the task, so keep it 300.

To revisit the earlier configuration experiment separately, preserve default report
values, run `kedro run --params=high_revenue_threshold=500`, record changed class
balance, and restore with a full default run. That experiment is not a model tournament.

**Break: 10 minutes.**

## Ex 7 — Apply environment overrides

**Time: 20 minutes. Start:** working model configuration and supplied settings module.

1. Create `conf/development/parameters.yml` with a `model_options` group containing
   only `C: 0.25`.
2. Create `conf/development/catalog.yml`. Override `classifier` and `metrics` with
   complete entries: preserve their dataset types and change paths to
   `data/06_models/development/classifier.pickle` and
   `data/08_reporting/development/metrics.json`.
3. Read `settings.py`. The explicit `parameters: soft` merge keeps `max_iter` and
   `class_weight` from base while replacing only C. Catalog merging retains default
   replacement behavior, so each overridden entry includes both type and filepath.
4. Run both environments:

   ```powershell
   uv run --locked kedro run --env=development
   uv run --locked kedro run
   ```

5. Inspect each saved estimator's C or write a focused check. Record which paths
   changed. The prepared data and class report still share base paths because their
   preparation settings were unchanged. This exercise does not establish safe
   concurrent execution or complete environment isolation.

**Check:** base + development yields C=0.25, max_iter=500, class_weight=balanced.
The ordinary run yields C=1.0. `--env=development` does not also layer `local` on top.
Commit the nonsecret development files; keep credentials out of committed configuration.

## Ex 8 — Test the assembled pipeline

**Time: 30 minutes. Start:** validated default graph. This exercise is required.

Copy [the integration scaffold](04_kedro/starter/tests/integration/test_kedro_pipeline.py)
to `tests/integration/test_kedro_pipeline.py` **now**. Its fixture copies your code,
configuration, and raw inputs into a temporary project and invokes a new CLI process.
You author the assertions. Keep outputs in that temporary project.

1. Implement the full-run test: require exit zero, saved classifier, expected metric
   keys/ranges, and report counts matching the saved labeled table. Include command
   stdout/stderr in assertion failures to expose setup problems.
2. Implement the invalid-schema test: remove `tshirt_price` only from the temporary
   orders CSV; require nonzero exit and the specific schema error. Prove no training
   node executed and no model/metrics appeared. A fresh directory prevents stale
   artifacts from making this test falsely pass.
3. Run these tests, the existing suites, and quality checks:

   ```powershell
   uv run --locked pytest tests/integration/test_kedro_pipeline.py -q
   uv run --locked pytest tests/unit tests/integration -q
   uv run --locked ruff check .
   uv run --locked ruff format --check .
   uv run --locked kedro run
   ```

Do not replace assertions with skips or accept an unrelated import error as the
expected validation failure. Preserve the Week 3 integration tests and CI workflow.
Finish copied placeholders before a full-suite commit.

**Check:** two meaningful CLI integration tests pass and invalid data cannot reach
training in the full graph. This does not prove future model quality or freshness
when a user deliberately selects a downstream graph that omits raw validation.

After the required checks, [direct-function parity](04_kedro/extensions/test_kedro_parity.py)
remains optional practice. Copy it to `tests/integration/test_kedro_parity.py` only
when ready to implement it; it must not break the completed required test suite.

## Expected failures and recovery

| Observation | Meaning and first action |
|---|---|
| Kedro cannot find the project | Check current directory, package discovery and `[tool.kedro]` |
| `NotImplementedError` | Finish the named function/test at its scheduled exercise |
| `orders: missing required columns` | Inspect the input schema; fix data or choose the intended catalog environment |
| Training still runs despite a validation failure | Check whether preparation consumes validated outputs |
| Missing train/test frames after node selection | Include the split producer in the same invocation |
| Missing labeled Parquet for modeling | Run data processing first or the default full graph |
| Namespace output collision | Keep outputs namespaced and catalog filepaths distinct |
| Missing nested parameter fields | Inspect the effective configuration and parameter merge policy |
| Duplicate base/development keys | Keep explicit base/local loader arguments in settings |
| Old output files remain after failure | Inspect the exit/log; use a fresh temporary project to prove artifact creation |
| Model metrics changed after setup | Compare direct and Kedro paths under the same new lock and parameters |

## Handoff to Week 5

- [ ] I can explain Kedro's role and its limits relative to scheduling/deployment.
- [ ] My default pipeline preserves Week 3 behavior at default settings.
- [ ] Raw validation is enforced through dependencies; report and model options are tested.
- [ ] I can explain partial-run failure and successful recovery.
- [ ] Two namespaces share one split and save distinct artifacts, or I have recorded independent implementation still pending after the compact delivery.
- [ ] I can explain environment overrides and effective values.
- [ ] The required full-run and invalid-input integration checks pass.
- [ ] My notes distinguish observed execution from unverified installation/remote behavior.
- [ ] I restored default parameters, retained raw inputs, and ignored generated artifacts.

Update your exercise README with run/test commands and output locations. Commit named
source, configuration, test, environment, README, and evidence files; a remote push
is not required. DVC next addresses recovering the exact raw data belonging to a run.
Optional reading is individual ungraded preparation. Grading is defined only by the
[final project rubric](../FINAL_PROJECT_RUBRIC.md).

## Reading

- [Kedro namespaces](https://docs.kedro.org/en/1.7.0/build/namespaces/).
- [Configuration and merge behavior](https://docs.kedro.org/en/1.7.0/configure/advanced_configuration/).
- [Kedro and Airflow](https://docs.kedro.org/en/1.7.0/deploy/supported-platforms/airflow/): architecture context; no deployment required in this lesson.
- [Dataset reference](https://docs.kedro.org/projects/kedro-datasets/en/stable/).
