"""Supplied plumbing: verify provenance and describe the running environment."""

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path

import yaml

POINTER = Path("data/01_raw.dvc")


def command(root: Path, *args: str) -> str:
    result = subprocess.run(
        args, cwd=root, text=True, encoding="utf-8", capture_output=True, check=False
    )
    if result.returncode:
        raise RuntimeError(f"{' '.join(args)} failed:\n{result.stderr or result.stdout}")
    return result.stdout.strip()


def provenance(root: Path) -> dict:
    """Refuse a misleading commit/data claim, including dirty or untracked code."""
    if Path(command(root, "git", "rev-parse", "--show-toplevel")).resolve() != root:
        raise RuntimeError("Run in the root of your separate exercise Git repository.")
    revision = command(root, "git", "rev-parse", "HEAD")
    for required in (POINTER.as_posix(), "uv.lock", "pyproject.toml"):
        command(root, "git", "ls-files", "--error-unmatch", required)
    dirty = command(root, "git", "status", "--porcelain", "--untracked-files=normal")
    if dirty:
        raise RuntimeError(f"Commit or preserve Git changes before recording a run:\n{dirty}")
    state = json.loads(
        command(root, sys.executable, "-m", "dvc", "status", "--json", POINTER.as_posix())
    )
    if state:
        raise RuntimeError(f"Raw data differs from the committed DVC pointer: {state}")
    pointer = yaml.safe_load((root / POINTER).read_text(encoding="utf-8"))
    outputs = pointer.get("outs", [])
    if len(outputs) != 1 or outputs[0].get("path") != "01_raw" or not outputs[0].get("md5"):
        raise RuntimeError("Expected a DVC pointer for the data/01_raw directory.")
    files = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((root / "data/01_raw").glob("*.csv"))
    }
    return {
        "git_commit": revision,
        "pointer": pointer,
        "data_hash": outputs[0]["md5"],
        "raw_sha256": files,
        "lock_sha256": hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
    }


def flatten(values: dict, prefix: str = "") -> dict:
    """Preserve nested YAML parameter names with dots for MLflow."""
    result = {}
    for key, value in values.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            result.update(flatten(value, name))
        else:
            result[name] = value
    return result


def environment() -> dict:
    """Record actual installed versions as well as the committed lockfile."""
    names = (
        "kedro",
        "kedro-datasets",
        "dvc",
        "mlflow",
        "pandas",
        "numpy",
        "scikit-learn",
        "pyarrow",
        "user-agents",
        "cloudpickle",
    )
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {name: importlib.metadata.version(name) for name in names},
    }


def model_requirements() -> list[str]:
    names = ("mlflow", "scikit-learn", "pandas", "numpy", "user-agents", "cloudpickle")
    return [f"{name}=={importlib.metadata.version(name)}" for name in names]


def check_catalog(catalog: dict, root: Path) -> None:
    """The pointer must identify the actual files consumed by the catalog."""
    expected = {
        "customers": "data/01_raw/customers.csv",
        "orders": "data/01_raw/orders.csv",
        "classifier": "data/06_models/classifier.pickle",
        "metrics": "data/08_reporting/metrics.json",
    }
    for name, path in expected.items():
        actual = catalog.get(name, {}).get("filepath")
        if actual is None or (root / actual).resolve() != (root / path).resolve():
            raise RuntimeError(f"This lesson adapter expects catalog {name} at {path}.")
