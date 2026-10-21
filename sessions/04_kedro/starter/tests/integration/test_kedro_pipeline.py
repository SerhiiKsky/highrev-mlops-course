"""Required Ex 8: isolation plumbing is supplied; students write the assertions.

Copy this file only when starting Ex 8 so earlier checkpoints keep their green CI.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def isolated_project(tmp_path):
    source = Path(__file__).resolve().parents[2]
    for name in ("src", "conf"):
        shutil.copytree(
            source / name, tmp_path / name, ignore=shutil.ignore_patterns("__pycache__")
        )
    shutil.copy2(source / "pyproject.toml", tmp_path / "pyproject.toml")
    (tmp_path / ".telemetry").write_text("consent: false\n", encoding="utf-8")
    raw = tmp_path / "data/01_raw"
    raw.mkdir(parents=True)
    for name in ("customers.csv", "orders.csv"):
        shutil.copy2(source / "data/01_raw" / name, raw / name)
    return tmp_path


def invoke_kedro(project, *options):
    env = os.environ.copy()
    env.update(
        PYTHONPATH=str(project / "src"), KEDRO_DISABLE_TELEMETRY="1", PYTHONUTF8="1"
    )
    return subprocess.run(
        [sys.executable, "-m", "kedro", "run", *options],
        cwd=project,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        timeout=90,
    )


def test_full_pipeline_writes_consistent_artifacts(isolated_project):
    """Invoke the CLI, assert exit 0, inspect saved model, labeled table and JSON.

    Compare report counts against the persisted labels; check metric names/ranges.
    Include stdout/stderr in a failing assertion so setup errors can be diagnosed.
    """
    raise NotImplementedError("Ex 8: author the successful end-to-end check")


def test_invalid_schema_stops_before_training(isolated_project):
    """Drop tshirt_price ONLY in the temporary orders CSV and run the full CLI.

    Require nonzero exit, specific schema error, no training node execution, and
    no model/metrics in this fresh output directory. An unrelated import error
    must not satisfy this check. The original exercise CSV must stay unchanged.
    """
    raise NotImplementedError("Ex 8: prove invalid data blocks the training graph")
