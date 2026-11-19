# Lab 08 — Data drift, model drift and the retraining signal

## Incident and goal

"A dashboard said *data drift* on Tuesday. The team retrained on Wednesday and
quality got worse. On Thursday a column went missing and nothing fired."

Your Lab 07 model is deployed, and nobody watches it. In this individual,
ungraded lab you add monitoring to your own exercise project. You will check
every batch of new data against the data the model was trained on, score the
model once the true outcomes arrive, and decide with three tests whether
retraining is justified. Then you run a ladder of simulated incidents and find
out which check notices which problem, and which problems no check notices.

By the end you can:

1. name the monitoring layer that can observe a given incident;
2. explain a schema check and an Evidently drift report, and the limits of both;
3. score batches against delayed labels and explain why accuracy hides a ROC AUC drop;
4. implement the hard, parametric and IQR retraining tests and explain their weaknesses;
5. defend a retraining rule and say what "retrain" means in your project.

Keep your observations in `notes/session-08.md`, started from the
[incident table](08_monitoring/incident-table.md). The
[final project rubric](../FINAL_PROJECT_RUBRIC.md) governs project grading
(dimension 7 covers monitoring); the [checklist](08_monitoring/checklist.md) at
the end is not graded.

## Before class

You need your own Lab 07 exercise project, in which these pass: the project
tests, the Kedro pipeline and the `lab07` tests. You also need the Lab 06 run
directory that your Lab 07 model was trained from. Lab 08 reads two files from it:
`comparison/training-input/fit.csv`, the rows the model was fitted on, and
`comparison/training-input/validation.csv`, rows it never fitted. The model to
monitor is `lab07/model/` with its `lab07-model.json`. Nothing in this lab
trains, registers, deploys or pushes a model.

Commands are Bash (Git Bash on Windows, as in Lab 07). Set the three paths from
Lab 07 again in every new terminal; replace them with your own absolute paths:

```bash
course='/path/to/highrev-mlops-course'
project='/path/to/your-exercise-project'
run='/path/to/your-lab06-run'
cd "$project"
test -f lab07/model/lab07-model.json && echo "model ok"
test -f "$run/comparison/training-input/fit.csv" && echo "fit ok"
test -f "$run/comparison/training-input/validation.csv" && echo "validation ok"
git status --short
```

All three checks must print `ok`. `git status --short` should print nothing;
commit or put aside unfinished work first. Update your course checkout and read
the [asset list](08_monitoring/README.md).

Install the lab while package access is available, before class. Each step
refuses to overwrite something you already have:

```bash
cd "$project"
test ! -e src/highrev/monitoring || echo "STOP: src/highrev/monitoring exists; inspect it first"
test ! -e lab07/lab07/score_batches.py || echo "STOP: score_batches.py exists; inspect it first"
starter="$course/sessions/08_monitoring/starter"
cp -R "$starter/src/highrev/monitoring" src/highrev/
cp "$starter/tests/unit/test_monitoring.py" tests/unit/
cp "$starter/lab07/lab07/score_batches.py" lab07/lab07/
cp "$starter/lab07/tests/test_score_batches.py" lab07/tests/
cp "$course/sessions/08_monitoring/lab07-provenance/verify_provenance.py" lab07/lab07/
grep -q '^monitoring:' conf/base/parameters.yml \
  || { printf '\n'; cat "$course/sessions/08_monitoring/parameters-snippet.yml"; } >> conf/base/parameters.yml
grep -qx 'data/05_serving/' .gitignore || printf '\n# Lab 08\ndata/05_serving/\n' >> .gitignore
uv add "evidently==0.7.23" "pandas==3.0.6"
```

If a `STOP` line prints, do not copy over it: compare the existing file with the
starter and keep your work. The leading `printf '\n'` keeps the appended block on
its own line even when your `parameters.yml` has no final newline.

**Why pandas is pinned.** On 2026-11-18, Evidently 0.7.23 was the newest release.
It fails to import with pandas 3.1, which a fresh resolution picked on that date,
and works with pandas 3.0.6. The same `uv add` therefore pins both. Lab 05 already showed why
exact versions matter for tools whose behaviour later work depends on.

