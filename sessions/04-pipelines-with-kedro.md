# Session 4 — Pipelines with Kedro

**Week 4 · 180 minutes · Individual practical work**

> “Nobody knows which cells run in which order.”

The notebook runs for its author because intermediate objects already exist in memory.
A colleague starts a fresh process and cannot reconstruct the same execution. Your
Session 3 functions already describe the transformations; this session makes their
dependencies, inputs, parameters, and saved outputs explicit with Kedro.

By the end, you can build and inspect a dependency graph, connect existing Python
functions as nodes, distinguish memory from persisted datasets, run a named pipeline
in a new process, and explain what a reproducible run still needs beyond the graph.
You will also add and test your own reporting node.

Work independently in your **individual exercise repository**, continuing your own
Session 3 implementation. Keep the course checkout separate; it supplies only the
named starter files below. The final team project has a separate repository and
collaboration workflow. Exercises, evidence notes, and this self-check are ungraded.

## Before class

Required starting state:

- Your importable `highrev.data_processing` and `highrev.modeling` modules implement
  the Session 3 contracts; `uv run --locked python -m highrev` runs successfully.
- The age, aggregation, target boundary, and modeling tests pass. Keep your documented
  negative-quantity policy and existing runner.
- `data/01_raw/customers.csv` and `data/01_raw/orders.csv` are available in your
  exercise project. Raw data stays untracked until Session 5 introduces DVC.
- `pyproject.toml`, `uv.lock`, and your Python version declaration are present.
  Complete the dependency installation in Ex 2 before class where possible;
  internet access is needed for uncached packages. The teacher rehearsal uses an
  existing reference interpreter; it does not establish that a fresh uv environment
  has been rebuilt successfully on your machine.
- Update the separate course checkout to obtain [the supplied assets](04_kedro/README.md).

Unless explicitly labelled otherwise, commands below run from the **exercise project
root**, using PowerShell, Bash, or another shell that supports the shown command.
Use the Python snippets as written on either platform. Never run exercise commands
in the course checkout. Record your starting commit and local changes:

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
An uncatalogued intermediate normally uses memory for that run. A catalogued Parquet
or pickle output can be loaded by a later process.

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

Kedro's pipeline is different from the scikit-learn `Pipeline` returned by your model
builder. Kedro connects data preparation, fitting, and evaluation; the scikit-learn
object keeps feature preprocessing with the fitted estimator.

Kedro does not automatically know that a saved dataset is current. A successful
partial run can consume an older file. Reproducibility still depends on the data,
code, environment, parameters, and deterministic behavior of your functions.

## Lesson route

| Block | Participation | Minutes |
|---|---|---:|
| Ex 1 — Sketch the dependencies | Individual | 10 |
| Opening demonstration: functions, nodes, catalog, registry | Instructor | 20 |
| Ex 2 — Bootstrap Kedro, configuration, and catalog | Individual | 20 |
| Ex 3 — Wire the existing functions | Individual | 30 |
| Break | Everyone | 10 |
| Ex 4 — Inspect and select pipelines | Individual | 25 |
| Ex 5 — Add and test class balance reporting | Individual | 30 |
| Ex 6 — Change a parameter and reproduce the result | Individual | 25 |
| Wrap-up and Session 5 handoff | Everyone | 10 |

### Ex 1 — Sketch the dependencies

**Purpose:** identify what must exist before each operation can run. **Start:** your
working Session 3 modules. **Time:** 10 minutes, individual.

1. Copy [the evidence template](04_kedro/pipeline-evidence.md) to
   `notes/session-04.md` in your exercise project. Fill in your starting commit,
   data identity, and baseline metrics from the readiness run.
2. Sketch the graph from raw orders and customers through aggregation, customer
   features, target creation, split, fit, and evaluation. Include parameters as inputs.
3. Mark which objects exist only in the current Python process. Choose an intermediate
   that would let training restart without repeating raw data preparation.
4. Predict whether fitting can start before the split, and whether evaluating can
   start before fitting. Explain each answer using an input dependency.

**Check and keep:** your own sketch and reasoning in the evidence note. There is no
code to change yet. During the 20-minute demonstration, compare your sketch with the
displayed graph and revise any missing dependency.

### Ex 2 — Bootstrap Kedro, configuration, and catalog

**Purpose:** give Kedro a project, configuration, and storage boundary. **Start:** Ex 1
and a working Session 3 package. **Time:** 20 minutes, individual.

1. Copy only the required files listed in [the asset inventory](04_kedro/README.md), from the
   course checkout to their exact destinations. Leave the optional integration
   scaffold in the course checkout until you begin that extension. Create destination directories as
   needed. Compare and merge a destination that already exists. Keep your Session 3
   `data_processing.py`, `modeling.py`, `runner.py`, and `__main__.py`.
