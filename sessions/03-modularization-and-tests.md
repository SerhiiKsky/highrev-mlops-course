# Session 03: Modularization and testing

**Incident.** A refactor changes the age feature from fractional years to whole years.
The script still trains, prints metrics, and saves a model. Which check would show that
its meaning changed before anyone relies on its predictions?

**Goal.** Extract your Session 2 baseline into importable functions, express their behavior
in tests, and show that those tests catch deliberate regressions. End with a command that
reproduces the baseline through the new modules and a workflow that checks quality before
training. Modular code and tests support the [final project rubric](../FINAL_PROJECT_RUBRIC.md).
This session's exercises and checklist are ungraded learning aids.

Use the separate course checkout to read this brief and receive assets. Implement in your
private team project, retaining its history and remotes. Do not import the instructor's
reference project or install its later-session dependencies. Session 4 will connect the
functions you write today into a pipeline.

## Before class

Your team repository should contain its working `baseline.py`, `data/01_raw/customers.csv`,
`data/01_raw/orders.csv`, `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`, and
Session 2's `.github/workflows/reproduce.yml`. Ruff should be a locked development tool.
Confirm `uv sync --locked` and `uv run --locked python baseline.py` work from the team root.
Resolve missing data or stale locks before extracting code. Preserve your existing raw data.

Commands in this brief use **Git Bash on Windows, or a POSIX shell on macOS/Linux**, from
the team repository root unless stated. Python/uv commands also work in PowerShell; the
copy and shell-variable examples use Bash. Close another active virtual environment first.

The teacher's opening uses the ASI 3 deck and Examples 1 to 3: a regression dependency
diagram, CLV functions separated from a main flow, and the HighRev classification flow.
You do not need their historical environments to complete this lab.

## Building blocks supplied

Open the [asset inventory](03_modularization/README.md) for each file's purpose and exact
destination. It links all required starter files. Also use:

- [Configuration fragment](03_modularization/config-snippets.toml): packaging and pytest
  settings to **merge** into your current `pyproject.toml`.
- [Blank contract and evidence record](03_modularization/contracts-and-evidence.md): copy
  to `notes/session-03.md` and fill in your own results.
- [Integration and workflow requirements](03_modularization/integration-requirements.md):
  the required behavior for Ex 6, without an implementation.

The source and test files contain placeholders. `NotImplementedError` is expected until
you implement them. Replacing a placeholder with `pass`, a skip, or an assertion that only
checks `True` does not establish the contract. There are no answer notebooks in this drop.

## Concepts for the work

| Concept | How to use it today |
|---|---|
| Responsibility | Give a module a coherent job: transform frames, construct/train/evaluate a model, or read/write files and connect steps. |
| Contract | Specify accepted inputs, output shape and meaning, parameter behavior, and allowed side effects. |
| Refactor | Change structure while preserving observed behavior. Changing the invalid-data policy later is a separate decision. |
| Pure transformation | Return a result without modifying the caller's input or accessing files. A deep-copy comparison can test input preservation. |
| Unit test | Use a small, controlled input and an independently derived expected result to check one behavior. |
| Integration test | Exercise boundaries together, including command invocation, data loading, and model persistence. |
| Regression test | Protect a behavior that might change unnoticed; demonstrate its usefulness by causing the bug deliberately. |
| Fixture | Reusable input setup. The supplied CSVs are tiny synthetic inputs, not answer tables. |
| Arrange / act / assert | Prepare a revealing input, call the behavior once, and compare with a meaningful expectation. |
| Import safety | Importing definitions must not read CSVs, train, print metrics, or save files. Execution belongs behind `main()`. |

A score is an aggregate observation. Two feature implementations can print the same rounded
score on one dataset. A focused age test asks a more precise question. Conversely, correct
small transformations do not prove that the whole command connects them correctly.

Keep preprocessing inside the scikit-learn model pipeline so training and later predictions
use the same transformations. Fit preprocessing on training data only. Keep the categorical
normalization helper at module scope so the saved model can find it on reload.

## In class

The teacher introduction and demonstration take at most 30 minutes. The six practical
blocks below take 130 minutes, with a 10-minute break after Ex 3 and a 10-minute wrap-up:
180 minutes in total. Work independently on an agreed team branch; coordinate file ownership
and review with teammates. Record your own reasoning, including when working together.

### Ex 1 — Map responsibilities and save the baseline (15 minutes)

**Start:** the working Session 2 project. **Purpose:** know what must remain equivalent.

