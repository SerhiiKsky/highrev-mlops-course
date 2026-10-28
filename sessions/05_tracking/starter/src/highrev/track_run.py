"""One MLflow run around the existing Kedro default pipeline. Run at project root."""

import argparse
import json
import math
import os
import pickle
from pathlib import Path

import mlflow
import mlflow.sklearn
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from highrev.tracking_support import (
    check_catalog,
    environment,
    flatten,
    model_requirements,
    provenance,
)


def record_parameters(params: dict, overrides: dict) -> None:
    """Ex 4: save searchable choices and the full effective configuration."""
    # TODO: searchable parameters, effective configuration, runtime overrides.
    _ = flatten(params)  # Available flat representation; choose the matching API card.
    raise NotImplementedError("Ex 4: connect the parameter and configuration pieces")


def record_metrics(metrics: dict, metrics_path: Path) -> None:
    """Ex 4: save measured numbers and their evaluation file."""
    # TODO: measured values AND their evaluation file are different pieces.
    raise NotImplementedError("Ex 4: connect the metric and report pieces")


def record_model(model):
    """Ex 4: preserve preprocessing, classifier and the custom Python transform."""
    # TODO: return model info from the supplied model logging card.
    _ = model_requirements()  # Actual installed versions are supplied.
    raise NotImplementedError("Ex 4: connect the model piece")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="tracked-run")
    parser.add_argument("--c", type=float, help="Override only model_options.C")
    args = parser.parse_args()
    if args.c is not None and (not math.isfinite(args.c) or args.c <= 0):
        parser.error("--c must be finite and positive")
    root = Path.cwd().resolve()
    os.environ.setdefault("KEDRO_DISABLE_TELEMETRY", "1")
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow.set_experiment("highrev-lesson-05")
    # Exceptions inside this context mark the run FAILED, even before training starts.
    with mlflow.start_run(run_name=args.name) as run:
        print(f"MLflow run ID: {run.info.run_id}", flush=True)
        before = provenance(root)
        mlflow.set_tags(
            {
                "git.commit": before["git_commit"],
                "dvc.pointer": "data/01_raw.dvc",
                "dvc.data_hash": before["data_hash"],
                "kedro.pipeline": "__default__",
                "kedro.env": "base",
            }
        )
        mlflow.log_dict(before["pointer"], "provenance/dvc-pointer.json")
        mlflow.log_dict(before["raw_sha256"], "provenance/raw-sha256.json")
        mlflow.log_dict(environment(), "provenance/environment.json")
        mlflow.log_artifact(str(root / "uv.lock"), "provenance")
        bootstrap_project(root)
        overrides = {"model_options": {"C": args.c}} if args.c is not None else {}
        with KedroSession.create(
            project_path=root, env="base", runtime_params=overrides
        ) as session:
            context = session.load_context()
            params = dict(context.config_loader["parameters"])
            check_catalog(context.config_loader["catalog"], root)
            if not {"C", "max_iter", "class_weight"} <= params.get("model_options", {}).keys():
                raise RuntimeError("Finish the Session 4 model_options wiring before this lab.")
            record_parameters(params, overrides)
            session.run()
        if provenance(root) != before:
            raise RuntimeError("Code or data provenance changed during the pipeline run.")
        metrics_path = root / "data/08_reporting/metrics.json"
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        record_metrics(metrics, metrics_path)
        # Only load the trusted model just produced by this local pipeline.
        with (root / "data/06_models/classifier.pickle").open("rb") as stream:
            model = pickle.load(stream)
        model_info = record_model(model)
        mlflow.set_tag("model.uri", model_info.model_uri)
        print(f"Recorded metrics: {metrics}", flush=True)
        print(f"Model URI: {model_info.model_uri}", flush=True)


if __name__ == "__main__":
    main()
