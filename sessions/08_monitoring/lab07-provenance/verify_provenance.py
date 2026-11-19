"""Release gate: check the packaged model against its own recorded lineage.

Lab 08 replacement for the Lab 07 version. Lineage is recorded once, when the
model is trained, and travels with the artifact in lab07-model.json. The gate
checks that artifact, not today's repository: the project lock and raw data
may legitimately change after training (Lab 08 adds Evidently) while the served
model keeps the environment it was built with (lab07/uv.lock and its image).
A model only moves when a new version is trained and promoted.

Fails when the metadata is unreadable, incomplete or malformed, or when the model
files' total size differs from the recorded ``artifact_bytes_before_metadata``.
That is a size check, not a content hash: Lab 07 records no per-file digest, so a
same-size change to a model file is not detected. Reports, without failing, whether the
current raw data and project lock still equal the training lineage.
Run from the project root: uv run --locked python lab07/lab07/verify_provenance.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HEX64 = re.compile(r"[0-9a-f]{64}")
CHECKS = {
    "git_commit": re.compile(r"[0-9a-f]{40}"),
    "data_hash": re.compile(r"[0-9a-f]{32}\.dir"),
    "raw_customers_sha256": HEX64,
    "raw_orders_sha256": HEX64,
    "original_lock_sha256": HEX64,
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_artifact(model_dir):
    """Return a list of problems with the artifact and its metadata; empty means it passes."""
    metadata_path = model_dir / "lab07-model.json"
    if not metadata_path.is_file():
        return [f"missing {metadata_path}: train and package the model first (Lab 07 E2)"]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"{metadata_path} is not readable JSON: {error}"]
    if not isinstance(metadata, dict):
        return [f"{metadata_path} must hold a JSON object"]
    problems = []
    if not str(metadata.get("model_version", "")).strip():
        problems.append("model_version is empty")
    if not HEX64.fullmatch(str(metadata.get("protocol_id", ""))):
        problems.append("protocol_id is not a SHA-256 digest")
    lineage = metadata.get("source_provenance")
    if not isinstance(lineage, dict):
        problems.append("source_provenance is missing or not an object")
        lineage = {}
    for key, pattern in CHECKS.items():
        if not pattern.fullmatch(str(lineage.get(key, ""))):
            problems.append(f"source_provenance.{key} is missing or malformed")
    files = [p for p in model_dir.rglob("*") if p.is_file() and p != metadata_path]
    size = sum(p.stat().st_size for p in files)
    if size != metadata.get("artifact_bytes_before_metadata"):
        problems.append(
            f"model files total {size} bytes, metadata records "
            f"{metadata.get('artifact_bytes_before_metadata')}: not the packaged artifact"
        )
    return problems


def report_lineage(project, lineage):
    """Print whether the working tree still equals the training lineage (information only)."""
    for path, key in (
        (project / "data/01_raw/customers.csv", "raw_customers_sha256"),
        (project / "data/01_raw/orders.csv", "raw_orders_sha256"),
        (project / "uv.lock", "original_lock_sha256"),
    ):
        if not path.is_file():
            state = "absent"
        elif sha256(path) == lineage.get(key):
            state = "same as at training"
        else:
            state = "changed since training (expected after later labs; retrain to move the model)"
        print(f"  {path.relative_to(project).as_posix()}: {state}")


def main():
    project = Path.cwd()
    model_dir = project / "lab07/model"
    problems = check_artifact(model_dir)
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        raise SystemExit(1)
    metadata = json.loads((model_dir / "lab07-model.json").read_text(encoding="utf-8"))
    print(
        f"Artifact {metadata['model_version']} matches its recorded metadata "
        f"(protocol {metadata['protocol_id'][:12]}, source commit "
        f"{metadata['source_provenance']['git_commit'][:12]})."
    )
    print("Working tree compared with the training lineage:")
    report_lineage(project, metadata["source_provenance"])


if __name__ == "__main__":
    main()