2. Merge [config-snippets.toml](04_kedro/config-snippets.toml) into your existing
   `pyproject.toml`; never replace the file or duplicate a TOML table. Preserve your
   build backend, `src/` package discovery, Python requirement, and Ruff settings.
3. Install the required dependencies and lock the resulting environment:

   ```bash
   uv add "kedro==1.7.0" "kedro-datasets[pandas-csvdataset,pandas-parquetdataset,pickle-pickledataset,json-jsondataset]==9.6.0"
   uv lock
   uv sync --locked
   uv run --locked kedro --version
   ```

   Review the lockfile diff. If dependencies changed, rerun `python -m highrev`
   under this lock and record that comparison before attributing differences to Kedro.
4. Ensure `conf/local/` exists:

   ```bash
   uv run --locked python -c "from pathlib import Path; Path('conf/local').mkdir(parents=True, exist_ok=True)"
   ```

   Keep local credentials out of Git. Track the base catalog and parameters. Ignore
   generated files in `data/02_intermediate/`, `data/03_primary/`, `data/06_models/`,
   and `data/08_reporting/`, while retaining directory marker files if your project
   uses them. Preserve existing ignores and tracked raw inputs.
5. Read `conf/base/catalog.yml` and `conf/base/parameters.yml`. Identify the CSV
   loading settings that preserve customer identifiers as strings. Explain why the
   aggregate index must survive a Parquet round trip.

| Name | Storage role |
|---|---|
| `customers`, `orders` | Raw CSV inputs, explicit string identifiers |
| `orders_by_customer` | Persisted Parquet aggregate |
| `customers_prepared` | Intermediate in memory |
| `customers_labeled` | Persisted Parquet input for modeling |
| `train_set`, `test_set` | Split frames in memory |
| `classifier` | Persisted fitted scikit-learn pipeline via PickleDataset |
| `metrics` | JSON evaluation report |

**Check and keep:** Kedro imports and prints its version; explain every catalog entry
and the four parameters. The pipeline stubs are intentionally incomplete, so a run
can still fail with `NotImplementedError`. Keep source/configuration and lock changes.

### Ex 3 — Wire the existing functions

**Purpose:** express the dependency graph while preserving tested behavior. **Start:**
Ex 2, your Session 3 functions, and the pipeline/registry stubs. **Time:** 30 minutes.

Implement `create_pipeline()` in the two pipeline modules. Import and wrap your
existing functions; move no business logic into pipeline definitions. Use the names
below so the later CLI selectors match your graph.

| Pipeline | Node name | Function | Inputs in argument order | Output names |
|---|---|---|---|---|
| data_processing | `prepare_orders` | `prepare_orders` | `orders` | `orders_by_customer` |
| data_processing | `prepare_customers` | `prepare_customers` | `customers`, `orders_by_customer`, `params:max_age` | `customers_prepared` |
| data_processing | `label_customers` | `label_customers` | `customers_prepared`, `params:high_revenue_threshold` | `customers_labeled` |
| modeling | `split_data` | `split_data` | `customers_labeled`, `params:test_size`, `params:random_state` | `train_set`, `test_set` |
| modeling | `train_model` | `train_model` | `train_set` | `classifier` |
| modeling | `evaluate_model` | `evaluate_model` | `classifier`, `test_set` | `metrics` |

1. Return a Kedro pipeline from each module. For the split, declare **two** output
   names so Kedro unpacks the returned tuple.
2. Implement `register_pipelines()` with keys `data_processing`, `modeling`, and
   `__default__`. The default composes both pipelines. Keep the parameter defaults
   `max_age: 100`, `high_revenue_threshold: 300`, `test_size: 0.2`, `random_state: 42`.
3. Execute from the project root:

   ```bash
   uv run --locked kedro registry list
   uv run --locked kedro run
   ```

4. Inspect generated Parquet, model, and metrics files using the paths in your
   catalog. Compare metrics and row counts with your modular runner under the same
   lock, data, and parameters. Investigate discrepancies; do not loosen assertions
   to force agreement.

**Check and keep:** all six nodes execute, registered names are present, and the
result matches the runner within a justified numeric tolerance. Session 3 tests
still pass. Record output paths and commit named source/configuration changes;
generated model and data files remain ignored. Reporting and its unit tests belong
to Ex 5; new integration tests are an optional Ex 6 extension and have not yet
been copied into your exercise repository.

**Break: 10 minutes.**

### Ex 4 — Inspect and select pipelines

**Purpose:** discover which inputs a selected graph needs in a fresh process.
**Start:** a successful Ex 3 full run. **Time:** 25 minutes, individual.

