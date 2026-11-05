"""Verify tracked evidence and move a single-writer MLflow champion alias."""

import hashlib
import json
import math
from pathlib import Path

from mlflow.exceptions import MlflowException
from .learning_tasks import gate_reasons

METRICS = (
    "validation_roc_auc",
    "validation_accuracy",
    "validation_f1",
    "train_seconds",
    "predict_median_ms",
    "predict_p95_ms",
    "load_seconds",
)


def _digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def verify_candidate(candidate, client):
    if (
        candidate.get("schema_version") != 1
        or candidate.get("status") != "complete"
        or candidate.get("roundtrip_verified") is not True
    ):
        raise ValueError("Candidate is not complete and roundtrip verified")
    if candidate.get("candidate_id") != candidate.get("run_id") or not candidate.get(
        "protocol_id"
    ):
        raise ValueError("Invalid candidate identity")
    if (
        not isinstance(candidate.get("artifact_bytes"), int)
        or candidate["artifact_bytes"] <= 0
    ):
        raise ValueError("Invalid model size")
    metrics = candidate.get("metrics", {})
    if any(
        not isinstance(metrics.get(k), (float, int)) or not math.isfinite(metrics[k])
        for k in METRICS
    ):
        raise ValueError("Candidate metrics must be finite")
    if any(not 0 <= metrics[k] <= 1 for k in METRICS[:3]) or any(
        metrics[k] < 0 for k in METRICS[3:]
    ):
        raise ValueError("Candidate metrics outside valid range")
    run = client.get_run(candidate["run_id"])
    if run.info.status != "FINISHED" or run.data.tags.get("model.uri") != candidate.get(
        "model_uri"
    ):
        raise ValueError("Run is unfinished or model URI differs")
    if run.data.tags.get("lab06.protocol_id") != candidate["protocol_id"]:
        raise ValueError("Run protocol differs")
    if any(
        not math.isclose(
            run.data.metrics.get(k, float("nan")),
            metrics[k],
            rel_tol=1e-10,
            abs_tol=1e-10,
        )
        for k in METRICS
    ):
        raise ValueError("Run metrics differ from candidate")
    path = client.download_artifacts(candidate["run_id"], "candidate.json")
    recorded = json.loads(Path(path).read_text(encoding="utf-8"))
    if recorded != candidate:
        raise ValueError("Candidate report differs from run artifact")
    return recorded


def register_candidate(candidate, client, model_name):
    candidate = verify_candidate(candidate, client)
    try:
        client.create_registered_model(model_name)
    except MlflowException as exc:
        if exc.error_code != "RESOURCE_ALREADY_EXISTS":
            raise
    for version in client.search_model_versions(f"name='{model_name}'"):
        if (
            version.run_id == candidate["run_id"]
            and version.source == candidate["model_uri"]
        ):
            return str(version.version)
    return str(
        client.create_model_version(
            model_name, candidate["model_uri"], candidate["run_id"]
        ).version
    )


def resolve_champion(client, model_name, alias="champion"):
    try:
        registered = client.get_registered_model(model_name)
    except MlflowException as exc:
        if exc.error_code == "RESOURCE_DOES_NOT_EXIST":
            return None
        raise
    if alias not in registered.aliases:
        return None
    version = client.get_model_version_by_alias(model_name, alias)
    report = json.loads(
        Path(client.download_artifacts(version.run_id, "candidate.json")).read_text(
            encoding="utf-8"
        )
    )
    verified = verify_candidate(report, client)
    if version.source != verified["model_uri"]:
        raise ValueError("Champion registry source differs from verified candidate")
    return {
        "version": str(version.version),
        "model_uri": f"models:/{model_name}/{version.version}",
        "candidate": verified,
    }


def _write_new(path, record):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, allow_nan=False)


def _update(path, record):
    # A pending record survives failures; completion replaces it after mutation.
    tmp = Path(str(path) + ".tmp")
    _write_new(tmp, record)
    tmp.replace(path)


def _policy(policy):
    names = (
        "min_validation_roc_auc",
        "max_auc_drop",
        "max_artifact_bytes",
        "max_predict_p95_ms",
    )
    if any(
        not isinstance(policy.get(k), (int, float)) or not math.isfinite(policy[k])
        for k in names
    ):
        raise ValueError("Policy requires four finite numeric limits")
    if (
        not 0 <= policy[names[0]] <= 1
        or policy[names[1]] < 0
        or policy[names[2]] < 0
        or policy[names[3]] <= 0
    ):
        raise ValueError("Policy limits outside valid range")


def promote(candidate, client, model_name, policy, decision_path):
    _policy(policy)
    if Path(decision_path).exists():
        raise FileExistsError(decision_path)
    candidate = verify_candidate(candidate, client)
    version = register_candidate(candidate, client, model_name)
    before = resolve_champion(client, model_name)
    champion = before["candidate"] if before else None
    if champion and champion["protocol_id"] != candidate["protocol_id"]:
        raise ValueError("Cannot compare candidates with different protocols")
    reasons = gate_reasons(candidate, champion, policy)
    record = {
        "operation": "promote",
        "status": "rejected" if reasons else "pending",
        "version": version,
        "before": before["version"] if before else None,
        "after": before["version"] if before else None,
        "protocol_id": candidate["protocol_id"],
        "candidate_hash": _digest(candidate),
        "policy": policy,
        "policy_hash": _digest(policy),
        "reasons": reasons,
    }
    _write_new(decision_path, record)
    if reasons:
        return record
    current = resolve_champion(client, model_name)
    if (current["version"] if current else None) != record["before"]:
        raise RuntimeError("Champion changed concurrently; decision remains pending")
    client.set_registered_model_alias(model_name, "champion", version)
    client.set_model_version_tag(
        model_name,
        version,
        "lab06.approval",
        json.dumps(
            {
                "candidate_hash": record["candidate_hash"],
                "protocol_id": record["protocol_id"],
                "policy_hash": record["policy_hash"],
            }
        ),
    )
    record.update(status="approved", after=version)
    _update(decision_path, record)
    return record


def rollback(client, model_name, version, decision_path):
    if Path(decision_path).exists():
        raise FileExistsError(decision_path)
    before = resolve_champion(client, model_name)
    if before is None:
        raise ValueError("No current champion")
    target = client.get_model_version(model_name, str(version))
    approval = json.loads(target.tags.get("lab06.approval", "null"))
    report = json.loads(
        Path(client.download_artifacts(target.run_id, "candidate.json")).read_text(
            encoding="utf-8"
        )
    )
    report = verify_candidate(report, client)
    if (
        target.source != report["model_uri"]
        or not approval
        or approval.get("candidate_hash") != _digest(report)
        or approval.get("protocol_id") != before["candidate"]["protocol_id"]
        or report["protocol_id"] != before["candidate"]["protocol_id"]
    ):
        raise ValueError("Rollback target lacks matching approval or protocol")
    record = {
        "operation": "rollback",
        "status": "pending",
        "before": before["version"],
        "after": None,
        "version": str(version),
        "protocol_id": report["protocol_id"],
        "candidate_hash": _digest(report),
        "reason": "restore previously approved version",
    }
    _write_new(decision_path, record)
    if resolve_champion(client, model_name)["version"] != before["version"]:
        raise RuntimeError("Champion changed concurrently; decision remains pending")
    client.set_registered_model_alias(model_name, "champion", str(version))
    record.update(status="completed", after=str(version))
    _update(decision_path, record)
    return record
