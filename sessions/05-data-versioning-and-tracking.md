# Session 05 — Data versioning and experiment tracking

## Incident and goal

A teammate says last week's HighRev model had a higher ROC AUC. The pipeline
still runs, and the code is in Git, but the team cannot establish which data
and settings produced that score. Your job is to assemble the evidence needed
to investigate. Each exercise supplies a piece of the puzzle; keep your own
observations on the [checklist](05_tracking/checklist.md).

By the end you can identify the code, raw data, configuration, metrics and model
associated with a run; retrieve a previous dataset in a separate clone; compare
controlled experiments; and explain the limits of a reproduction attempt. This
is individual, ungraded lesson work. The separate [final project rubric](../FINAL_PROJECT_RUBRIC.md)
governs project assessment.

## Before class

You need Git, Python 3.12, uv, and your own Session 04 exercise repository with
a working full Kedro pipeline. It must read `data/01_raw/orders.csv` and
`data/01_raw/customers.csv`, use the base `model_options.C` in training, and
save `data/08_reporting/metrics.json` and `data/06_models/classifier.pickle`.
If your paths or graph differ, resolve them with the instructor before using the
supplied adapter. Restore the default target threshold and finish any missing
Session 04 wiring first. Configure a local Git identity if you have not already.

Update your separate course checkout and inspect the [asset list](05_tracking/README.md),
[API cards](05_tracking/api-cards.md), and [ignore snippet](05_tracking/gitignore-snippet.txt).
Do not initialize DVC inside the course checkout or the full reference project.
Install and lock DVC and MLflow in **your exercise project**, then sync:

```bash
uv add "dvc==3.67.1" "mlflow==3.16.1"
uv sync --locked
uv run --locked dvc --version
uv run --locked python -c "import mlflow; print(mlflow.__version__)"
uv run --locked kedro run
git status --short
```

Retain your existing HighRev pipeline dependencies and review the resulting
lockfile; resolve dependencies before class while package access is available.
Commands below use Bash (Git Bash on Windows, as in earlier sessions) from your
exercise project root. Do not run these commands in the course checkout. Run
existing tests and fix a broken baseline before continuing. Shell variables such
as `$exercise_root` last only for the current terminal; if you open a new one,
set them again from the values you recorded.

## Puzzle pieces

| Component | What it contributes | Boundary |
| --- | --- | --- |
| Git | Code, configuration and DVC pointer history | Does not itself retain DVC data objects. |
| DVC | A content reference and storage/retrieval of raw input bytes | In this lesson Kedro, not DVC, executes the graph. |
| Kedro | The existing processing, training and evaluation graph | Running it does not itself provide a history of experiments. |
| MLflow | Experiments containing runs, parameters, metrics, tags and artifacts | Records evidence; does not automatically reproduce a run. |

A DVC pointer is small metadata committed to Git. The local cache stores data
objects; a remote stores shareable copies. A local-directory remote is adequate
for this exercise, but it is not a cloud service or an independent backup unless
you manage it as one. An MLflow experiment groups runs. A parameter describes a
choice, a metric a measured result, a tag identifies context, and an artifact
is a produced object such as a classifier or report. Tracking training runs is
not monitoring a deployed service.

The instructor demonstrates;
you carry out each checkpoint individually in your exercise repository.

## Ex 1 — Find missing evidence

**Purpose:** understand the incident before adding tools. **Start:** working
Session 04 pipeline.

1. Inspect the catalog, `conf/base/parameters.yml`, pipeline graph, and your
   last model and metrics. Identify the two raw files, split settings, seed,
   model configuration and saved outputs.
2. Copy the [checklist](05_tracking/checklist.md) to
   `notes/session-05.md` or keep a separate scratch copy. List what is missing
   when a colleague has only a Git commit and a reported score.
3. Explain why the current terminal output and saved model do not uniquely
   describe the original data and full execution.

**Check:** trace raw data to an evaluation metric and identify at least code,
data, effective configuration, environment and result as evidence needed.