1. Open `baseline.py`. Identify I/O, order aggregation, customer features, target creation,
   splitting, model construction, fitting, and evaluation. Sketch the dependencies between
   those responsibilities before moving lines.
2. Inspect `git status --short` and record the current commit. Save a baseline run and
   environment versions in your notes. Record the three metrics and test-row count; use
   your own result instead of an old course example.

   ```bash
   uv sync --locked
   uv run --locked python -c "import sys, pandas, sklearn, numpy; print(sys.version); print(pandas.__version__, sklearn.__version__, numpy.__version__)"
   uv run --locked python baseline.py
   ```

3. Locate the threshold, age limit, split settings, and model hyperparameters. Explain which
   changes would affect behavior and which only relocate code. Record data identity using
   the commit that contains the two CSVs and note any uncommitted data changes.

**Check:** you can point to the input/output boundary for each proposed module and reproduce
the same baseline in the locked environment. If it fails, repair Session 2 readiness first.
Keep `baseline.py` as the comparison until the modular command works.

### Ex 2 — Extract modules without changing behavior (30 minutes)

**Start:** Ex 1's baseline and the supplied skeleton. **Purpose:** make behavior importable.

1. Update your separate course checkout. Copy the named starter trees using the inventory.
   For sibling checkouts, these Bash commands run from the **team root**:

   ```bash
   lesson_assets=../highrev-mlops-course/sessions/03_modularization
   mkdir -p src tests notes
   cp -Rn "$lesson_assets/starter/src/highrev" src/
   cp -Rn "$lesson_assets/starter/tests/." tests/
   cp -n "$lesson_assets/contracts-and-evidence.md" notes/session-03.md
   ```

   Adjust `lesson_assets` if the course checkout is elsewhere. `-n` preserves existing
   files; compare and merge any existing implementation manually. Confirm the result is
   `src/highrev/data_processing.py`, not `src/src/highrev/...`.
2. Merge the configuration fragment into your existing `pyproject.toml`. Keep the Python
   range, project name/version, dependency bounds, and Ruff settings. Do not duplicate TOML
   headers. If you already use a build backend, configure it to discover `src/highrev`
   instead of adding a second backend. Remove or change `tool.uv.package = false` if present.
3. Add pytest and declare numpy as a direct runtime dependency because the baseline imports
   it directly. Session 2 may have installed numpy only transitively:

   ```bash
   uv add --dev pytest
   uv add numpy
   uv sync --locked
   uv run --locked python -c "import highrev; print(highrev.__file__)"
   ```

   The import should resolve to your team's `src/highrev/__init__.py`. Review the lockfile
   diff. If runtime packages changed, rerun the unchanged baseline under the resulting lock
   before comparing the refactor. Do not add Kedro or MLflow yet.
4. Implement the transformation contracts from your own baseline:

   | Function | Required behavior |
   |---|---|
   | `prepare_orders(orders)` | Normalize baseline T-shirt names, parse dates, calculate totals, group by `customer_id`: earliest date, sum total, mean pages, count order IDs. Return an indexed frame. |
   | `prepare_customers(customers, orders_by_customer, max_age=100)` | Inner-join `customerID` to aggregate index; repair `1993/2/29`, `1947/2/29`, `1965/2/29` to February 28; calculate fractional age as elapsed days divided by 365; retain age strictly below the limit; derive browser/OS; drop raw date, order count, IP, and user-agent columns specified in the stub. |
   | `label_customers(customers_prepared, threshold=300)` | Create boolean `high_revenue` from total strictly greater than the parameter; drop total to prevent target leakage. |

   Each returns a new frame and leaves both inputs unchanged where applicable. Keep customer
   IDs as strings when loading CSVs. Dates use the baseline's year/month/day slash convention,
   with padded or unpadded month/day components. Keep additional fixtures in this format;
   mixed slash/ISO input support would be a separate parsing-contract change. Do not round
   age or replace elapsed days divided by 365 with a calendar-year calculation.
5. Extract `build_model`, `split_data`, `train_model`, and `evaluate_model` using their
   signatures. Keep `NUMERIC`, `CATEGORICAL`, and `TARGET` as declared in the skeleton.
   Preserve the baseline preprocessing, balanced logistic regression, stratified split,
   random state, test size, and probability/decision rules. Evaluation returns keys
   `roc_auc`, `accuracy`, and `f1`.
6. Implement `runner.main()` to read root-relative project CSVs, call the functions, print
   the three metrics, and save `model.pickle`. Keep I/O inside the function. The supplied
   `__main__.py` only wires the explicit command to it.

   ```bash
   uv run --locked python -m highrev
   ```