**Why `verify_provenance.py` is replaced.** Your Lab 07 check required the
project's `uv.lock` to equal the lock recorded when the model was trained.
Adding Evidently changes that lock, so the old check would now fail the Lab 07
release workflow on every push. Lineage is recorded once, at training, and
travels with the model: the served model keeps the environment it was built
with (`lab07/uv.lock` and its image). A release gate checks the artifact being
shipped, not today's repository. The replacement fails when the model's
metadata is unreadable, incomplete or malformed, or when the model files' total
size differs from the size recorded at training. That is a size check, not a
content hash: Lab 07 recorded no per-file digest, so a same-size change to a
model file would pass. It reports, without failing, that the project lock has
changed since training. The model only changes when you train and promote a new version.

Readiness check:

```bash
uv run --locked python -c "import evidently, pandas; print(evidently.__version__, pandas.__version__)"
uv run --locked python lab07/lab07/verify_provenance.py
uv run --locked kedro run
uv run --locked pytest tests -q --tb=line
(cd lab07 && uv run --locked python -m pytest tests -q --tb=line)
uv run --locked ruff check . && uv run --locked ruff format --check .
```

Expected: `0.7.23 3.0.6` (a `SyntaxWarning` from inside Evidently on the first
import is harmless). Then `Artifact <your model version> matches its recorded
metadata` with `uv.lock: changed since training`; Kedro completes with the new
parameters; Ruff is clean. Your earlier tests pass. With `--tb=line` every new
failure is one line ending in `NotImplementedError: L08-E2 ...`, `L08-E3 ...` or
`L08-E4 ...`: your tasks (about 19 project tests and 4 `lab07` tests). Skipped are
the optional benchmark test and possibly the `lab07` real-model test, which runs
when `LAB06_RUN` is set or your run directory is `../lab06-run-01` beside the
project. Deprecation warnings from inside Evidently and its dependencies are
expected. Read any other failure before class. Commit the setup:

```bash
git add src/highrev/monitoring tests/unit/test_monitoring.py lab07/lab07 lab07/tests \
  conf/base/parameters.yml .gitignore pyproject.toml uv.lock
git commit -m "Lab 08: monitoring starter, Evidently and pandas pins"
```

**Commit locally; do not push yet.** Your Lab 07 release workflow runs every test on
a push to `main`, so pushing a commit with unfinished TODOs turns it red and blocks
deployment. Push once all tests pass after L08-E4. That push is the first time
Evidently and the new provenance check run in Linux CI. The instructor has not
verified this yet: if the workflow fails, keep the log and report it rather than
changing the workflow.

## Concepts

**Three layers.** Monitoring is not one check.

| Layer | Question | Needs labels? | In this lab |
|---|---|---|---|
| A — service health | Is the service up, fast and answering? | no | Lab 07 `/health`; not repeated here |
| B — inputs | Does new data look like the training data, column by column? Is its structure valid? | no | schema check and Evidently report per batch |
| C — outcomes | Is the model still right once the true outcomes are known? | yes, delayed | ROC AUC per batch and three retraining tests |

**What can go wrong** (the module 6 taxonomy): the input distribution shifts
(*covariate drift*); the label distribution shifts; the schema changes (a column
disappears or gains values); the relationship between features and label changes
(*concept drift*); an upstream data source or upstream model changes. Some of
these change the inputs, some change only the outcomes, and some change both.

**Reference and current data.** A drift check compares a *current* batch with a
*reference*. The right reference is the data the monitored model was fitted on:
here `fit.csv`. Your Kedro `train_set` belongs to the scikit-learn classifier,
not to the AutoGluon model. The simulated serving stream is sampled from
`validation.csv`, rows the model never fitted. Scoring rows the model was
trained on would overstate its quality. The Lab 06 test partition stays untouched.