## Ex 2 — Version/publish V1

**Purpose:** give the current raw data a recoverable identity. **Start:** Ex 1;
Git project with the raw files present.

1. Inspect `git status --short` and `git ls-files -- data/01_raw`. Preserve any
   existing work. If the raw files are tracked by Git, remove **only their Git
   index entries**, retaining local files:

   ```bash
   git rm -r --cached -- data/01_raw
   ```

   Skip that command if `git ls-files` lists nothing. Verify both CSVs still
   exist. If DVC has not been initialized in this individual project, run
   `uv run --locked dvc init`; otherwise inspect its existing configuration
   and do not reinitialize. Do not overwrite an existing data pointer.
2. Before tracking, replace any broad `data/` ignore rule with the specific
   generated-output rules in the [ignore snippet](05_tracking/gitignore-snippet.txt).
   A broad rule prevents DVC creating its pointer; force-adding a pointer later
   cannot fix that initialization error. Track `data/01_raw`, inspect `data/01_raw.dvc` and the generated ignore rule:

   ```bash
   uv run --locked dvc add data/01_raw
   cat data/01_raw.dvc
   git status --short
   ```

   The pointer hash identifies the directory's data objects. It is not the
   same thing as a checksum for either individual CSV.
3. Create a local remote outside this repository. The following commands put
   it next to your project. `--local` keeps the machine-specific path in local
   DVC configuration; it must be set separately in another clone. `pwd -W`
   prints Git Bash's Windows form of a path (`D:/...`), which DVC and MLflow
   expect on Windows; on Linux/macOS the plain `pwd` is used.

   ```bash
   native_path() { (cd "$1" && { pwd -W 2>/dev/null || pwd; }); }
   exercise_root=$(native_path .)
   mkdir -p ../highrev-dvc-remote
   dvc_remote=$(native_path ../highrev-dvc-remote)
   echo "$exercise_root" "$dvc_remote"
   uv run --locked dvc remote add --local -d lesson05 "$dvc_remote"
   uv run --locked dvc push
   ```

   Stage and commit DVC's generated pointer and ignore changes, plus your
   dependency changes (substitute paths if your project differs):

   ```bash
   git add -- .dvc .gitignore data/01_raw.dvc pyproject.toml uv.lock
   if [[ -f .dvcignore ]]; then git add -- .dvcignore; fi
   if [[ -f data/.gitignore ]]; then git add -- data/.gitignore; fi
   git status --short
   git diff --cached
   git commit -m "Track HighRev raw data V1"
   v1_commit=$(git rev-parse HEAD)
   echo "$v1_commit"
   ```

   The conditional commands include only ignore files that exist. Inspect staged changes: do not commit data bytes, local cache,
   local remote configuration or credentials. Record the V1 hash and commit.
4. Keep `reproduce.yml` honest. The GitHub runner now checks out the pointer
   but not the CSVs, and it cannot reach your local remote, so the Session 4
   Kedro integration test and `python -m highrev` would fail there. The Session
   3 workflow test builds its data from `tests/fixtures/` and still runs. In
   `.github/workflows/reproduce.yml`, replace the last two steps
   (`Integration tests` and `Train through the modules`) with:

   ```yaml
         - name: Integration tests that use committed fixtures
           run: uv run --locked pytest tests/integration -q --ignore=tests/integration/test_kedro_pipeline.py
         - name: Say which checks need the DVC-managed raw data
           if: hashFiles('data/01_raw/orders.csv') == ''
           run: echo "::warning::data/01_raw is managed by DVC and absent on this runner; the Kedro integration test and python -m highrev did not run here."
         - name: Integration tests that need the raw data
           if: hashFiles('data/01_raw/orders.csv') != ''
           run: uv run --locked pytest tests/integration/test_kedro_pipeline.py -q
         - name: Train through the modules
           if: hashFiles('data/01_raw/orders.csv') != ''
           run: uv run --locked python -m highrev
   ```

   Keep the indentation of the existing steps. Locally, where the data exist,
   run the full set as before: `uv run --locked pytest tests/integration -q`
   and `uv run --locked python -m highrev`. Commit the workflow with
   `git commit -m "Keep reproduce green without raw data in Git" -- .github/workflows/reproduce.yml`.
   `$v1_commit` stays the pointer commit recorded above. The warning is a
   recorded gap, not a pass: Lab 07 restores approved data copies on the runner
   so the full pipeline runs in CI again.

