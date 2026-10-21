# Session 4 — My pipeline evidence

Copy to `notes/session-04.md` in your individual exercise project. Replace prompts
with your own observations. This is an ungraded learning record. Distinguish
predictions, observed results, instructor demonstrations, and pending work.
Do not include credentials or full customer records.

Record outputs before another run overwrites them. The guided route takes
240 minutes including two ten-minute breaks. In the compact 180-minute route,
mark variant/environment work demonstrated by the instructor separately from
your own implementation; continue unfinished independent variants in the next
supervised period. Validation and required integration checks remain essential.

## Starting point

- Date / OS / shell:
- Starting code commit and uncommitted changes:
- Python, uv, Kedro, kedro-datasets versions:
- Data identity: commit or checksums for both raw CSVs; local input changes:
- Lockfile identity/state and dependency changes during setup:
- Session 3 readiness commands and observed outcomes:
- Modular runner baseline metrics, row counts, and effective parameters:

## Ex 1 — Explain and sketch the workflow

Insert your graph or link. Identify raw inputs, functions, intermediate objects,
outputs, and parameters. Distinguish node names, dataset names, and file paths.
Mark objects held in memory and proposed persisted boundaries.

- An ordering constraint and the dependency that requires it:
- A branch with more than one valid execution order:
- How test data reach evaluation without passing through training:
- Different responsibilities of sklearn Pipeline and Kedro Pipeline:
- What remains unknown after seeing a successful notebook run:

## Ex 2 — Bootstrap Kedro and the catalog

- Files copied/merged; confirmation that future test skeletons are not collected:
- Project discovery/import check and actual output:
- Dependency changes, lock status, and baseline rerun under this lock:
- Why string identifiers and aggregate-index preservation matter:
- Persisted dataset names, types, and exact paths:
- Intermediates held in memory:
- Preparation/split defaults and default `model_options`:
- Supplied `models.low_c` and `models.high_c` settings:
- Meaning of `base_env`, `default_run_env`, and soft parameter merging:

## Ex 3 — Wire functions and model options

- Completed pipeline factories, registry entries, and full-run command:
- Node inputs mapped to function arguments, including `params:model_options`:
- My changes to the optional arguments of `build_model` and `train_model`:
- Evidence that calls without options preserve Session 3 behavior:
- Actual node execution and artifact paths:
- Default Kedro metrics/row counts versus the modular runner under the same lock:
- Numeric comparison tolerance and reason:
- Existing unit-test results; checkpoint commit and pending work:

## Ex 4 — Validate inputs and report class balance

- Validation contract and a small valid fixture:
- Missing columns, empty tables, null/blank IDs, invalid/nonfinite numeric cases:
- Evidence that repeated customer IDs and accepted values remain unchanged:
- Where the existing negative-quantity policy remains enforced:
- Edges from `validated_customers` and `validated_orders` to preparation:
- Why placing validation first in a Python list is insufficient to gate training:
- Reporting contract and hand-calculated mixed-target example:
- Empty, null, nonboolean, and valid single-class reporting cases:
- Input preservation and native JSON scalar checks:
- Focused commands, completed unit-suite results, and Ruff results:
- Full-run class balance: rows / positive / negative / positive_rate:
- Agreement between report values and persisted labels:
- Catalog entry and output path for `class_balance`:
- What these checks establish and what the validator does not check:

## Ex 5 — Select and debug a pipeline

| Investigation | Prediction | Actual command/result or error | Explanation and recovery |
|---|---|---|---|
| Modeling after preparation in a new process | | | |
| Starting at `train_model` in a new process | | | |
| Modeling with labeled Parquet unavailable | | | |
| Modeling after restoring the labeled input | | | |

- Inspection method: definitions, my diagram, or Kedro-Viz:
- Safe rename/disposable-copy method and confirmation of restored state:
- Why selection does not recreate all omitted upstream nodes:
- Why readable saved inputs can still be stale:
- Fresh-process reproduction, comparison tolerance, and limits of local evidence:

## Ex 6 — Reuse modeling with namespaces

- Status: my completed work / instructor demonstration / pending:
- Shared split factory and reusable training/evaluation template:
- `comparison` registry entry and command:
- How both variants receive the same `train_set` and `test_set`:
- Parameter mappings to `models.low_c` and `models.high_c`:
- Graph evidence: one split, two training/evaluation branches, distinct outputs:

| Variant | C | Other model options | Split/target identity | Model path | Metrics path | Observed metrics |
|---|---:|---|---|---|---|---|
| low_c | 0.1 | | | | | |
| high_c | 10.0 | | | | | |

- Evidence that variant outputs do not overwrite each other:
- Interpretation with target, data, and split held fixed:
- Why a changed revenue threshold would change the comparison question:
- Remaining independent work and next supervised checkpoint, if any:

## Ex 7 — Apply environment overrides

- Status: my completed work / instructor demonstration / pending:
- Development files I created and tracked:
- Base versus effective development `model_options`:
- Evidence that development C is `0.25` while base `max_iter` and `class_weight` remain:
- Why parameters merge softly but catalog overrides need both type and path:
- Development run command and observed outcome:
- Development model path: `data/06_models/development/classifier.pickle`:
- Development metrics path: `data/08_reporting/development/metrics.json`:
- Base locations and evidence that model/metrics artifacts are separated:
- Other artifacts still shared through base catalog entries:
- CLI override, if investigated: effective value, precedence, and unchanged YAML:
- Default-environment rerun and verification of restored effective settings:
- Remaining independent work, if any:

## Ex 8 — Test the assembled pipeline

Copy the required integration scaffold only when beginning this exercise.
Complete its assertions; the fixture and CLI helper provide setup, not proof.

| Required check | Command | Actual outcome | Evidence inspected |
|---|---|---|---|
| `test_full_pipeline_writes_consistent_artifacts` | | | |
| `test_invalid_schema_stops_before_training` | | | |
| Complete required test suite | | | |
| Ruff check and format check | | | |

- How the fixture isolates source, configuration, raw inputs, and outputs:
- Successful CLI exit, loadable model, labeled data, metric names/ranges, and report consistency:
- Exact schema mutation made only in the temporary orders CSV:
- Specific validation error; why an import failure cannot satisfy my assertion:
- Evidence that training did not execute and fresh model/metrics were not created:
- Confirmation that original raw files and working artifacts were unchanged:
- Workflow status: local proof / observed remote result / unverified:
- Remaining required assertions or failures, if any:

### Optional extension after Ex 8 — Direct-function parity

Leave `extensions/test_kedro_parity.py` in the course checkout until beginning
this extension. Its destination is `tests/integration/test_kedro_parity.py`.
Complete it before including it in claims of a passing full suite.

- Status: not started / implemented / verified:
- Comparison of labeled frame, predictions, and metrics against direct calls:
- Automated missing-persisted-input failure and recovery:
- Isolation, commands, observed outcomes, and comparison tolerances:
- Additional guarantee beyond the required integration checks:

## Handoff

- Final checkpoint commit and uncommitted changes:
- README updated with default/comparison/environment commands and artifact paths:
- Default model options, environment, and artifact state restored:
- Temporary renames and intentional failures removed:
- Required unit/integration tests implemented and passing:
- Raw CSVs still tracked; generated artifacts and credentials ignored:
- Demonstrated but unfinished independent work and next supervised checkpoint:
- Reproduction conditions: code, data, lock/environment, parameters, random settings:
- Limits: fresh local process versus clean clone or another machine:
- What Session 5 must record to recover the exact data after the CSVs change:
