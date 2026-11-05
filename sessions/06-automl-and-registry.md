# Lab 06 - AutoML, model registry and promotion

Your Lab 05 pipeline can identify a training run, but a consumer still needs to know which model is approved. In this individual lab, compare a fixed baseline with a bounded PyCaret search, track both in MLflow, register models, apply a promotion policy, and restore a previously approved version. A final held-out audit happens only after the choice is fixed. The local SQLite store below is a classroom substitute for an MLflow server, not a shared deployment service.

## Before class

Start with your own working Lab 05 exercise project, including `data/01_raw/customers.csv`, `data/01_raw/orders.csv`, `src/highrev/modeling.py`, `uv.lock`, and its working Python environment. The data must match its DVC pointer. Record the actual Git commit and DVC directory hash; do not copy identifiers from an example. Make sure your working tree and data are in the intended state, and retain any existing work. Python 3.11 and `uv` are needed for the separate PyCaret worker; the project environment continues to run Kedro. Internet access or a populated uv cache is needed for the initial worker sync.

The [starter](06_automl_registry/starter/) includes worker and registry plumbing, a locked worker environment, a configuration helper, and tests. Each student implements the three functions in the two `learning_tasks.py` files independently. The supplied code retains multiple rows per customer, assigns whole customers to partitions and folds, measures row-weighted ROC AUC, and keeps the test partition out of training input. This prevents repeated-customer overlap; it does not prove that all features are available at production prediction time.

## Preparation - copy the starter and complete the small functions

Use Bash on Linux/macOS or Git Bash on Windows. In Git Bash, use paths such as `/d/course/ASI`; in WSL, create Linux environments rather than reusing Windows virtual environments. The helper selects `bin/python` or `Scripts/python.exe` as appropriate. In Bash, set `$course` to your course checkout and `$project` to your separate exercise checkout. Verify both paths before copying; the destination must not already exist. Do not copy into the course checkout or a team project.

```bash
set -euo pipefail
course='/path/to/highrev-mlops-course'
project='/path/to/your-exercise-project'
test -f "$project/src/highrev/modeling.py"
test -f "$project/data/01_raw/orders.csv"
lab="$project/lab06"
if [[ -e "$lab" ]]; then
    printf 'lab06 already exists; preserve it and use a new exercise checkout.\n' >&2
    exit 1
fi
cp -R "$course/sessions/06_automl_registry/starter" "$lab"
source "$lab/shell_helpers.sh"
project_python=$(venv_python "$project/.venv")
export PYTHON_BIN="$project_python"
cd "$lab/worker-env"
uv sync --locked --python 3.11
worker_python=$(venv_python "$lab/worker-env/.venv")
cd "$project"
if ! "$worker_python" -m unittest discover -s "$lab/tests" -v; then
    printf 'Inspect the errors: only the three TODO NotImplementedError failures are expected initially.\n'
fi
```

The initial three `NotImplementedError` results are intentional. Implement `comparison_options` and `log_validation_metrics` in `lab06/lab06_worker/learning_tasks.py`, and `gate_reasons` in `lab06/src/highrev/lab06/learning_tasks.py`. Read their docstrings and the tests. For PyCaret, the budget is in minutes; `sort='AUC'`, `n_select=1`, and `errors='raise'` make the selection explicit. Log the supplied metrics with MLflow. The gate must check absolute AUC, permitted regression against an existing champion, model size, and p95 latency. Rerun the test command until all three tests pass, and add your own boundary test. These tests do not establish that the whole workflow works.

## L06-E1 - Define the prediction contract

Write down what one request represents, when prediction happens, which seven features are available then, and what `high_revenue` means. In this classroom dataset revenue is historical and pages visited comes from orders. Serving these prepared records does not establish that the features are available for a brand-new customer. A future-revenue service would need observation and target windows defined before training.

Inspect `src/highrev/lab06/protocol.py`: whole customers, not individual rows, are assigned to outer partitions and inner folds. Explain why duplicated customer records must remain together. Completion: record feature names, target meaning, observation-time limitation and the distinction between CV, validation and final test.

## L06-E2 - Train and track the baseline

