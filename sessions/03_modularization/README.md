# Session 03 building blocks

Start with [the session brief](../03-modularization-and-tests.md). These assets contain
interfaces, tiny input data, and unfinished tests. The functions and tests deliberately
raise `NotImplementedError`: a collected test suite is not yet a working implementation.
Write your own transformation bodies and assertions using your Session 2 baseline
and the documented contracts. No model, completed assertions, or solution notebook is supplied.

## What to copy

All source paths below are relative to the **course checkout**. All destinations are
relative to the **individual exercise project**. Update the course checkout before copying.

| Source under `sessions/03_modularization/` | Destination | Purpose |
|---|---|---|
| [`starter/src/highrev/__init__.py`](starter/src/highrev/__init__.py) | `src/highrev/__init__.py` | Importable package without execution |
| [`starter/src/highrev/__main__.py`](starter/src/highrev/__main__.py) | `src/highrev/__main__.py` | Wiring for `python -m highrev` |
| [`starter/src/highrev/data_processing.py`](starter/src/highrev/data_processing.py) | `src/highrev/data_processing.py` | Three transformation contracts |
| [`starter/src/highrev/modeling.py`](starter/src/highrev/modeling.py) | `src/highrev/modeling.py` | Features and modeling function contracts |
| [`starter/src/highrev/runner.py`](starter/src/highrev/runner.py) | `src/highrev/runner.py` | Explicit execution boundary |
| [`starter/tests/unit/test_data_processing.py`](starter/tests/unit/test_data_processing.py) | `tests/unit/test_data_processing.py` | Unfinished behavior tests |
| [`starter/tests/unit/test_modeling.py`](starter/tests/unit/test_modeling.py) | `tests/unit/test_modeling.py` | Unfinished modeling tests |
| [`starter/tests/integration/test_workflow.py`](starter/tests/integration/test_workflow.py) | `tests/integration/test_workflow.py` | Unfinished workflow tests |
| [`starter/tests/fixtures/orders_tiny.csv`](starter/tests/fixtures/orders_tiny.csv) | `tests/fixtures/orders_tiny.csv` | Repeat customers, aggregation, threshold cases |
| [`starter/tests/fixtures/customers_tiny.csv`](starter/tests/fixtures/customers_tiny.csv) | `tests/fixtures/customers_tiny.csv` | Date repairs, fractional age, old/unmatched customers |
| [`starter/tests/fixtures/orders_negative.csv`](starter/tests/fixtures/orders_negative.csv) | `tests/fixtures/orders_negative.csv` | One valid and one negative quantity for the same customer |
| [`contracts-and-evidence.md`](contracts-and-evidence.md) | `notes/session-03.md` | Blank decision and observation record |
| [`pre-commit-config.yaml`](pre-commit-config.yaml) | `.pre-commit-config.yaml` | Ruff lint/format checks on staged Python files before each commit |
| [`config-snippets.toml`](config-snippets.toml) | Merge into `pyproject.toml` | Install `src/highrev` and configure test discovery |
| [`integration-requirements.md`](integration-requirements.md) | Read in the course checkout | Requirements for tests and workflow edits |

The fixtures use the baseline's year/month/day slash date convention (padded and unpadded
month/day components). Use that convention in additional fixtures too; accepting mixed
slash and ISO date strings would be a separate parsing-contract change.

The fixtures are synthetic: their IDs are intentionally strings with leading zeroes,
their IP addresses are documentation examples, and their rows are small enough to reason
about manually. They are inputs, not expected-output tables. They do not have enough rows
to train and stratify the full classifier reliably; create a suitable small modeling
fixture for unit tests and use the existing project CSVs for the integration exercise.

Do not replace your project's raw CSVs with these fixtures. Keep `baseline.py` available
as the comparison until the extracted command works. Course materials stay in the course
checkout; your implementation, tests, decisions, and workflow belong in the exercise project.
