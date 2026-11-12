"""Train from Lab 06 exported partitions, never from the held-out test set."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from autogluon.tabular import TabularPredictor
from sklearn.metrics import roc_auc_score

from lab07.contracts import FEATURES, TARGET


def read_partition(path):
    frame = pd.read_csv(path, dtype={"row_id": str})
    if list(frame.columns) != ["row_id", *FEATURES, TARGET] or frame.empty:
        raise ValueError(f"Unexpected schema or empty partition: {path}")
    if frame.row_id.isna().any() or frame.row_id.duplicated().any():
        raise ValueError(f"Invalid row IDs: {path}")
    if frame[TARGET].isna().any() or set(frame[TARGET]) != {0, 1}:
        raise ValueError(f"Both binary labels required: {path}")
    # Lab 06 CSVs may encode this target as True/False; make the class labels
    # consistently integer 0/1 before AutoGluon chooses probability columns.
    frame[TARGET] = frame[TARGET].astype("int64")
    return frame


def check_membership(comparison, protocol, partitions):
    """Check the retained Lab 06 manifest before fitting; never read test features."""
    canonical = json.dumps(
        {k: v for k, v in protocol.items() if k != "protocol_id"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != protocol.get("protocol_id"):
        raise ValueError("Lab 06 protocol digest differs")
    manifest = (comparison / "membership.csv").read_bytes()
    if hashlib.sha256(manifest).hexdigest() != protocol.get("membership_sha256"):
        raise ValueError("Lab 06 membership digest differs")
    membership = pd.read_csv(comparison / "membership.csv", dtype={"row_id": str, "customer_id": str})
    if membership.row_id.duplicated().any() or membership.customer_id.isna().any():
        raise ValueError("Invalid Lab 06 membership identities")
    if membership.groupby("customer_id")[["outer_partition", "inner_partition"]].nunique().gt(1).any().any():
        raise ValueError("A customer crosses comparison partitions")
    selectors = {
        "fit": membership.inner_partition.eq("fit"),
        "holdout": membership.inner_partition.eq("holdout"),
        "validation": membership.outer_partition.eq("validation"),
    }
    for name, frame in partitions.items():
        expected = membership.loc[selectors[name], ["row_id", TARGET]]
        if frame.row_id.tolist() != expected.row_id.tolist() or frame[TARGET].tolist() != expected[TARGET].tolist():
            raise ValueError(f"{name} rows or labels differ from Lab 06 membership")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--seconds", type=int, default=60)
    args = parser.parse_args()
    if not args.version.strip() or args.seconds < 1:
        parser.error("version must be nonempty and seconds must be positive")
    if args.output.exists():
        raise FileExistsError(f"Preserve existing model; choose another output: {args.output}")
    protocol = json.loads((args.comparison / "protocol.json").read_text(encoding="utf-8"))
    if protocol.get("features") != FEATURES or protocol.get("target") != TARGET:
        raise ValueError("Lab 06 protocol has an incompatible feature/target contract")
    inputs = args.comparison / "training-input"
    fit, holdout, validation = [read_partition(inputs / f"{part}.csv") for part in ("fit", "holdout", "validation")]
    check_membership(args.comparison, protocol, {"fit": fit, "holdout": holdout, "validation": validation})
    ids = [set(part.row_id) for part in (fit, holdout, validation)]
    if any(ids[i] & ids[j] for i, j in ((0, 1), (0, 2), (1, 2))):
        raise ValueError("Training partitions share row IDs")
    # Use Lab 06's customer-disjoint inner holdout. Never let AutoGluon randomly split rows.
    predictor = TabularPredictor(label=TARGET, eval_metric="roc_auc", path=str(args.output)).fit(
        train_data=fit.drop(columns="row_id"),
        tuning_data=holdout.drop(columns="row_id"),
        time_limit=args.seconds,
        hyperparameters={"RF": {"n_estimators": 50}},
        num_bag_folds=0,
        num_stack_levels=0,
        num_cpus=1,
        fit_weighted_ensemble=False,
    )
    data = validation[FEATURES]
    probabilities = predictor.predict_proba(data)[1].to_numpy(dtype=float)
    auc = float(roc_auc_score(validation[TARGET], probabilities))
    sample = data.iloc[: min(32, len(data))]
    for _ in range(2):
        predictor.predict_proba(sample)
    times = []
    for _ in range(10):
        start = time.perf_counter()
        predictor.predict_proba(sample)
        times.append((time.perf_counter() - start) * 1000)
    # Remove AutoGluon's cached training/validation tables from the deployment copy.
    # The model itself can still retain information learned from its training data.
    predictor.save_space(remove_data=True)
    model_bytes = sum(p.stat().st_size for p in args.output.rglob("*") if p.is_file())
    metadata = {
        "model_version": args.version,
        "protocol_id": protocol["protocol_id"],
        "source_provenance": protocol["provenance"],
        "validation_roc_auc": auc,
        "artifact_bytes_before_metadata": model_bytes,
        "prediction_p95_ms": float(np.percentile(times, 95)),
        "prediction_batch_size": len(sample),
        "repeats": len(times),
    }
    (args.output / "lab07-model.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