1. Inspect the graph in your pipeline definitions and registry. If the optional
   visualization dependency is available, install and launch it:

   ```bash
   uv add --dev "kedro-viz==12.4.0"
   uv sync --locked
   uv run --locked kedro viz run
   ```

   Stop the server with Ctrl+C when finished. A drawing of the node names and
   dataset edges is an acceptable fallback if visualization is unavailable.
2. Run the named modeling pipeline in a **new CLI process**:

   ```bash
   uv run --locked kedro run --pipeline=modeling
   ```

   Explain why this works: the prior full run persisted `customers_labeled`, which
   the selected pipeline can load. Record which raw preparation nodes did not run.
3. Predict this command, then run it and save the relevant error:

   ```bash
   uv run --locked kedro run --from-nodes=train_model
   ```

   `train_set` and `test_set` existed only in the previous process. Selecting a
   downstream node does not recreate its upstream memory datasets. Recover by
   running the full modeling pipeline, whose split node produces those frames.
4. Demonstrate a missing persisted input safely. Use a disposable exercise copy,
   or temporarily **rename only the generated `customers_labeled` Parquet file**
   to a backup name. Find its exact location in the catalog first. Run the modeling
   pipeline again and observe the missing-input failure. Restore the file immediately,
   then rerun modeling successfully. Never rename or remove raw inputs.
5. Explain why an existing labeled file can still be stale after a raw input or
   threshold change. A successful selected run proves that its inputs were available;
   it does not prove that they were rebuilt from the current configuration.

**Check and keep:** record one successful selected run, both intentional failures,
and successful recovery. Preserve your working artifacts and evidence. Explain
the difference between selecting `modeling` and starting at `train_model`.

### Ex 5 — Add and test class balance reporting

**Purpose:** extend the graph with useful behavior and prove the assembled pipeline
works. **Start:** Ex 4 recovery complete. **Time:** 30 minutes, individual.

1. Implement `report_class_balance(customers_labeled)` in `highrev/reporting.py`.
   Its `high_revenue` column must contain non-null boolean labels only. Return a
   JSON-compatible dictionary with `rows`, `positive`, `negative` as native Python
   integers and `positive_rate` as a native float. Reject an empty target or invalid
   labels with `ValueError`; do not silently turn strings or integers into booleans.
   Leave the input unchanged.
2. Add `report_class_balance` to the data-processing pipeline, taking
   `customers_labeled` and producing `class_balance`. Add a JSONDataset catalog
   entry that saves `data/08_reporting/class_balance.json`. This node and the
   modeling split share an input; neither depends on the other's output.
3. Replace the unit-test requirements in `tests/unit/test_reporting.py` with your
   own assertions: a hand-calculated mixed example, all-positive and all-negative
   examples, empty input, null/nonboolean labels, native JSON serialization, and
   input immutability. Do not calculate expected counts by calling the function
   being tested.
4. Run the reporting tests, then your completed unit suite and quality checks:

   ```bash
   uv run --locked pytest tests/unit/test_reporting.py -q
   uv run --locked pytest tests/unit -q
   uv run --locked ruff check .
   uv run --locked ruff format --check .
   uv run --locked kedro run
   ```

**Check and keep:** your report agrees with the persisted labels, accepts valid
boolean cases, rejects invalid inputs, and participates in the default graph.
The unit tests establish the reporting contract on their chosen inputs; the full
run shows that your added node executes. Keep implementation, tests, catalog
changes, and evidence. The optional integration scaffold remains in the course
checkout, outside your collected tests. Your existing Session 3 integration tests
and CI should continue to pass.

### Ex 6 — Change a parameter and reproduce the result

**Purpose:** distinguish a new target definition from a model improvement and
record the conditions needed to reproduce a run. **Start:** a full default run
including reporting and passing Ex 5 checks. **Time:** 25 minutes, individual.

1. Save the current metrics and class-balance values in `notes/session-04.md`
   **before** the next run overwrites their files. Record code commit, data identity,
   parameters, Python/package versions, and lockfile state. Copy reports into an
   ignored scratch folder if you also want to retain the original JSON files.
2. Predict what happens when the revenue threshold increases. Then execute the
   **full** pipeline with a CLI override:

   ```bash
   uv run --locked kedro run --params=high_revenue_threshold=500
   ```

3. Record the new class counts and metrics before restoring anything. Explain
   that this changes the target definition and can change the stratified split.
   A higher AUC here is not a fair claim that the model improved on the same task.
   Check the YAML file: the CLI override applies to this invocation and does not
   rewrite the saved default.
4. Restore the default artifact state with a full run, then launch a separate
   modeling process and compare its metrics with the restored full run:

   ```bash
   uv run --locked kedro run
   uv run --locked kedro run --pipeline=modeling
   ```

   State the tolerance and conditions used for the comparison. A process restart
   with local files is evidence of fresh-process execution; it does not establish
   a clean-clone or second-machine reproduction by itself.