**Check:** the command runs and matches the unchanged baseline in the same environment.
Importing any module does not execute it. An incomplete function still raises an intentional
`NotImplementedError`; finish that function before interpreting this as a regression.
Commit implementation and packaging changes when this checkpoint works. Keep generated
`model.pickle` ignored.

### Ex 3 — Specify contracts and write focused tests (25 minutes)

**Start:** extracted functions. **Purpose:** define expectations before introducing bugs.

1. Read the synthetic CSVs in `tests/fixtures/`. Calculate the output for a repeated
   customer on paper. Choose an age interval with a fractional year.
2. Complete the four essential Ex 3 tests in `tests/unit/test_data_processing.py`:
   aggregation, fractional age, labels below/at/above the default threshold, and unchanged
   input frames. Extend tiny inputs where needed. Do not calculate expected values by
   calling the same production helper you are testing.
3. Run the focused suite. The negative-quantity placeholder belongs to Ex 5; the tiny
   modeling test belongs to Ex 6. Select today's scope explicitly:

   ```bash
   uv run --locked pytest tests/unit/test_data_processing.py -k "not negative_quantity" -v
   ```

   `NotImplementedError` identifies unfinished tests or functions. An assertion failure
   identifies a mismatch to investigate. Read the actual/expected difference before editing.

**Extensions if time permits:** add tests for the three date repairs, inner join, exact
age-limit equality, a non-default labeling threshold, and repeatable/disjoint splits.
The old customer in the supplied fixture alone cannot prove strict age-limit equality.
You can also begin Ex 6's small modeling test. These additional cases strengthen coverage;
the four essential tests above are the checkpoint needed for Ex 4. Record any uncovered
contract in your notes instead of implying the whole contract has been verified.

**Check:** the completed Ex 3 tests pass before any mutation. Use numeric tolerance where
floating-point representation requires it, not to accept a whole-year age error. A tiny
fixture test proves that contract on its chosen cases, not model quality on future data.
Commit the tests so the next exercise has a known passing checkpoint.

**Break: 10 minutes.**

### Ex 4 — Catch deliberate regressions (20 minutes)

**Start:** passing Ex 3 tests. **Purpose:** show whether tests detect the incident.

1. Change the age division in `prepare_customers` from `/ 365` to `// 365`.
   Run your fractional-age test. Record the test name and the actual failure.
2. If it stays green, inspect the input interval and assertion. Improve the revealing
   test, restore the original function, and establish green before repeating the mutation.
3. Restore the correct division and show green. Then change the target comparator from
   `>` to `>=`. Run the equality-boundary test and record what it detects.
4. Restore the intended comparator and rerun the focused suite. Inspect `git diff` so no
   deliberate bug is carried forward. Explain why merely checking for a nonempty result
   would miss both changes.

**Check:** two observed failures, followed by passing restored tests. Keep evidence and any
improved tests; discard the deliberate implementation changes. The size or direction of an
AUC change is not a required outcome of these mutations.

### Ex 5 — Decide and test invalid-input behavior (20 minutes)

**Start:** restored implementation. **Purpose:** make a behavior change explicit and testable.

`orders_negative.csv` has a valid and a negative-quantity order for the same customer.
Choose one policy: reject input containing a negative quantity, or exclude invalid rows
before aggregation. Describe the reason and what a caller should observe. Decide what
happens when all rows are invalid. Keep this decision distinct from Ex 2's refactor.

1. Write the expected behavior in `notes/session-03.md`.
2. Replace `test_negative_quantity_policy` with tests for that decision and normal orders.
   Show the failing result before changing production code.
3. Implement the policy in `prepare_orders`. Run the completed data-processing tests:

   ```bash
   uv run --locked pytest tests/unit/test_data_processing.py -v
   ```

**Check:** the chosen policy is visible in the function contract and tested, and ordinary
aggregation still passes. If the real project data contains such rows, record any intentional
change from baseline metrics and trace it to this policy. If it contains none, unchanged
metrics remain the expected comparison. Commit this decision separately from extraction.

### Ex 6 — Integrate the runner and quality checks (20 minutes)

**Start:** completed data-processing tests. **Purpose:** prove the assembled command and automate checks.

1. Complete `tests/unit/test_modeling.py` with a tiny deterministic fit and held-out
   evaluation, including an unseen category. Create enough examples in both classes for
   any stratified split; derive checks for metric names/ranges and prediction shape yourself.
   Full raw-CSV training belongs in integration tests. Then follow
   [integration requirements](03_modularization/integration-requirements.md) to
   implement the two integration placeholders. Run against temporary copies of project
   inputs so the check does not replace your working model artifact.