**Check:** DVC reports the push completed, Git tracks the pointer rather than
raw files, and the raw files remain usable. The pointer without retained remote
objects cannot recover lost data. Keep the remote for later steps.

## Ex 3 — Restore V1 in independent clone

**Purpose:** test retrieval without depending on the original cache. **Start:**
V1 committed and pushed.

1. Record the V1 commit and the SHA-256 of each original CSV. Clone your local
   exercise repository into a new sibling path; do not clone into the project
   itself. The clone is disposable and its destination must not already exist.

   ```bash
   git rev-parse HEAD
   sha256sum data/01_raw/orders.csv data/01_raw/customers.csv
   clone_root="$(dirname "$exercise_root")/highrev-lesson05-clone"
   test ! -e "$clone_root" || echo "$clone_root already exists: choose another name"
   git clone --no-local "$exercise_root" "$clone_root"
   cd "$clone_root"
   ```
2. In the clone, configure its own `lesson05` local remote pointing to the
   same `$dvc_remote`, then pull:

   ```bash
   uv sync --locked
   uv run --locked dvc remote add --local -d lesson05 "$dvc_remote"
   uv run --locked dvc pull
   sha256sum data/01_raw/orders.csv data/01_raw/customers.csv
   ```

   The clone's DVC cache is separate. Compare hashes and pointer with the
   original. Return with `cd "$exercise_root"` for the next exercise.

**Check:** both files and hashes agree, and the pull succeeded in the fresh
clone. This establishes local recovery from that remote, not an off-machine
backup or a full software/environment reproduction.

## Ex 4 — Connect MLflow

**Purpose:** record what the existing pipeline did, without changing its nodes.
**Start:** Ex 3 complete; work in the original exercise project.

**Hard stop before the first tracking command:** the V1 DVC pointer must be
committed to Git, the V1 objects must have been pushed to the configured DVC
remote, `dvc status` must be clean, and `git status --short` must show no
changes. Check the pointer explicitly:

```bash
git ls-files --error-unmatch data/01_raw.dvc
uv run --locked dvc status
git status --short
```

If the first command fails, return to Ex 2 and commit the pointer. If the DVC
status reports changes, restore or re-track the intended data before proceeding.
The adapter creates an MLflow run before validating provenance so failures are
visible. Therefore, a printed run ID alone does not mean the run succeeded;
check its final status and the command exit code. Stop after any failed run and
fix that cause before trying again.

1. Copy the adapter, support module and tools to the exact destinations in the
   [asset list](05_tracking/README.md). Merge the supplied ignore snippet into
   `.gitignore`, preserving existing rules. Inspect the adapter and the
   [API cards](05_tracking/api-cards.md).
2. Complete its three TODO functions: `record_parameters(params, overrides)`,
   `record_metrics(metrics, metrics_path)` and `record_model(model)`. The last
   returns the MLflow model info. Use the supplied values; do not manually
   invent a configuration or hardcode the metric. Explain what each piece
   records and why. The supplied driver handles run lifecycle; the support module verifies
   provenance and records the environment. Use the model logging card's supplied requirements and
   code paths so the artifact can include the HighRev code it needs.
3. Commit all source, assets, configuration, ignores and `uv.lock` before A.
   Record observations outside the repository until after B, or commit them
   before A. Verify `git status --short` and save the commit ID. Run A:

   ```bash
   uv run --locked python -m highrev.track_run --name A-baseline
   ```

