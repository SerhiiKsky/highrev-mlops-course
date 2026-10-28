# Session 05 student assets

Start with the [student brief](../05-data-versioning-and-tracking.md). Work in
your own individual exercise repository, separate from the course checkout and
the team project. Copy only the named files; do not replace your Session 04
pipeline, configuration, or functions.

| Course asset | Destination in your exercise project | Purpose |
| --- | --- | --- |
| [track_run.py](starter/src/highrev/track_run.py) | `src/highrev/track_run.py` | Execution adapter with three short functions for you to implement. |
| [tracking_support.py](starter/src/highrev/tracking_support.py) | `src/highrev/tracking_support.py` | Supplied provenance and environment helpers; inspect their contract. |
| [make_v2.py](starter/tools/make_v2.py) | `tools/make_v2.py` | Create controlled V2 by removing every tenth order. The required `--v1-ref` and clean-data guard prevent accidental repeated changes. |
| [inspect_run.py](starter/tools/inspect_run.py) | `tools/inspect_run.py` | Print run evidence as JSON, optionally comparing another run, including across tracking stores. |
| [API cards](api-cards.md) | Read from the course checkout | The available MLflow calls and how to use each puzzle piece. |
| [Ignore snippet](gitignore-snippet.txt) | Merge into `.gitignore` | Keep local tracking stores and generated outputs out of Git. |
| [Evidence board](evidence-board.md) | `notes/session-05.md` | Your own observations and conclusions. |

Create missing parent directories. Compare existing files before copying and
merge rather than overwrite your work. Complete and commit the adapter, support
files, lockfile and project changes before run A. Keep observations outside the
project until after run B, or commit them before A: A and B need the same clean
Git commit. The local MLflow database, model artifacts, DVC cache and remote
data are runtime data, not files to commit.

The three functions you complete are `record_parameters(params, overrides)`,
`record_metrics(metrics, metrics_path)` and `record_model(model)`; the last
returns MLflow model info. The model API card supplies the complete logging
call using `model_requirements()`, `code_paths=['src/highrev']` and
`serialization_format='cloudpickle'`. Do not change the existing data
preparation imports to make the model log.
