"""Run with: python -m lab06_worker {train,predict} --request request.json."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

for name in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[name] = "1"
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"

import joblib
import mlflow
import numpy as np
import pandas as pd
from mlflow.models import infer_signature
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import PredefinedSplit
from sklearn.preprocessing import FunctionTransformer

from lab06_worker.bundle import ProbabilityBundle
from lab06_worker.learning_tasks import comparison_options, log_validation_metrics

FEATURES = [
    "pages_visited",
    "age_first_order",
    "gender",
    "campaign",
    "ip_address_country",
    "browser",
    "os",
]
TARGET = "high_revenue"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def read_frame(path, labeled=True):
    frame = pd.read_csv(path, dtype={"row_id": str})
    expected = set(FEATURES + ([TARGET] if labeled else []))
    if "row_id" in frame:
        if frame.row_id.isna().any() or frame.row_id.duplicated().any():
            raise ValueError("row_id must be unique and non-null")
        frame = frame.set_index("row_id")
    if set(frame.columns) != expected or frame.empty:
        raise ValueError(
            f"Expected exactly columns {sorted(expected)} and at least one row"
        )
    return frame[FEATURES + ([TARGET] if labeled else [])]


def predict(request):
    frame = read_frame(request["input_csv"], labeled=False)
    mlflow.set_tracking_uri(request["tracking_uri"])
    model = mlflow.pyfunc.load_model(request["model_uri"])
    values = model.predict(frame)["probability_high_revenue"].to_numpy(dtype=float)
    write_json(
        request["result_path"],
        {
            "model_uri": request["model_uri"],
            "row_ids": [str(x) for x in frame.index],
            "probabilities": values.tolist(),
        },
    )


def train(request):
    output = Path(request["output_dir"])
    output.mkdir(parents=True, exist_ok=False)
    inputs = Path(request["input_dir"])
    fit, holdout, validation = (
        read_frame(inputs / (name + ".csv"))
        for name in ("fit", "holdout", "validation")
    )
    if any(
        set(frame[TARGET].astype(int)) != {0, 1} for frame in (fit, holdout, validation)
    ):
        raise ValueError("Each partition must contain both classes")
    fold_data = json.loads((inputs / "folds.json").read_text(encoding="utf-8"))
    if fold_data["row_ids"] != fit.index.tolist() or set(fold_data["folds"]) != {
        0,
        1,
        2,
    }:
        raise ValueError(
            "Fold membership must align with fit rows and contain folds 0, 1, 2"
        )
    folds = np.asarray(fold_data["folds"])
    for fold in range(3):
        if set(fit.loc[folds == fold, TARGET].astype(int)) != {0, 1} or set(
            fit.loc[folds != fold, TARGET].astype(int)
        ) != {0, 1}:
            raise ValueError(
                "Each CV training and validation partition needs both classes"
            )
    options = request.get("options", {})
    mlflow.set_tracking_uri(request["tracking_uri"])
    mlflow.set_experiment(request["experiment"])
    with mlflow.start_run() as run:
        mlflow.set_tags(
            {
                "lab06.framework": request["framework"],
                "lab06.protocol_id": request["protocol"]["protocol_id"],
                "lab06.comparison_id": request["parent_run_id"],
            }
        )
        started = time.perf_counter()
        if request["framework"] == "baseline":
            sys.path.insert(0, request["project_src"])
            from highrev.modeling import build_model

            model = build_model(options.get("model_options"))
            model.fit(fit[FEATURES], fit[TARGET].astype(int))
            version = importlib.metadata.version("scikit-learn")
        elif request["framework"] == "pycaret":
            from pycaret.classification import ClassificationExperiment

            exp = ClassificationExperiment()
            dtype_normalizer = FunctionTransformer(
                pd.DataFrame.astype,
                kw_args={"dtype": {n: object for n in FEATURES[2:]}},
                feature_names_out="one-to-one",
            )
            exp.setup(
                data=fit,
                test_data=holdout,
                target=TARGET,
                index=True,
                session_id=options.get("seed", 42),
                n_jobs=1,
                use_gpu=False,
                html=False,
                verbose=False,
                log_experiment=False,
                system_log=str(output / "pycaret.log"),
                memory=str(output / "cache"),
                numeric_features=FEATURES[:2],
                categorical_features=FEATURES[2:],
                normalize=True,
                fold_strategy=PredefinedSplit(folds),
                custom_pipeline=dtype_normalizer,
                custom_pipeline_position=0,
            )
            if exp.get_config("X_train").index.tolist() != fit.index.tolist():
                raise ValueError("PyCaret changed fit row order")
            best = exp.compare_models(
                **comparison_options(
                    options.get("models", ["lr", "dt"]),
                    options.get("budget_seconds", 300),
                ),
                verbose=False,
            )
            exp.pull().to_csv(output / "leaderboard.csv")
            model, _ = exp.save_model(
                best, str(output / "pycaret_pipeline"), model_only=False, verbose=False
            )
            version = importlib.metadata.version("pycaret")
        else:
            raise ValueError("framework must be baseline or pycaret")
        train_seconds = time.perf_counter() - started
        X = validation[FEATURES]
        native = model.predict_proba(X)[:, list(model.classes_).index(1)]
        pipeline_path = output / "pipeline.joblib"
        joblib.dump(model, pipeline_path)
        wrapped = ProbabilityBundle()
        code_paths = [str(Path(__file__).resolve().parent)]
        if request["framework"] == "baseline":
            code_paths.append(str(Path(request["project_src"]) / "highrev"))
        example = X.head(min(len(X), 5))
        signature = infer_signature(
            example, pd.DataFrame({"probability_high_revenue": native[: len(example)]})
        )
        info = mlflow.pyfunc.log_model(
            name="probability_model",
            python_model=wrapped,
            artifacts={"pipeline": str(pipeline_path)},
            code_paths=code_paths,
            pip_requirements=["mlflow==3.16.1", "pycaret==3.3.2"],
            signature=signature,
            input_example=example,
        )
        load_start = time.perf_counter()
        loaded = mlflow.pyfunc.load_model(info.model_uri)
        load_seconds = time.perf_counter() - load_start
        np.testing.assert_allclose(
            loaded.predict(X).iloc[:, 0], native, rtol=0, atol=1e-10
        )
        # Isolated interpreter deliberately has neither the project nor worker on sys.path.
        reload_input = output / "reload-input.csv"
        reload_output = output / "reload-output.json"
        X.to_csv(reload_input, index=False)
        script = Path(__file__).with_name("reload_check.py")
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        process = subprocess.run(
            [
                sys.executable,
                "-I",
                str(script),
                request["tracking_uri"],
                info.model_uri,
                str(reload_input),
                str(reload_output),
            ],
            cwd=output,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180,
        )
        if process.returncode:
            raise RuntimeError(
                "Fresh model reload failed: " + process.stdout + process.stderr
            )
        np.testing.assert_allclose(
            json.loads(reload_output.read_text(encoding="utf-8")),
            native,
            rtol=0,
            atol=1e-10,
        )
        bundle_dir = Path(
            mlflow.artifacts.download_artifacts(artifact_uri=info.model_uri)
        )
        artifact_bytes = sum(
            p.stat().st_size for p in bundle_dir.rglob("*") if p.is_file()
        )
        batch = X.head(min(len(X), options.get("batch_size", 32)))
        for _ in range(options.get("warmups", 2)):
            loaded.predict(batch)
        durations = []
        for _ in range(options.get("repeats", 10)):
            start = time.perf_counter()
            loaded.predict(batch)
            durations.append((time.perf_counter() - start) * 1000)
        y = validation[TARGET].astype(int)
        metrics = {
            "validation_roc_auc": float(roc_auc_score(y, native)),
            "validation_accuracy": float(accuracy_score(y, native >= 0.5)),
            "validation_f1": float(f1_score(y, native >= 0.5)),
            "train_seconds": train_seconds,
            "predict_median_ms": float(np.median(durations)),
            "predict_p95_ms": float(np.percentile(durations, 95)),
            "load_seconds": load_seconds,
        }
        log_validation_metrics(metrics)
        mlflow.set_tag("model.uri", info.model_uri)
        mlflow.log_dict(request["protocol"], "protocol.json")
        if (output / "leaderboard.csv").exists():
            mlflow.log_artifact(str(output / "leaderboard.csv"))
        provenance = request["protocol"].get("provenance", {})
        lock = Path(request["worker_lock"])
        report = {
            "schema_version": 1,
            "candidate_id": run.info.run_id,
            "run_id": run.info.run_id,
            "framework": request["framework"],
            "framework_version": version,
            "model_uri": info.model_uri,
            "protocol_id": request["protocol"]["protocol_id"],
            "metrics": metrics,
            "git_commit": provenance.get("git_commit"),
            "data_hash": provenance.get("data_hash"),
            "worker_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
            "comparison_id": request["parent_run_id"],
            "status": "complete",
            "roundtrip_verified": True,
            "artifact_bytes": artifact_bytes,
            "features": FEATURES,
            "positive_label": 1,
            "measurement": {
                "hardware": platform.platform(),
                "threads": 1,
                "batch_size": len(batch),
                "warmups": options.get("warmups", 2),
                "repeats": options.get("repeats", 10),
                "size_scope": "all files in downloaded MLflow model directory",
            },
        }
        write_json(output / "candidate.json", report)
        mlflow.log_artifact(str(output / "candidate.json"))
    write_json(request["result_path"], report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["train", "predict"])
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    {"train": train, "predict": predict}[args.command](request)


if __name__ == "__main__":
    main()