The command below runs the complete baseline and PyCaret comparison. First identify the baseline run and its validation evidence; interpret the AutoML part in L06-E3. MLflow groups attempts in an experiment. A run stores settings and results; a logged model contains fitted preprocessing and the predictor. Autologging is useful, but common explicit metrics make the two candidates comparable.

Set the actual commit and DVC hash from your project. Inspect `data/01_raw.dvc` and use its directory `md5` value, including `.dir`. `$run` must be a new directory outside the project; choose another name if it already exists. Review your `max_age` and revenue threshold in `conf/base/parameters.yml` and adjust the generated config if your project uses different values. The generous policy values are demonstration values, not production thresholds.

```bash
cd "$project"
commit=$(git rev-parse HEAD)
cat data/01_raw.dvc
data_hash='replace-with-the-actual-md5.dir'
run="$(dirname "$project")/lab06-run-01"
bash "$lab/new_config.sh" "$project" "$run" "$commit" "$data_hash"
config="$run/config.json"
cat "$config"
# Edit preparation values and policy limits with your preferred text editor.
export PYTHONPATH="$(native_path "$lab/src")"
export MLFLOW_DISABLE_AGENT_HINT=1
export PYTHONUTF8=1
cd "$run"
"$project_python" -X utf8 -m highrev.lab06 run --config "$config"
```

Wait for completion before continuing. Inspect `comparison/protocol.json`, `membership.csv`, `comparison.json`, each candidate report, and worker logs. Record the comparison ID and both run IDs. Explain why the baseline and PyCaret have the same protocol ID and why the test rows do not appear in `training-input/`. Compare validation AUC, model bytes and p95 latency; a higher AUC does not by itself establish a better deployment choice. The budget bounds the search but is not a strict wall-clock deadline for every operation.

If a run fails, read its worker log and correct the cause. Keep the failed directory as evidence; create a new `$run` and config rather than overwriting it. A missing worker dependency requires completing the locked sync, not installing packages into the project environment. Provenance hashes are checked before and after training; do not edit input files during the run.

## L06-E3 - Compare models with AutoML

Open the PyCaret leaderboard and candidate report. `compare_models(include=["lr", "dt"], sort="AUC", budget_time=5)` searches two algorithm families with a bounded budget. `pull()` captures the most recent comparison table. This search ranks inner-fold scores; outer validation is measured only after selection. No final test enters search.

Compare the baseline and selected candidate using the same validation metric, protocol ID, fit rows, prediction batch size and runtime. Record validation AUC, model size and p95 latency in a two-row table. Explain one tradeoff. `compare_models` compares model families; `tune_model` would add a separate hyperparameter search and is optional. AutoML does not define your target, prevent all leakage or decide the serving budget.

Completion: identify the selected family, distinguish CV AUC from validation AUC, and justify whether a small score gain is worth additional resources. If the search fails, inspect `pycaret.log` and keep the failed run before starting a fresh directory.

## L06-E4 - Approve and pin a model version

The CLI uses the candidate's returned MLflow model URI and verifies its completed run and report. A model version is immutable; the `champion` alias is a movable pointer. A policy decides whether the pointer may move. From `$run`, in the same Bash terminal:

```bash
"$project_python" -X utf8 -m highrev.lab06 register --config "$config" --framework baseline
"$project_python" -X utf8 -m highrev.lab06 promote --config "$config" --framework baseline --decision "$run/baseline-decision.json"
"$project_python" -X utf8 -m highrev.lab06 promote --config "$config" --framework pycaret --decision "$run/pycaret-decision.json"
cat "$run/baseline-decision.json"
cat "$run/pycaret-decision.json"
```

Record the actual versions and whether each decision was approved. The first registration is idempotent. For a rejection exercise, choose a fresh decision filename, temporarily set `max_artifact_bytes` to `0` in the config, and try to promote a candidate: the decision should be rejected and the champion should remain unchanged. Restore the policy before continuing. Explain why registration does not itself mean approval. Decision files cannot be reused. If a pending decision remains after an error, inspect the registry and decision record before attempting recovery; this classroom implementation assumes one writer and does not provide atomic distributed alias updates.

## L06-E5 - Serve the model and call it from a notebook