4. Start the local UI in a separate terminal from the exercise root:

   ```bash
   uv run --locked mlflow ui --backend-store-uri sqlite:///mlflow.db --workers 1
   ```

   Open the displayed local URL. In experiment `highrev-lesson-05`, inspect A's
   status, parameters, metrics, tags `git.commit` and `dvc.data_hash`, and the
   `classifier` model artifact. Use the supplied inspector with A's actual ID:

   ```bash
   uv run --locked python tools/inspect_run.py --run-id "REPLACE_WITH_RUN_ID"
   ```

   Replace `REPLACE_WITH_RUN_ID` with the ID printed by the adapter. Stop the UI with
   Ctrl+C when finished. Do not commit `mlflow.db` or generated artifacts.

**Check:** A completed successfully; the displayed commit and data reference
match actual project state and the effective parameter values match what was
used. The metric and model appear in the run, not just in terminal output.

## Ex 5 — Compare A/B/C

**Purpose:** interpret a controlled comparison. **Start:** A recorded; same
clean commit and V1 data still selected.

| Run | Data | Model configuration | Comparison question |
| --- | --- | --- | --- |
| A | V1 | Base C | Baseline |
| B | V1 | C = 0.1 | What changes with C? |
| C | V2 | Base C | What changes with data? |

1. Run B without changing code or the data and record its ID:

   ```bash
   uv run --locked python -m highrev.track_run --name B-parameter --c 0.1
   ```

   If your base C is already 0.1, choose a different valid C and document it.
   Check that A and B share the same commit, data hash, seed and evaluation
   settings. Only then record observations in your notes and commit the notes
   before C, so they do not make provenance ambiguous.
2. Use the supplied `tools/make_v2.py` to remove every tenth order once; inspect
   its repeat guard and the actual changed file. `$v1_commit` is the V1 commit
   saved in Ex 2; if you opened a new terminal, set it to that recorded commit.
   The helper rejects a mismatched pointer or dirty data, so it cannot silently
   apply the change twice. The customer table, column
   schema, split seed, target definition and base configuration remain fixed.
   Update the DVC pointer, push V2, commit the pointer, and run C:

   ```bash
   uv run --locked python tools/make_v2.py --v1-ref "$v1_commit"
   uv run --locked dvc add data/01_raw
   uv run --locked dvc push
   git add data/01_raw.dvc
   git commit -m "Record data version V2"
   uv run --locked python -m highrev.track_run --name C-data
   ```

   Record C's ID, commit and pointer hash. Compare the runs in the UI and with
   `uv run --locked python tools/inspect_run.py --run-id <A_ID> --compare <B_ID>`.
   Inspector results are JSON on stdout. Inspect A vs C too. Capture actual values rather than expecting specific
   scores. The inherited row-based split can also place repeated customer IDs
   in both partitions; production evaluation needs a customer/time-aware design.
   V2 can change the composition of the evaluation sample, so its score
   difference alone is not proof that the training data caused improvement.

**Check:** A/B have the same commit and data hash but different C; A/C have
the same base model settings and different data references. The C commit must
contain the V2 pointer. Note all other changed commit contents honestly.

## Ex 6 — Reproduce a run and inspect failure

**Purpose:** follow the evidence backward and distinguish failed execution
from a successful run. **Start:** A/B/C recorded, V1 and V2 pushed.

1. Choose A. Inspect its run ID, `git.commit`, `dvc.data_hash`, effective
   configuration, environment and metric. In the independent clone, select
   the **run's Git commit** (not the earlier V1 pointer commit, which may not
   contain the tracking adapter). Ensure local edits are saved before checkout.
   The clone was created before the integration commit: fetch the new Git
   objects first, then synchronize the environment and data. Replace the quoted
   value with A's actual `git.commit` tag:

   ```bash
   cd "$clone_root"
   git status --short
   git fetch origin
   git switch --detach "REPLACE_WITH_A_GIT_COMMIT"
   uv sync --locked
   uv run --locked dvc pull data/01_raw.dvc
   sha256sum data/01_raw/*.csv
   uv run --locked python -m highrev.track_run --name A-reproduced
   ```

   Verify the pointer and hashes against the chosen run. Use the same effective
   settings, including any runtime override if reproducing B instead of A. The clone has its own `mlflow.db`; inspect its run
   there and compare with the original using `--tracking-uri` and
   `--compare-tracking-uri` when inspecting across stores:

   ```bash
   cd "$exercise_root"
   clone_uri="sqlite:///$clone_root/mlflow.db"
   uv run --locked python tools/inspect_run.py --run-id "A_RUN_ID" --compare "REPRODUCED_RUN_ID" --compare-tracking-uri "$clone_uri"
   ```

   The inspector reports `reproduction_matches` only when finished status,
   commit, data, parameters and metric tolerance all agree. Compare the original and reproduced metric using a
   stated absolute tolerance (start with `1e-8` on the same environment).
   Explain any difference rather than asserting success if the tolerance fails.
