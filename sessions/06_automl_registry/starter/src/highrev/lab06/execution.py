"""Filesystem and subprocess adapters for a single Lab 06 comparison."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient

from .lifecycle import verify_candidate
from .protocol import make_bundle, membership_bytes, validate_bundle


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def prepare(customers_path, orders_path, preparation, project_src):
    """Run the existing Lab 05 Kedro preparation graph in an in-memory catalog."""
    import highrev

    project_package = str(Path(project_src).resolve() / "highrev")
    if project_package not in highrev.__path__:
        highrev.__path__.append(project_package)
    from highrev.pipelines.data_processing.pipeline import create_pipeline
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    customers = pd.read_csv(customers_path, dtype={"customerID": str})
    orders = pd.read_csv(orders_path, dtype={"customer_id": str})
    if "_lab06_source_row" in customers:
        raise ValueError("Reserved source-row column already exists")
    customers["_lab06_source_row"] = customers.index
    catalog = DataCatalog(
        {
            "customers": MemoryDataset(data=customers),
            "orders": MemoryDataset(data=orders),
            "params:max_age": MemoryDataset(data=preparation["max_age"]),
            "params:high_revenue_threshold": MemoryDataset(
                data=preparation["threshold"]
            ),
        }
    )
    labeled = SequentialRunner().run(
        create_pipeline().to_outputs("customers_labeled"), catalog
    )["customers_labeled"]
    if isinstance(labeled, MemoryDataset):
        labeled = labeled.load()
    return labeled.set_index("_lab06_source_row", drop=True).rename_axis(None)


def call_worker(config, command, request, request_path, log_path):
    write_json(request_path, request)
    env = os.environ.copy()
    env.update(PYTHONUTF8="1", MLFLOW_DISABLE_AGENT_HINT="1")
    env["PYTHONPATH"] = str(Path(config["solution_dir"]).resolve())
    process = subprocess.run(
        [
            str(Path(config["worker_python"]).resolve()),
            "-X",
            "utf8",
            "-m",
            "lab06_worker",
            command,
            "--request",
            str(Path(request_path).resolve()),
        ],
        cwd=str(Path(config["solution_dir"]).resolve()),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=config.get("worker_timeout_seconds", 1800),
    )
    Path(log_path).write_text(process.stdout + process.stderr, encoding="utf-8")
    if process.returncode:
        raise RuntimeError(
            f"Worker {command} exited {process.returncode}; see {log_path}"
        )
    return json.loads(Path(request["result_path"]).read_text(encoding="utf-8"))


def provenance(config):
    return {
        "git_commit": config["git_commit"],
        "data_hash": config["data_hash"],
        "raw_customers_sha256": digest_file(config["customers_csv"]),
        "raw_orders_sha256": digest_file(config["orders_csv"]),
        "original_lock_sha256": digest_file(config["project_lock"]),
    }


def prepare_bundle(config):
    before = provenance(config)
    labeled = prepare(
        config["customers_csv"],
        config["orders_csv"],
        config["preparation"],
        config["project_src"],
    )
    if provenance(config) != before:
        raise RuntimeError("Input provenance changed during preparation")
    return make_bundle(
        labeled,
        {
            "seed": config.get("seed", 42),
            "provenance": before,
            "preparation": config["preparation"],
            "comparison": config["comparison"],
        },
    )


def export_training(bundle, destination):
    validate_bundle(bundle)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for name in ("fit", "holdout", "validation"):
        bundle[name].rename_axis("row_id").to_csv(destination / f"{name}.csv")
    write_json(
        destination / "folds.json",
        {"row_ids": bundle["fit"].index.tolist(), "folds": bundle["folds"]},
    )


def train_candidate(framework, bundle, config, output, comparison_id):
    output = Path(output)
    request = {
        "framework": framework,
        "input_dir": str((output / "training-input").resolve()),
        "output_dir": str((output / framework).resolve()),
        "protocol": bundle["protocol"],
        "tracking_uri": config["tracking_uri"],
        "experiment": config["experiment"],
        "parent_run_id": comparison_id,
        "worker_lock": str(Path(config["worker_lock"]).resolve()),
        "project_src": str(Path(config["project_src"]).resolve()),
        "options": config.get("options", {}),
        "result_path": str((output / f"{framework}-result.json").resolve()),
    }
    result = call_worker(
        config,
        "train",
        request,
        output / f"{framework}-request.json",
        output / f"{framework}.log",
    )
    checked = verify_candidate(
        result, MlflowClient(tracking_uri=config["tracking_uri"])
    )
    if (
        checked["protocol_id"] != bundle["protocol"]["protocol_id"]
        or checked["comparison_id"] != comparison_id
    ):
        raise ValueError("Worker result is not linked to this comparison")
    return checked


def run_comparison(bundle, config):
    output = Path(config["output_dir"]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "config.json", config)
    write_json(output / "protocol.json", bundle["protocol"])
    (output / "membership.csv").write_bytes(membership_bytes(bundle["membership"]))
    export_training(bundle, output / "training-input")
    before = provenance(config)
    if before != bundle["protocol"]["provenance"]:
        raise ValueError("Input provenance changed before training")
    mlflow.set_tracking_uri(config["tracking_uri"])
    mlflow.set_experiment(config["experiment"])
    with mlflow.start_run(run_name="lab06-comparison") as run:
        mlflow.set_tag("lab06.protocol_id", bundle["protocol"]["protocol_id"])
        candidates = [
            train_candidate(name, bundle, config, output, run.info.run_id)
            for name in ("baseline", "pycaret")
        ]
        if provenance(config) != before:
            raise RuntimeError("Input provenance changed during comparison")
        summary = {
            "comparison_id": run.info.run_id,
            "protocol_id": bundle["protocol"]["protocol_id"],
            "candidates": candidates,
        }
        write_json(output / "comparison.json", summary)
        mlflow.log_artifact(str(output / "comparison.json"))
    return summary