**Schema versus statistics.** A schema check answers yes or no: are the
expected columns there, numeric where they should be, with known category values?
A broken schema means the batch must not be scored. A drift statistic answers
"how different?" For each column, Evidently computes a distance between the
reference and the current distribution and compares it with a threshold:
normalized Wasserstein distance for numeric columns, Jensen–Shannon distance for
categorical ones. Some columns have an *open domain*: a list of countries grows
naturally, so a new country is reported but is not a schema break, while a new
operating-system value is. `open_domain_columns` in your parameters records that
decision.

**Delayed labels.** `serving.csv` holds what the model sees at prediction time;
`reality.csv` holds the outcome, known days later. Layer C runs only when both
exist. It runs in the AutoGluon environment, where the predictor's runtime lives;
the project environment and the AutoGluon environment exchange only files.

**Why not accuracy.** About 8% of HighRev customers are high revenue (6–11% per
500-row batch). A model
that always says "no" is about 90% accurate. ROC AUC asks whether the model
ranks high-revenue customers above the others, and that is what the business uses.

**Retraining tests** (module 7). Each compares the latest batch's ROC AUC with a rule:

- *hard*: below a fixed floor that the business sets (`roc_auc_floor`);
- *parametric*: below the mean of earlier batches minus `k` sample standard
  deviations. It assumes roughly bell-shaped readings and needs at least three;
- *IQR*: below the lower fence `Q1 - 1.5 × IQR` of earlier batches. It assumes
  no particular shape but needs at least four readings;
- *benchmarking* (optional): below the best value so far. In E4 you work out
  from your clean scores why it would alarm almost every day.

All tests use a strict `<`: a value exactly on the floor or fence does not fire.
Drift alone is evidence for an investigation, not a reason to retrain.

**What "retrain" means here.** A new Lab 06 run directory and export from
current data, `lab07.train` with a new version, scoring that candidate on the
same stream, then the Lab 06 gate decides on promotion. Lab 08 prints these
commands; it runs none of them.

## Resuming after a break

In a new terminal, set `course`, `project` and `run` again
(Before class), `cd "$project"`, and find where you are before running anything:

```bash
git log --oneline -5                     # your last Lab 08 commit names the exercise
ls data/05_serving                       # streams already generated: do not simulate them again
ls data/08_reporting/monitoring          # streams already validated or scored
ls data/08_reporting/monitoring/*/scores.csv data/08_reporting/monitoring/*/retrain_signal.json 2>/dev/null
```

`validate`, scoring and `decide` are safe to repeat; only `simulate` refuses an
existing stream. Continue from the first step of your exercise whose output is missing.

## L08-E1 — The serving stream and the taxonomy

**Purpose:** see what a monitoring system receives before checking it.
**Start:** the setup above is committed. Project root, project environment.

1. Read `src/highrev/monitoring/simulate.py`. Find, for each incident, what it
   changes: `schema`, `covariate`, `category`, `new_category`, `concept`, and the
   optional `corrupt`. Note which ones keep each row's true label attached to the
   row's original features.
2. Generate the clean stream:

   ```bash
   uv run --locked python -m highrev.monitoring simulate --comparison "$run/comparison" --incident none
   ls data/05_serving/none
   head -3 data/05_serving/none/2026-10-01/serving.csv data/05_serving/none/2026-10-01/reality.csv
   ```

3. Copy the [incident table](08_monitoring/incident-table.md) to
   `notes/session-08.md`. For each incident, fill the taxonomy row and the
   layer (B, C, both or neither) you **predict** will notice it.

**Expected result:** ten date folders `2026-10-01` … `2026-10-10`, each with
`serving.csv` (`date,row_id` and the seven features) and `reality.csv`
(`date,row_id,high_revenue` as 0/1), 500 rows each. Your table has predictions,
not results yet.

**Check:** which taxonomy rows can no simulator here produce (for example an
upstream model change)? Why does `concept` keep every column's distribution intact?

