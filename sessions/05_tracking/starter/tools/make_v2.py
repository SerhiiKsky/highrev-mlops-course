"""Create V2 once from the committed V1 pointer; preserve its schema."""

import argparse
import csv
import io
import json
import subprocess
import sys
from pathlib import Path

import yaml


def command(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", check=True)
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-ref", required=True, help="Git commit recorded after tracking V1")
    args = parser.parse_args()
    pointer = Path("data/01_raw.dvc")
    original = yaml.safe_load(command("git", "show", f"{args.v1_ref}:data/01_raw.dvc"))
    if yaml.safe_load(pointer.read_text(encoding="utf-8")) != original:
        raise SystemExit("Current pointer is not V1. Restore V1 before making V2.")
    state = json.loads(command(sys.executable, "-m", "dvc", "status", "--json", str(pointer)))
    if state:
        raise SystemExit("Raw data is already modified; preserve or restore it first.")
    path = Path("data/01_raw/orders.csv")
    with path.open(newline="", encoding="utf-8") as stream:
        header, *rows = list(csv.reader(stream))
    if len(rows) < 10:
        raise SystemExit("This fixture requires at least ten orders.")
    # Detach a potentially linked workspace file before writing, preserving the DVC cache.
    command(sys.executable, "-m", "dvc", "unprotect", str(path))
    result = io.StringIO(newline="")
    writer = csv.writer(result, lineterminator="\n")
    writer.writerow(header)
    kept = [row for index, row in enumerate(rows, 1) if index % 10]
    writer.writerows(kept)
    path.write_bytes(result.getvalue().encode("utf-8"))
    print(f"Orders: {len(rows)} -> {len(kept)}. Run dvc add, commit the pointer, then dvc push.")


if __name__ == "__main__":
    main()
