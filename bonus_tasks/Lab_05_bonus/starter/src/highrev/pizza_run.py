"""Pizza tracking adapter. Complete K4; reuse your completed Session 05 helpers."""

import argparse
import json
import math
import os
import pickle
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import mlflow
import pandas as pd
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from highrev.pipelines.pizza_panic.nodes import comparison_figure
from highrev.track_run import record_metrics, record_model, record_parameters
from highrev.tracking_support import environment, provenance

CATALOG_PATHS = {
    "pizza_orders": "data/01_raw/orders.csv",
    "pizza_restaurants": "data/01_raw/restaurants.csv",
    "pizza_results": "data/08_reporting/pizza_comparison.csv",
    "pizza_models": "data/06_models/pizza_models.pickle",
}


def run_pizza_pipeline(session):
    """STUDENT TODO K4: execute the registered pizza_panic pipeline here.

    Use the KedroSession.run pipeline_name argument. The supplied adapter
    handles logging; this function must let Kedro execute your graph.
    """
    raise NotImplementedError("K4: run your named Kedro pipeline")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="pizza-search")
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--c", type=float)
    parser.add_argument("--threshold", type=float)
    args = parser.parse_args()
    if args.reproduce:
        if args.c is None or args.threshold is None:
            parser.error("--reproduce needs both --c and --threshold")
        if not math.isfinite(args.c) or args.c <= 0:
            parser.error("C must be finite and positive")
        if not math.isfinite(args.threshold) or not 0 <= args.threshold <= 1:
            parser.error("threshold must be finite and between 0 and 1")
    elif args.c is not None or args.threshold is not None:
        parser.error("Use --reproduce when selecting C and threshold")
    root = Path.cwd().resolve()
    os.environ.setdefault("KEDRO_DISABLE_TELEMETRY", "1")
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow.set_experiment("pizza-panic-bonus")
    overrides = {"pizza_selection": {
        "mode": "reproduce", "c": args.c, "threshold": args.threshold,
    }} if args.reproduce else {}
    with mlflow.start_run(run_name=args.name) as parent:
        print(f"Parent run ID: {parent.info.run_id}", flush=True)
        before = provenance(root)
        if set(before["raw_sha256"]) != {"orders.csv", "restaurants.csv"}:
            raise RuntimeError("Use only the assigned Pizza orders/restaurants pair in data/01_raw")
        identity = {"git.commit": before["git_commit"],
                    "dvc.data_hash": before["data_hash"],
                    "dvc.pointer": "data/01_raw.dvc",
                    "kedro.pipeline": "pizza_panic", "kedro.env": "pizza"}
        mlflow.set_tags(identity)
        mlflow.log_dict(before, "provenance/identity.json")
        runtime = environment()
        # matplotlib is added for this bonus and is also covered by uv.lock.
        import importlib.metadata
        runtime["packages"]["matplotlib"] = importlib.metadata.version("matplotlib")
        mlflow.log_dict(runtime, "provenance/environment.json")
        mlflow.log_artifact(str(root / "uv.lock"), "provenance")
        bootstrap_project(root)
        with KedroSession.create(project_path=root, env="pizza", runtime_params=overrides) as session:
            context = session.load_context()
            catalog = context.config_loader["catalog"]
            for name, expected in CATALOG_PATHS.items():
                actual = catalog.get(name, {}).get("filepath")
                if actual is None or (root / actual).resolve() != (root / expected).resolve():
                    raise RuntimeError(f"K2: {name} must use {expected}")
            params = dict(context.config_loader["parameters"])
            effective = {key: params[key] for key in ("pizza_settings", "pizza_selection")}
            record_parameters(effective, overrides)
            run_pizza_pipeline(session)
        if provenance(root) != before:
            raise RuntimeError("Code or data provenance changed during execution")
        results = pd.read_csv(root / CATALOG_PATHS["pizza_results"])
        # Load only models just produced by this local, trusted Kedro execution.
        with (root / CATALOG_PATHS["pizza_models"]).open("rb") as stream:
            models = pickle.load(stream)
        expected_rows = 1 if args.reproduce else 15
        if len(results) != expected_rows:
            raise RuntimeError(f"Expected {expected_rows} candidate rows; got {len(results)}")
        mlflow.log_artifact(str(root / CATALOG_PATHS["pizza_results"]), "comparison")
        if not args.reproduce:
            fig = comparison_figure(results)
            try:
                mlflow.log_figure(fig, "comparison/auc_vs_f1.png")
            finally:
                plt.close(fig)
        for row in results.to_dict("records"):
            with mlflow.start_run(run_name=f"C={row['C']} threshold={row['threshold']}",
                                  nested=True) as child:
                mlflow.set_tags(identity)
                record_parameters({**effective, "C": row["C"], "threshold": row["threshold"]},
                                  overrides)
                metrics = {key: float(value) for key, value in row.items()
                           if key.startswith("val_")}
                with tempfile.TemporaryDirectory() as folder:
                    report = Path(folder) / "metrics.json"
                    report.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
                    record_metrics(metrics, report)
                info = record_model(models[float(row["C"])])
                mlflow.set_tag("model.uri", info.model_uri)
                print(f"Candidate {child.info.run_id}: C={row['C']} t={row['threshold']} {metrics}")
        print(results.to_string(index=False))


if __name__ == "__main__":
    main()