The registry stores artifacts. FastAPI hosts one selected artifact and accepts JSON requests. The server loads once at startup and returns its immutable model URI with every response. Use the approved version from your decision record; do not assume it is version 1 or 2.

Open a second Bash terminal and redefine `$project`, `$lab`, `$run` and `$config` using your actual absolute paths. Start the service in the worker environment:

```bash
set -euo pipefail
project='/path/to/your-exercise-project'
lab="$project/lab06"
run='/path/to/lab06-run-01'
config="$run/config.json"
source "$lab/shell_helpers.sh"
worker_python=$(venv_python "$lab/worker-env/.venv")
export PYTHON_BIN="$worker_python"
decision="$run/pycaret-decision.json"
if [[ "$(json_get "$decision" status)" != approved ]]; then
    printf 'Choose an approved decision first.\n' >&2
    exit 1
fi
export LAB06_TRACKING_URI="$(json_get "$config" tracking_uri)"
model_name=$(json_get "$config" model_name)
version=$(json_get "$decision" version)
export LAB06_MODEL_URI="models:/$model_name/$version"
export PYTHONPATH="$(native_path "$lab")"
export MLFLOW_DISABLE_AGENT_HINT=1
"$worker_python" -m uvicorn lab06_worker.serve:app --host 127.0.0.1 --port 8016
```

Wait for startup success. Open `http://127.0.0.1:8016/docs` to inspect the schema. Open [Call_the_model_API.ipynb](06_automl_registry/Call_the_model_API.ipynb) and run its cells from any notebook environment with `requests`. The notebook sends features, not target labels or a Python model object. Verify one probability per row and the exact version in the response. An empty batch or an extra target field should receive HTTP 422.

Completion: save one request, its response, the model URI and an expected schema failure. If connection is refused, check the server terminal and URL. If startup fails, inspect the tracking URI, model version and environment. Do not install PyCaret into the project environment. Stop this server with Ctrl+C; avoid leaving extra demo processes running.

This is local hosting only. Public hosting later needs a deployable image/environment, artifact access, HTTPS, authentication, resource limits and monitoring. Multiple service processes each load their own model. A notebook HTTP call is a client integration check, not a load or production-readiness test.

## L06-E6 - Rehearse rollback and perform the final audit

In the original project terminal, restore its variables and `PYTHONPATH` if needed. Use the version from the baseline approval, not a guessed version:

```bash
source "$lab/shell_helpers.sh"
project_python=$(venv_python "$project/.venv")
export PYTHON_BIN="$project_python"
export PYTHONPATH="$(native_path "$lab/src")"
version=$(json_get "$run/baseline-decision.json" version)
"$project_python" -X utf8 -m highrev.lab06 rollback --config "$config" --version "$version" --decision "$run/rollback.json"
```

The alias now points to the approved baseline, but a running API still has its previous model. In the server terminal, stop the service, set `LAB06_MODEL_URI` to the baseline's immutable URI, and restart. Repeat the notebook request and check the returned URI. Probabilities need not differ for every input; version identity is the decisive check.

After the choice is frozen, perform one final audit in the original terminal:

```bash
"$project_python" -X utf8 -m highrev.lab06 audit --config "$config"
cat "$run/comparison/audit-result.json"
```

The audit writes `test-consumed.json` before loading held-out data. It evaluates the exact version and refuses a second audit, including after an error that might expose test results. Lifecycle commands then refuse further selection for this comparison. Do not delete the marker to choose another model based on test results. Preserve an audit failure and investigate it instead.

Completion: record registry rollback, service restart, changed served URI and one final audit (or an honest failure record). Keep code, tests and your own explanations. Keep worker virtual environments, caches and run directories outside Git. Commit the worker lock and source, not the SQLite database.

## Exit check

Explain what AutoML automated, what MLflow recorded, which rule approved a model, and how FastAPI loaded that artifact. Identify the notebook's role as an HTTP client. Describe the difference between alias rollback and serving rollback, and why no test-driven reselection is permitted. Lab work is individual and these checks are ungraded; the [project rubric](../FINAL_PROJECT_RUBRIC.md) remains the grading authority. The next serving lesson can extend this local API into a deployable service.
