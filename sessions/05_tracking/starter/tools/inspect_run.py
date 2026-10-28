"""Read a run's evidence without the UI; optionally compare with another run."""

import argparse
import json
import os
import tempfile
from pathlib import Path

from mlflow.tracking import MlflowClient


def read_run(client: MlflowClient, run_id: str) -> dict:
    run = client.get_run(run_id)
    evidence = {
        "run_id": run_id,
        "status": run.info.status,
        "name": run.data.tags.get("mlflow.runName"),
        "tags": run.data.tags,
        "parameters": run.data.params,
        "metrics": run.data.metrics,
        "artifact_uri": run.info.artifact_uri,
    }
    files = {item.path for item in client.list_artifacts(run_id, "provenance")}
    with tempfile.TemporaryDirectory() as temp:
        for filename in ("effective-parameters", "runtime-overrides", "raw-sha256", "environment"):
            path = f"provenance/{filename}.json"
            if path in files:
                local = client.download_artifacts(run_id, path, temp)
                evidence[filename] = json.loads(Path(local).read_text(encoding="utf-8"))
    return evidence


def compare(left: dict, right: dict, tolerance: float = 1e-8) -> dict:
    names = sorted(set(left["metrics"]) | set(right["metrics"]))
    deltas = {
        name: right["metrics"][name] - left["metrics"][name]
        for name in names
        if name in left["metrics"] and name in right["metrics"]
    }
    same_metrics = bool(names) and len(deltas) == len(names)
    same_code = left["tags"].get("git.commit") == right["tags"].get("git.commit")
    same_data = left["tags"].get("dvc.data_hash") == right["tags"].get("dvc.data_hash")
    within = same_metrics and all(abs(value) <= tolerance for value in deltas.values())
    same_params = left["parameters"] == right["parameters"]
    return {
        "same_code": same_code,
        "same_data": same_data,
        "same_parameters": same_params,
        "metric_deltas_right_minus_left": deltas,
        "tolerance": tolerance,
        "metrics_within_tolerance": within,
        "reproduction_matches": (
            left["status"] == right["status"] == "FINISHED"
            and same_code
            and same_data
            and same_params
            and within
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--tracking-uri", default=os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    )
    parser.add_argument("--compare", help="Second run ID")
    parser.add_argument("--compare-tracking-uri", help="Optional store for a clone's run")
    args = parser.parse_args()
    first = read_run(MlflowClient(tracking_uri=args.tracking_uri), args.run_id)
    result = {"run": first}
    if args.compare:
        second = read_run(
            MlflowClient(tracking_uri=args.compare_tracking_uri or args.tracking_uri), args.compare
        )
        result.update(other_run=second, comparison=compare(first, second))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