2. In the disposable clone, demonstrate a provenance failure before training.
   Unprotect the CSV so a linked workspace file cannot damage the DVC cache,
   append a deliberately invalid line, then invoke the adapter:

   ```bash
   cd "$clone_root"
   uv run --locked dvc unprotect data/01_raw/orders.csv
   echo 'deliberate invalid row' >> data/01_raw/orders.csv
   uv run --locked python -m highrev.track_run --name deliberate-failure
   # Expected: nonzero exit and a printed run ID. Inspect that ID.
   uv run --locked python tools/inspect_run.py --run-id "FAILED_RUN_ID"
   # Only after confirming this deliberate edit is the sole data change:
   uv run --locked dvc checkout --force data/01_raw.dvc
   uv run --locked python -m highrev.track_run --name recovered
   ```

   Inspect the corresponding run status and error; restore the input immediately with
   DVC and verify a subsequent normal run. An unrelated setup failure before
   the run starts does not prove failed-run tracking. Never remove the remote.
3. Answer the three questions at the end of the checklist. Save your notes
   and commit them only after finishing the controlled A/B comparison.

**Check:** the run commit and data reference lead to recoverable inputs; the
rerun's result is compared under stated conditions; the intended failed run is
visible as failed and recovery works. Same-machine evidence does not prove
cross-platform equivalence, an external backup, or production readiness.

Before leaving Ex 6, fetch/switch the clone to C's recorded commit and pull
its data; verify V2 too. Preserve work before switching. Keep the original
exercise project at its latest committed state.

## Troubleshooting and handoff

| Symptom | First action |
| --- | --- |
| Git checkout refuses due to local changes | Save or commit your work; switch versions in the disposable clone. Do not discard work blindly. |
| Windows DVC site-cache access denied | `export DVC_SITE_CACHE_DIR="$(dirname "$exercise_root")/dvc-site-cache"`, then retry. This is separate from `.dvc/cache`. |
| DVC cannot find an object | Confirm the intended remote, that the version was pushed, and that the object still exists. A pointer alone cannot restore missing bytes. |
| Data were edited after `dvc add` | Update the pointer and push, or restore the intended version; verify before running. |
| No run appears in the UI | Check working directory, experiment name, and that UI and adapter use the same SQLite store. |
| Missing metrics or artifact | Check run status and pipeline outputs; a failed pipeline is not a successful model. |
| Different metric after reproduction | Compare actual data, parameters, seed, environment and evaluation first; record the difference and tolerance. |
| V2 script refuses to run | Its guard prevents applying the modification twice. Restore known V1 in a clean disposable workspace before repeating. |

Keep code, configuration, lockfile, DVC metadata, and your notes in your
individual Git history; keep raw data objects in the remote. Retain the local
tracking store for investigation. The next session can assume a runnable Kedro
project with explicit dataset versions and experiment runs; record incomplete
checks so they can be recovered. Optional ungraded individual research: compare
a local MLflow tracking store with a shared service and explain what changes
for access, retention and backups.

Read further: [DVC documentation](https://doc.dvc.org/start),
[MLflow Tracking](https://mlflow.org/docs/latest/ml/tracking/), and
[Kedro documentation](https://docs.kedro.org/).
