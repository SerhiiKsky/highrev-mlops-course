"""One-time final test evaluation after the champion has been fixed."""

import hashlib
import json
from pathlib import Path

import numpy as np
from mlflow.tracking import MlflowClient
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

from .execution import call_worker, prepare_bundle, write_json
from .lifecycle import resolve_champion
from .protocol import FEATURES, TARGET


def final_audit(config):
    root = Path(config["output_dir"]).resolve()
    marker = root / "test-consumed.json"
    protocol = json.loads((root / "protocol.json").read_text(encoding="utf-8"))
    client = MlflowClient(tracking_uri=config["tracking_uri"])
    champion = resolve_champion(client, config["model_name"])
    if not champion or champion["candidate"]["protocol_id"] != protocol["protocol_id"]:
        raise ValueError("Select a champion approved for this protocol before audit")
    version = client.get_model_version(config["model_name"], champion["version"])
    approval = json.loads(version.tags.get("lab06.approval", "null"))
    if not approval or approval.get("protocol_id") != protocol["protocol_id"]:
        raise ValueError("Champion has no matching approval")
    # Exclusive creation occurs before test data are loaded; failures also consume it.
    write_json(
        marker,
        {
            "status": "consumed",
            "protocol_id": protocol["protocol_id"],
            "model_uri": champion["model_uri"],
            "version": champion["version"],
            "run_id": champion["candidate"]["run_id"],
            "approval": approval,
        },
    )
    bundle = prepare_bundle(config)
    if bundle["protocol"] != protocol:
        raise ValueError("Reconstructed protocol differs; audit remains consumed")
    test = bundle["test"]
    feature_path = root / "audit-features.csv"
    test[FEATURES].rename_axis("row_id").to_csv(feature_path)
    prediction_path = root / "audit-predictions.json"
    request = {
        "model_uri": champion["model_uri"],
        "tracking_uri": config["tracking_uri"],
        "input_csv": str(feature_path),
        "result_path": str(prediction_path),
    }
    result = call_worker(
        config,
        "predict",
        request,
        root / "audit-request.json",
        root / "audit-worker.log",
    )
    if result["row_ids"] != test.index.tolist():
        raise ValueError("Audit predictions do not align with test membership")
    probabilities = np.asarray(result["probabilities"], dtype=float)
    if (
        len(probabilities) != len(test)
        or not np.isfinite(probabilities).all()
        or ((probabilities < 0) | (probabilities > 1)).any()
    ):
        raise ValueError("Invalid audit predictions")
    y = test[TARGET].astype(int)
    report = {
        "protocol_id": protocol["protocol_id"],
        "membership_sha256": protocol["membership_sha256"],
        "test_row_ids_sha256": hashlib.sha256(
            "\n".join(test.index).encode("utf-8")
        ).hexdigest(),
        "model_uri": champion["model_uri"],
        "version": champion["version"],
        "run_id": champion["candidate"]["run_id"],
        "approval": approval,
        "rows": len(test),
        "metrics": {
            "test_roc_auc": float(roc_auc_score(y, probabilities)),
            "test_accuracy": float(accuracy_score(y, probabilities >= 0.5)),
            "test_f1": float(f1_score(y, probabilities >= 0.5)),
        },
    }
    write_json(root / "audit-result.json", report)
    return report
