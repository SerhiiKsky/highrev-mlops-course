# Session 4 student assets

Start with [the session brief](../04-pipelines-with-kedro.md). Continue your own
HighRev exercise project from Session 3. These assets supply configuration,
package scaffolding, function contracts, and test requirements. You implement
the graph, validation, reporting, model configuration, and assertions.

The complete guided implementation takes **240 minutes, including two ten-minute
breaks**. In the compact 180-minute delivery, the instructor walks through model
variants and environment overrides while students complete essential validation
and integration work. Independent implementation of unfinished variants continues
in the next supervised period. Record unfinished checkpoints honestly; the
shorter delivery does not remove required integration checks. Exercises and
this evidence record are ungraded individual work.

## Copy assets when their exercise starts

Update the course checkout to receive these files. Copy from that checkout into
your separate individual exercise repository. Source links below are relative
to `sessions/04_kedro/`; destinations are relative to your exercise project root.
Create parent directories as needed. Compare and merge existing destination
files. Do not copy the whole starter tree at once: test skeletons deliberately
fail until implemented and must enter test discovery at their stated exercise.

| When | Supplied asset | Exact destination | Purpose |
|---|---|---|---|
| Ex 1 | [pipeline-evidence.md](pipeline-evidence.md) | `notes/session-04.md` | Record observations across all eight exercises. |
| Ex 2 | [config-snippets.toml](config-snippets.toml) | Merge into `pyproject.toml` | Add Kedro metadata; retain build, dependencies, package discovery, Ruff, and pytest settings. |
| Ex 2 | [settings.py](starter/src/highrev/settings.py) | `src/highrev/settings.py` | Explicit base/local environments and soft merging of nested parameters. |
| Ex 2 | [pipeline_registry.py](starter/src/highrev/pipeline_registry.py) | `src/highrev/pipeline_registry.py` | Ex 3 registration scaffold; extend with `comparison` in Ex 6. |
| Ex 2 | [pipelines/__init__.py](starter/src/highrev/pipelines/__init__.py) | `src/highrev/pipelines/__init__.py` | Pipeline package marker. |
| Ex 2 | [data_processing/__init__.py](starter/src/highrev/pipelines/data_processing/__init__.py) | `src/highrev/pipelines/data_processing/__init__.py` | Data-processing package export. |
| Ex 2 | [data_processing/pipeline.py](starter/src/highrev/pipelines/data_processing/pipeline.py) | `src/highrev/pipelines/data_processing/pipeline.py` | Ex 3 wiring; Ex 4 validation and reporting. |
| Ex 2 | [modeling/__init__.py](starter/src/highrev/pipelines/modeling/__init__.py) | `src/highrev/pipelines/modeling/__init__.py` | Modeling package export. |
| Ex 2 | [modeling/pipeline.py](starter/src/highrev/pipelines/modeling/pipeline.py) | `src/highrev/pipelines/modeling/pipeline.py` | Ex 3 model-options wiring; Ex 6 shared split and reusable training/evaluation template. |
| Ex 2 | [catalog.yml](starter/conf/base/catalog.yml) | `conf/base/catalog.yml` | Basic raw-input and persisted-output entries; add report and variant entries later. |
| Ex 2 | [parameters.yml](starter/conf/base/parameters.yml) | `conf/base/parameters.yml` | Preparation/split defaults, default model options, and `models.low_c` / `models.high_c`. |
| Ex 4 | [validation.py](starter/src/highrev/validation.py) | `src/highrev/validation.py` | Raw-input validation contract to implement. |
| Ex 4 | [reporting.py](starter/src/highrev/reporting.py) | `src/highrev/reporting.py` | Class-balance reporting contract to implement. |
| Ex 4 | [test_validation.py](starter/tests/unit/test_validation.py) | `tests/unit/test_validation.py` | Write validation assertions using small fixtures. |
| Ex 4 | [test_reporting.py](starter/tests/unit/test_reporting.py) | `tests/unit/test_reporting.py` | Write report assertions and invalid-input cases. |
| Ex 8 only | [test_kedro_pipeline.py](starter/tests/integration/test_kedro_pipeline.py) | `tests/integration/test_kedro_pipeline.py` | Required integration tests: isolated-project fixture and CLI helper supplied; assertions are your work. |

