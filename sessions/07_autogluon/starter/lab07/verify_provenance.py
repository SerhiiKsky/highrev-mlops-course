"""Check that the packaged model names the restored Lab 06 inputs and lock."""
import hashlib
import json
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    project = Path.cwd()
    metadata = json.loads((project / "lab07/model/lab07-model.json").read_text(encoding="utf-8"))
    provenance = metadata["source_provenance"]
    for path, key in (
        (project / "data/01_raw/customers.csv", "raw_customers_sha256"),
        (project / "data/01_raw/orders.csv", "raw_orders_sha256"),
        (project / "uv.lock", "original_lock_sha256"),
    ):
        if sha256(path) != provenance[key]:
            raise ValueError(f"{path} differs from the model's Lab 06 provenance ({key})")
    print("Raw input and project lock hashes match the model's recorded Lab 06 provenance.")


if __name__ == "__main__":
    main()
