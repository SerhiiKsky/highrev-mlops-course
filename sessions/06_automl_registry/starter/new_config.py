"""Portable JSON writer used by the Bash setup command."""
import argparse
import json
import uuid
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("git_commit")
    parser.add_argument("data_hash")
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    lab = Path(__file__).resolve().parent
    run = args.run_directory.resolve()
    worker = lab / "worker-env/.venv/bin/python"
    if not worker.is_file():
        worker = lab / "worker-env/.venv/Scripts/python.exe"
    if not worker.is_file():
        raise FileNotFoundError("Sync the worker environment before creating a config")
    for path in (project / "src", project / "uv.lock", project / "data/01_raw/customers.csv", project / "data/01_raw/orders.csv"):
        if not path.exists():
            raise FileNotFoundError(path)
    run.mkdir(parents=True, exist_ok=False)
    config = {
        "solution_dir": str(lab), "worker_python": str(worker),
        "worker_lock": str(lab / "worker-env/uv.lock"),
        "project_src": str(project / "src"), "project_lock": str(project / "uv.lock"),
        "customers_csv": str(project / "data/01_raw/customers.csv"),
        "orders_csv": str(project / "data/01_raw/orders.csv"),
        "output_dir": str(run / "comparison"),
        "tracking_uri": "sqlite:///" + (run / "mlflow.db").as_posix(),
        "experiment": "lab06-comparison", "model_name": "lab06-" + uuid.uuid4().hex[:8],
        "git_commit": args.git_commit, "data_hash": args.data_hash, "seed": 42,
        "preparation": {"max_age": 100, "threshold": 300},
        "comparison": {"metric": "roc_auc", "weighting": "row", "classification_threshold": .5, "resource_policy": "classroom"},
        "options": {"models": ["lr", "dt"], "budget_seconds": 300, "seed": 42, "warmups": 2, "repeats": 10, "batch_size": 32},
        "policy": {"min_validation_roc_auc": 0, "max_auc_drop": 1, "max_artifact_bytes": 1000000000, "max_predict_p95_ms": 100000},
    }
    with (run / "config.json").open("x", encoding="utf-8") as stream:
        json.dump(config, stream, indent=2, allow_nan=False)
    print(f"Configuration created: {run / 'config.json'}")
    print("Review preparation values and policy limits before the comparison.")


if __name__ == "__main__":
    main()