2. Add ignored entries for `.pytest_cache/`, `__pycache__/`, `*.pyc`, `*.egg-info/`,
   `build/`, and `dist/` if missing. Preserve the Session 2 ignores. Raw CSVs remain tracked.
3. Run the checks in this order:

   ```bash
   uv run --locked ruff check .
   uv run --locked ruff format --check .
   uv run --locked pytest tests/unit -q
   uv run --locked pytest tests/integration -q
   uv run --locked python -m highrev
   ```

   Fix formatting locally with `uv run --locked ruff format .`, review the diff, and rerun
   the format check. Review any automatic lint fixes before accepting them.
4. Edit your existing `reproduce.yml` using the requirements. Commit named source, test,
   configuration, note, and workflow paths, then push the working branch for team review.
   Inspect the Actions log. If remote execution is unavailable, record local results and
   mark the remote proof pending rather than calling it verified.

**Check:** all placeholders are replaced, fast checks gate training, explicit invocation
produces metrics and a model, imports are safe, and a reviewer can understand the changes.
Keep the old baseline until the modular execution has been reviewed. Update the project
README to name `uv sync --locked` and `uv run --locked python -m highrev` as the new run path.

## Expected observations and recovery

| Checkpoint | Expected observation | If it differs |
|---|---|---|
| Ex 1 | Baseline runs under the existing lock | Repair missing data or Session 2 environment first. |
| Ex 2, before implementation | Calls to stubs raise `NotImplementedError` | This is unfinished work, not a passing application. |
| Ex 2, after extraction | Command metrics match the same locked baseline | Compare row counts, IDs, feature columns, split, and settings before changing tolerances. |
| Package import | Path points to your team's `src/highrev` | Check build-system settings, remove `package = false`, and run `uv sync --locked`. |
| Ex 3 | Focused completed tests pass | Preserve leading zeros; locate fixture paths relative to the test file; inspect expected values. |
| Ex 4 | Each intentional bug fails a relevant existing test; restoration passes | Use a non-whole-year age and exact threshold equality rather than random inputs. |
| Ex 5 | Normal inputs and explicit invalid-input policy pass | Check whether invalid rows are handled before aggregation. |
| Ex 6 | Unit/integration suites and checks pass; workflow gates training | Check dev dependencies and unfinished placeholders; do not skip a failing check. |
| Stratified split error on tiny data | A class has too few rows | Use a sufficiently large balanced fixture; do not remove stratification from production. |
| TOML duplicate-key error | A configuration table was pasted twice | Merge keys into the existing table. |
| Pickle reload cannot find `_as_str` | Helper lives in an execution-only context | Define it in the importable modeling module and regenerate the model. |

## Wrap-up and next session

- [ ] I can explain each module's responsibility and one function's complete contract.
- [ ] The baseline comparison uses the same data, environment, split, and model settings.
- [ ] Focused tests catch both deliberate regressions and pass after restoration.
- [ ] The negative-quantity policy is documented as an intentional behavior change.
- [ ] Imports are safe; explicit execution connects the functions and persists a usable model.
- [ ] Ruff, unit tests, and integration checks run before training in our workflow.
- [ ] My notes distinguish observed local results from any pending remote verification.

Session 4 assumes importable preparation and modeling functions, explicit I/O in the runner,
passing behavior tests, and a locked environment. If unfinished, complete extraction and
the age/threshold/aggregation tests first, then integration and the workflow. Tell the
instructor which checkpoint remains open; do not copy a completed solution to hide it.

Optional individual preparation is ungraded and stays outside the team repository: sketch
the dependency graph of your functions and consider where file paths and parameters should
live when a pipeline orchestrator takes over. Compare the role of a Python function and a
pipeline node. No separate homework submission is required.

## Reading

- [pytest assertions](https://docs.pytest.org/en/stable/how-to/assert.html): expressing
  expected values and exceptions.
- [uv project configuration](https://docs.astral.sh/uv/concepts/projects/config/): how a
  build system makes the local package installable.
- [setuptools package discovery](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html):
  the `src/` layout and package discovery settings.
- ASI 3 deck and Examples 1 to 3, as selected in the teacher's opening discussion.

Project scope lives in [PROJECT.md](../PROJECT.md); grading and contribution evidence are
defined only by the [final project rubric](../FINAL_PROJECT_RUBRIC.md).