**Failure and recovery:** a refusal saying the stream folder already exists
protects an earlier run. Inspect it. To keep it and generate another, pass
`--out data/05_serving/<new-folder>`: the stream is then
`data/05_serving/<new-folder>/<incident>`, and `validate` writes its reports to the
matching `data/08_reporting/monitoring/<new-folder>/<incident>`. Remove a stream only if you created
it and no longer need it. A missing-section error
means `conf/base/parameters.yml` has no `monitoring` block: append the snippet.
**Handoff:** keep the stream folder (ignored by Git) and your predictions.

## L08-E2 — Schema check and drift thresholds

**Purpose:** decide whether a batch may be scored and how far it moved.
**Start:** E1 stream `none`. Project environment.

1. Implement `check_schema(batch, domain, open_columns=())` in
   `src/highrev/monitoring/schema.py`, following its docstring and the
   [API card](08_monitoring/README.md#check_schema). `domain` comes from the
   supplied `reference_domain(fit)`. Return a list of readable problems; an empty
   list means the batch is valid. Ignore `date` and `row_id`.
2. Run its tests, then validate the stream and save one HTML report:

   ```bash
   uv run --locked pytest tests/unit/test_monitoring.py -q -k schema
   uv run --locked python -m highrev.monitoring validate --comparison "$run/comparison" \
     --stream data/05_serving/none --html 2026-10-10
   cat data/08_reporting/monitoring/none/2026-10-10/schema.json
   cat data/08_reporting/monitoring/none/2026-10-10/drift.json
   ```

   Open `data/08_reporting/monitoring/none/2026-10-10/drift.html` in a browser.
3. Look at `drifted` in each day's `drift.json`. On a stream with **no**
   incident, one column is reported as drifted on every day. Find which column,
   its distance, and why a 500-row batch of a column with many rare values sits
   far from a 4,600-row reference. Choose a threshold for that column in
   `conf/base/parameters.yml` (`monitoring.drift_threshold`). It must stop the
   false alarm on clean data and still be low enough to catch a real flood of
   one value. Write the number and your reason in your notes, then validate again.

**Expected result:** `schema.json` has `"ok": true` on every day, and
`unseen_open` lists a few countries absent from `fit.csv` (sample from the
instructor rehearsal: 1–5 rows per day). After your threshold change, clean days
report no drifted column. Validation rewrites its own outputs, so repeating it
is safe; a run without `--html` removes that day's older `drift.html`, which would no
longer match `drift.json`.

**Check:** what does the HTML report show that `drift.json` does not, and what
does neither show? (Hint: labels.) Why is a new country not a schema break
while a new `os` value is?

**Failure and recovery:** `ImportError` or a pandas error inside Evidently: check
that `uv run --locked python -c "import pandas; print(pandas.__version__)"`
prints `3.0.6`. If every day fails the schema check, print `problems`: an
unseen-country problem means the open-domain columns are not passed through.
**Handoff:** commit `schema.py`, your threshold and your notes.

## L08-E3 — Score with delayed labels

**Purpose:** measure the model where its runtime lives, with model identity.
**Start:** E2 validation outputs for `none`. AutoGluon environment, in `lab07/`.

1. Implement `score_batch(predictor, serving, reality)` in
   `lab07/lab07/score_batches.py` (see its docstring and the
   [API card](08_monitoring/README.md#score_batch)). Merge on `row_id` one to one
   and raise `ValueError` with both counts if any row is lost or duplicated.
   Predict with `predictor.predict_proba(frame[FEATURES])[1]`. Return `n`,
   `roc_auc`, `accuracy` (cut at 0.5), `mean_probability` and `positive_rate`.
2. Test and score the stream:

   ```bash
   cd "$project/lab07"
   uv run --locked python -m pytest tests/test_score_batches.py -q
   uv run --locked python -m lab07.score_batches --model model \
     --stream ../data/05_serving/none --reports ../data/08_reporting/monitoring/none
   cd "$project"
   cat data/08_reporting/monitoring/none/scores.csv
   ```

**Expected result:** ten rows with `status` `scored`, ROC AUC between about 0.70
and 0.80 (instructor rehearsal of `lab07-v1`: 0.70–0.80, mean about 0.74; your
model differs), accuracy about 0.9, and filled `model_version`, `protocol_id`,
`git_commit` and `data_hash`. AutoGluon may warn that the model was trained on
Linux or with another Python micro version; read it and continue. Scoring
rewrites `scores.csv`, so repeating it is safe.

**Check:** the clean stream's AUC moves by up to 0.1 between days. What does that
mean for a rule such as "retrain when AUC drops by 0.05"? Why does each score row
carry the model version and commit?

**Failure and recovery:** a row-count error from your merge means the files do
not match; read the counts before changing code. A missing model directory means
the Lab 07 model is absent: restore it from Git (`git status lab07/model`), do
not retrain here. Days marked `skipped: schema` mean E2 found a problem on those days.
**Handoff:** commit `score_batches.py`.

## L08-E4 — Three retraining tests

**Purpose:** turn a history of scores into a defensible decision.
**Start:** E3 `scores.csv` for `none`. Project environment, project root.

1. Implement `hard_test`, `parametric_test` and `iqr_test` in
   `src/highrev/monitoring/retrain.py` (see [API card](08_monitoring/README.md#retraining-tests)).
   The supplied tests cover short histories, values exactly on the floor or fence,
   and a history with no spread.
2. Add one boundary test of your own to `tests/unit/test_monitoring.py`, a case
   the supplied tests do not cover, and say in a comment what it protects.
3. Run the tests and the decision:

   ```bash
   uv run --locked pytest tests/unit/test_monitoring.py -q
   uv run --locked python -m highrev.monitoring decide --reports data/08_reporting/monitoring/none
   ```

   Optional: implement `benchmark_test` and run its test, then count from your
   clean `scores.csv` on how many days it would fire.

**Expected result:** all tests pass; `retrain_signal.json` for `none` says
`"action": "none"` with all three tests false.

**Check:** which test would fire first on a slow decline, and which on a single
sudden drop? Why does the IQR test need four readings? Why does the benchmark
test alarm on clean data?

**Failure and recovery:** a failing boundary test prints the value and the floor
or fence; compare `<` with `<=` and the standard deviation you used (sample,
`ddof=1`). Run `uv run --locked ruff check . && uv run --locked ruff format --check .`
before committing.
**Handoff:** commit `retrain.py` and your test. The incident ladder runs on this commit.

## L08-E5 — Incident ladder and your retraining rule

**Purpose:** test your predictions from E1 and decide what to do.
**Start:** E4 committed (`git status --short` empty), so every score row carries
the commit that produced it.

1. Run the full chain for `schema`, `covariate` and `concept`:

   ```bash
   for incident in schema covariate concept; do
     uv run --locked python -m highrev.monitoring simulate --comparison "$run/comparison" --incident "$incident" &&
     uv run --locked python -m highrev.monitoring validate --comparison "$run/comparison" --stream "data/05_serving/$incident" &&
     (cd lab07 && uv run --locked python -m lab07.score_batches --model model \
        --stream "../data/05_serving/$incident" --reports "../data/08_reporting/monitoring/$incident") &&
     uv run --locked python -m highrev.monitoring decide --reports "data/08_reporting/monitoring/$incident" \
     || { echo "STOPPED at $incident: read the error above" >&2; break; }
   done
   ```

   The `&&` chain stops at the first failing step and names the incident. Fix the
   cause, then finish that incident by hand. The simulator refuses a stream that
   already exists, so start from the `validate` line; run the loop again only for
   incidents that did not start.
2. Fill the result columns of your table. Layer B comes from each day's
   `drift.json` and `schema.json` for days 6–10, layer C from `scores.csv`, and the
   action from the stream's `retrain_signal.json`. Compare them with your predictions.
3. Look at `concept`'s decision day by day. `--until` decides as if that day's
   batch were the latest and writes `retrain_signal_<date>.json` beside the default:

   ```bash
   for day in 2026-10-06 2026-10-07 2026-10-08; do
     uv run --locked python -m highrev.monitoring decide \
       --reports data/08_reporting/monitoring/concept --until "$day"
   done
   ```

   Which tests fire on day 6 and which still fire later? Why do the relative tests
   go quiet once drifted readings are part of the history?
4. Print what retraining would involve, and decide whether you would run it:

   ```bash
   uv run --locked python -m highrev.monitoring act --signal data/08_reporting/monitoring/concept/retrain_signal.json
   ```

5. Write your retraining rule in your notes: which evidence triggers retraining,
   which only an investigation, and what false alarm or missed incident it
   accepts. Commit the notes.

**Expected result** (instructor rehearsal of `lab07-v1`; your numbers differ, the
pattern should not):

| Incident | Layer B, days 6–10 | Layer C, days 6–10 | Action |
|---|---|---|---|
| none | nothing after your E2 threshold | AUC 0.72–0.78 | none |
| schema | `browser` missing: schema break | not scored | investigate |
| covariate | `pages_visited` drifted | AUC 0.68–0.76; no test fires (day-to-day noise) | investigate |
| concept | nothing in the per-column checks | AUC about 0.57–0.62 | retrain |

**Check:** which incident would the Tuesday dashboard have shown, and would
retraining have helped? Which layer caught Thursday's missing column? Why do
per-column checks miss concept drift? (The shuffle does change how columns combine;
a multivariate check could notice that, but only the labels show that the
feature–label relationship broke.)

**Failure and recovery:** a `retrain` action on `none` or `covariate` usually
means a test compares in the wrong direction or the floor is too high; recheck
E4 before changing the rule.
**Handoff:** committed code, tests, parameters and notes. Streams and reports stay
outside Git; delete them when you no longer need them.

## Expected results and troubleshooting

| Check | Expected observation | What it does not prove |
|---|---|---|
| Setup | Evidently 0.7.23, pandas 3.0.6; provenance artifact check passes, lock reported as changed | That the model is still good |
| E1 stream | Ten dated folders, 500 rows, labels separate | That real traffic looks like this |
| E2 schema and drift | Clean days valid; one false-alarm column fixed by your threshold | That the model's predictions are right |
| E3 scores | Ten scored rows with identity; AUC near the Lab 07 validation value | Anything about rows without labels yet |
| E4 tests | Unit tests pass; clean stream gives `none` | That your floor suits the business |
| E5 ladder | Concept quiet in B, loud in C; schema stops C; covariate moves B, no test fires | That retraining would fix the incident |

| Symptom | First action |
| --- | --- |
| `import evidently` fails | Check the pandas pin; rerun the `uv add` line from Before class |
| `verify_provenance.py` fails | Read the `FAIL:` line: a size mismatch (a stray or changed file in `lab07/model/`), or unreadable or edited metadata. Restore the model directory from Git (`git status lab07/model`) |
| Every batch fails the schema check | Print `problems`; check `open_domain_columns` is passed to `check_schema` |
| Every day drifted on one column | That is E2's decision: choose and justify its threshold |
| `Stream ... exists` | Earlier run protected; validate the existing stream or remove only a stream you no longer need |
| Lab 07 tests now fail | Run them from `lab07/`; read whether the failure is in your new `score_batch` |
| Many deprecation warnings in pytest output | They come from inside Evidently's dependencies; read failures, not warnings |
| AutoGluon warnings at load | Model trained on Linux or another Python micro version; expected |

## Exit checklist and next step

Work through the [checklist](08_monitoring/checklist.md). Your project now has a
monitoring package with tests, a scorer in the AutoGluon environment, monitoring
parameters with your thresholds and floor, and a written retraining rule. Next,
Lab 09 runs the API and its dependencies in containers; Lab 10 puts the quality
gate and monitoring checks into CI and registers AutoGluon versions. Keep your
streams if you want to compare them later; nothing later depends on them.

Optional individual practice: run `category`, `new_category` and `corrupt`, and
explain why `corrupt`, which changes features while the labels stay fixed, also
moves layer C. Change the decision so readings after an alarm are left out of the
history. Then read Rabanser, Günnemann and Lipton,
[*Failing Loudly*](https://arxiv.org/abs/1810.11953) (2019), and the
[Evidently data drift documentation](https://docs.evidentlyai.com/metrics/preset_data_drift).