5. Update your exercise README with the Kedro command, named pipelines, parameter
   defaults, and artifact locations. Keep Session 3's modular command available.
   Review `git diff` and `git status --short`; commit named source, test,
   configuration, lock, README, and note paths. No remote push is required here.

**Check and keep:** evidence records baseline, threshold-500, and restored-default
results, with a reasoned explanation. No temporary renames, intentional failures,
or changed defaults remain. Your next run can start from a fresh process.

**Optional extension — automate integration evidence, or finish it later.**
The manual fresh-process checks above are the essential class checkpoint. The
teacher's completed rehearsal provides a reference proof of full direct-function
parity; writing that entire automated proof is additional student work.

When time permits, copy the optional
[integration scaffold](04_kedro/extensions/test_kedro_pipeline.py) from the course
checkout to `tests/integration/test_kedro_pipeline.py` in your exercise project.
Create the parent directory if needed; compare and merge if the destination already
exists. Implement the copied requirements before running the full suite or committing
the new test file: unfinished placeholders would fail the existing Session 3 CI.

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
uv run --locked pytest tests/integration/test_kedro_pipeline.py::test_modeling_requires_persisted_input -q
uv run --locked pytest tests/integration/test_kedro_pipeline.py::test_kedro_matches_direct_functions -q
```

Run the complete integration suite once all copied placeholders are implemented.
Record an unfinished extension as pending; it does not block the core Session 4
checkpoint or erase the manual evidence you collected.

## Expected observations and recovery

| Observation | Interpretation and first recovery step |
|---|---|
| Kedro cannot locate a project | Run at the exercise root; inspect the merged `[tool.kedro]` table and package name. |
| `NotImplementedError` | A student function, registry, pipeline, or test is still a requirement stub; complete the named exercise. |
| Duplicate TOML table | Merge fragment keys into the existing table rather than pasting another header. |
| Dataset class or Parquet engine missing | Install the specified kedro-datasets extras, update the lock, then sync with `--locked`. |
| Join unexpectedly loses customers | Inspect CSV identifier dtypes and aggregate index preservation; do not cast IDs to integers. |
| Missing `train_set` after `--from-nodes` | Run `--pipeline=modeling` so the split executes in the same process. |
| Missing labeled Parquet for modeling | Restore the renamed file or run the full pipeline from the raw inputs. |
| Success with surprising old results | A partial run can load stale artifacts; rerun the full graph with the intended parameters. |
| Report is rejected by JSON serialization | Convert counts and rate to native Python scalars in the reporting function. |
| Changed metrics after dependency installation | Compare both execution paths under the same new lock before diagnosing wiring. |
| Single-class or undersized split | Check the threshold, labels, and data; retain stratification and use enough examples per class in tests. |
| Visualization cannot start | Use the registry and a graph sketch; pipeline execution and evidence remain required. |

## Wrap-up and next preparation

- [ ] I can explain every input and output in the graph and why list order is insufficient.
- [ ] My six original nodes call my existing Session 3 functions without duplicating logic.
- [ ] My catalog distinguishes persisted artifacts from intermediates in memory.
- [ ] I observed selected-run success, missing-input failures, and recovery.
- [ ] My reporting node has meaningful unit tests and runs in the composed pipeline.
- [ ] My manual fresh-process runs succeed after preparation, and my notes record their limits.
- [ ] My experiment notes preserve results before overwriting and distinguish a changed target from improved modeling.
- [ ] Code, base configuration, tests, and lockfile are tracked; generated artifacts are ignored; raw inputs remain tracked.

Session 5 assumes a runnable default Kedro pipeline, explicit raw input and artifact
paths, tested functions, a locked environment, and the default threshold restored.
Finish missing pipeline wiring first, then reporting tests and manual reproduction.
Automated integration tests are an optional extension to finish later. Record any
unfinished core checkpoint honestly so the instructor can help you recover.

Optional ungraded individual research, kept outside the team project: explain how
you would identify the exact two raw CSV versions that produced a model after those
CSVs change. Distinguish saving a model from recording its data lineage. Session 5
introduces DVC to address this missing piece.

## Reading

- [Kedro documentation](https://docs.kedro.org/en/stable/): nodes, pipelines,
  project configuration, parameters, and pipeline selection.
- [Kedro datasets documentation](https://docs.kedro.org/projects/kedro-datasets/en/stable/):
  CSV, Parquet, pickle, and JSON dataset types and their load/save settings.
- [Kedro-Viz documentation](https://docs.kedro.org/projects/kedro-viz/en/stable/):
  optional graph inspection.

Project expectations live in [PROJECT.md](../PROJECT.md); only the
[final project rubric](../FINAL_PROJECT_RUBRIC.md) defines grading and contribution evidence.
