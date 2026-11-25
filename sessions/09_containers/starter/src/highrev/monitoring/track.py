"""Record one monitoring window in MLflow and report which model was scored and served.

Supplied for Lab 09 (project environment, run in the ``project`` job container):

    python -m highrev.monitoring.track --reports data/08_reporting/monitoring/lab09/none

Reads ``<reports>/scores.csv`` (written by ``lab07.score_batches``), asks the live API
which model it serves (``$API_URL/health``), logs both versions, the score summary and
``scores.csv`` to the MLflow tracking server (``$MLFLOW_TRACKING_URI``), then prints
three shell assignments for the driver script::

    MLFLOW_RUN_ID=<run id>
    SERVED_MODEL=<model_version from /health>
    SCORED_MODEL=<model_version in scores.csv>
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

import mlflow
import pandas as pd

EXPERIMENT = "lab09-monitoring"


def served_model(api_url: str) -> str:
    """The model_version the live API reports, or "none" when it serves nothing."""
    with urllib.request.urlopen(f"{api_url.rstrip('/')}/health", timeout=10) as response:
        health = json.load(response)
    return str(health.get("model_version") or "none")


def scored_model(scores: pd.DataFrame) -> str:
    versions = sorted(set(scores["model_version"].dropna().astype(str)))
    if len(versions) != 1:
        raise ValueError(f"scores.csv names {len(versions)} model versions: {versions}")
    return versions[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--reports",
        required=True,
        type=Path,
        help="data/08_reporting/monitoring/<window>/<incident>",
    )
    args = parser.parse_args(argv)
    path = args.reports / "scores.csv"
    if not path.is_file():
        print(f"error: no {path.as_posix()}; run lab07.score_batches first", file=sys.stderr)
        return 1
    scores = pd.read_csv(path)
    scored = scored_model(scores)
    served = served_model(os.environ.get("API_URL", "http://api:10000"))
    done = scores[scores["status"] == "scored"]

    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=f"{args.reports.name}-{scored}") as run:
        mlflow.set_tags({"window": args.reports.as_posix(), "lab": "09"})
        mlflow.log_params(
            {
                "served_model_version": served,
                "scored_model_version": scored,
                "protocol_id": scores["protocol_id"].iloc[0],
                "git_commit": scores["git_commit"].iloc[0],
                "data_hash": scores["data_hash"].iloc[0],
            }
        )
        mlflow.log_metrics(
            {
                "days_scored": len(done),
                "days_skipped": len(scores) - len(done),
                "roc_auc_mean": float(done["roc_auc"].mean()) if len(done) else float("nan"),
                "roc_auc_min": float(done["roc_auc"].min()) if len(done) else float("nan"),
            }
        )
        mlflow.log_artifact(str(path))
    print(f"MLFLOW_RUN_ID={run.info.run_id}")
    print(f"SERVED_MODEL={served}")
    print(f"SCORED_MODEL={scored}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