Retain `src/highrev/__init__.py`, `__main__.py`, `runner.py`,
`data_processing.py`, and existing tests. In Ex 3, **edit your own `modeling.py`**
to give `build_model` and `train_model` an optional `model_options` dictionary.
Calls without this argument must preserve Session 3 defaults and behavior.
No replacement modeling implementation is supplied. The pipeline package lives
alongside these existing modules.

Use your tracked Session 3 CSVs; no raw data is supplied here. Create `conf/local/`,
keep credentials ignored, and track base configuration. Keep generated artifacts
ignored; raw inputs remain tracked until Session 5.

## Work added during the exercises

| Exercise | Work you own |
|---|---|
| Ex 1 — Explain and sketch the workflow | Trace functions, data, parameters, and persistence boundaries. |
| Ex 2 — Bootstrap Kedro and the catalog | Merge metadata, install dependencies, inspect the catalog, and update the lock. |
| Ex 3 — Wire functions and model options | Complete basic pipelines and registry; add default-compatible model options. |
| Ex 4 — Validate inputs and report class balance | Implement/test both functions; route both preparation paths through validated outputs; persist the report. |
| Ex 5 — Select and debug a pipeline | Observe selected-run success, missing memory/persisted inputs, and recovery. |
| Ex 6 — Reuse modeling with namespaces | Share one split and instantiate training/evaluation as `low_c` and `high_c`; register `comparison`. |
| Ex 7 — Apply environment overrides | Create development configuration, inspect merging, and separate development model/metrics paths. |
| Ex 8 — Test the assembled pipeline | Complete required isolated integration assertions and run the required suite. |

Add these entries to the base catalog at their stated exercise:

| Exercise | Dataset name | Type | File path |
|---|---|---|---|
| Ex 4 | `class_balance` | `json.JSONDataset` | `data/08_reporting/class_balance.json` |
| Ex 6 | `low_c.classifier` | `pickle.PickleDataset` | `data/06_models/low_c/classifier.pickle` |
| Ex 6 | `high_c.classifier` | `pickle.PickleDataset` | `data/06_models/high_c/classifier.pickle` |
| Ex 6 | `low_c.metrics` | `json.JSONDataset` | `data/08_reporting/low_c/metrics.json` |
| Ex 6 | `high_c.metrics` | `json.JSONDataset` | `data/08_reporting/high_c/metrics.json` |

Both variants use the same `train_set` and `test_set`. Their parameters come
from `models.low_c` and `models.high_c`; model and metric outputs have distinct
names. Compare their settings on the same target and split.

For Ex 7, create **your own** `conf/development/parameters.yml` and
`conf/development/catalog.yml`; these files are not supplied. Override
`model_options.C` to `0.25`. The supplied soft parameter merge retains base
`max_iter` and `class_weight`. Catalog overrides use replacement behavior, so
each overridden `classifier` and `metrics` entry needs its full `type` and
`filepath`. Use `data/06_models/development/classifier.pickle` and
`data/08_reporting/development/metrics.json`. Other entries still come from base;
these two overrides do not isolate every artifact of a full development run.

## Tests and the optional parity extension

Copy validation/reporting tests only at Ex 4 and complete their assertions then.
Copy the required integration file only when **starting Ex 8**. Its fixture copies
source, configuration, and CSVs into a temporary project; its helper launches
fresh Kedro CLI processes. Assert successful-run artifacts and prove invalid
schema prevents training for the intended reason. An unrelated import failure
is not validation evidence. Complete these required assertions before claiming
the full suite or existing integration workflow passes.

After Ex 8, optionally copy [test_kedro_parity.py](extensions/test_kedro_parity.py)
to `tests/integration/test_kedro_parity.py`. This extension compares labeled data,
predictions, and metrics with direct calls and automates the persisted-input
boundary check. Leave it outside test discovery until starting the extension.
It adds evidence beyond required Ex 8 tests; no activity points or additional
grading requirements are attached to it.
