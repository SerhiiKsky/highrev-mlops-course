"""Score every serving batch once its delayed labels arrive (layer C, AutoGluon environment).

Run from lab07/ after ``python -m highrev.monitoring validate`` wrote the schema verdicts:

    uv run --locked python -m lab07.score_batches --model model \\
        --stream ../data/05_serving/none --reports ../data/08_reporting/monitoring/none

Rewrites ``<reports>/scores.csv`` for the whole stream, one row per date:
``date,status,n,roc_auc,accuracy,mean_probability,positive_rate,model_version,
protocol_id,git_commit,data_hash``. ``status`` is ``scored``, or ``skipped: schema``
when the date's ``schema.json`` is missing or not ok (its metrics stay empty).
``model_identity`` and the CLI are supplied; ``score_batch`` is the L08-E3 TODO. This
environment exchanges only CSV and JSON files with the project environment.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score

from lab07.contracts import FEATURES, TARGET

KEY = "row_id"
METRICS = ["n", "roc_auc", "accuracy", "mean_probability", "positive_rate"]
IDENTITY = ["model_version", "protocol_id", "git_commit", "data_hash"]
COLUMNS = ["date", "status", *METRICS, *IDENTITY]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATE_FOLDER = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# data/01_raw.dvc is YAML, but this environment has no PyYAML: read the md5 line.
MD5_LINE = re.compile(r"^\s*-?\s*md5:\s*(\S+)\s*$", re.MULTILINE)


def model_identity(model_dir, project_root):
    """Which model scored, from which code and data (supplied).

    ``model_version`` and ``protocol_id`` come from ``<model_dir>/lab07-model.json``;
    ``git_commit`` is ``git rev-parse HEAD`` in ``project_root`` ("unknown" if git fails);
    ``data_hash`` is the ``md5`` of ``data/01_raw.dvc`` ("unknown" if absent).
    """
    metadata = json.loads((Path(model_dir) / "lab07-model.json").read_text(encoding="utf-8"))
    absent = [name for name in ("model_version", "protocol_id") if not metadata.get(name)]
    if absent:
        raise ValueError(f"lab07-model.json lacks {', '.join(absent)}")
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=project_root, capture_output=True,
            text=True, check=True,
        ).stdout.strip() or "unknown"
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    pointer = Path(project_root) / "data" / "01_raw.dvc"
    match = MD5_LINE.search(pointer.read_text(encoding="utf-8")) if pointer.is_file() else None
    return {
        "model_version": str(metadata["model_version"]),
        "protocol_id": str(metadata["protocol_id"]),
        "git_commit": commit,
        "data_hash": match.group(1) if match else "unknown",
    }


def score_batch(predictor, serving, reality):
    """L08-E3 TODO. Score one batch against its delayed labels.

    Inputs: the loaded predictor, ``serving`` (``date,row_id,<FEATURES>``) and
    ``reality`` (``date,row_id,high_revenue`` as 0/1), both read with
    ``dtype={"row_id": str}``.

    1. Join ``serving[[KEY, *FEATURES]]`` and ``reality[[KEY, TARGET]]`` on ``row_id``,
       one row to one row. If a ``row_id`` is duplicated in either frame, or any row of
       either frame finds no partner, raise ``ValueError`` naming the counts (serving
       rows, reality rows, matched rows, duplicates).
    2. ``probability = predictor.predict_proba(merged[FEATURES])[1]``: the positive-class
       column, label ``1``, as in the Lab 07 API.
    3. Return plain Python numbers::

           {"n": matched rows, "roc_auc": roc_auc_score(labels, probability),
            "accuracy": accuracy_score(labels, probability >= 0.5),
            "mean_probability": mean of probability,
            "positive_rate": share of labels equal to 1}
    """
    raise NotImplementedError("L08-E3: implement score_batch in lab07/lab07/score_batches.py")


def schema_ok(reports, date):
    """True only when ``<reports>/<date>/schema.json`` exists and says ok (supplied)."""
    path = Path(reports) / date / "schema.json"
    if not path.is_file():
        return False
    return json.loads(path.read_text(encoding="utf-8")).get("ok") is True


def score_stream(predictor, stream, reports, identity):
    """One row per date of the stream, in date order (supplied)."""
    stream, rows = Path(stream), []
    dates = sorted(
        folder.name for folder in stream.iterdir()
        if folder.is_dir() and DATE_FOLDER.match(folder.name)
    )
    for date in dates:
        row = {"date": date, **dict.fromkeys(METRICS), **identity}
        if not schema_ok(reports, date):
            rows.append({**row, "status": "skipped: schema"})
            continue
        serving = pd.read_csv(stream / date / "serving.csv", dtype={KEY: str})
        reality_path = stream / date / "reality.csv"
        if not reality_path.is_file():
            raise FileNotFoundError(f"{date}: no reality.csv, the labels have not arrived")
        reality = pd.read_csv(reality_path, dtype={KEY: str})
        absent = [column for column in FEATURES if column not in serving]
        if absent:
            raise ValueError(f"{date}: schema.json says ok, but serving.csv lacks {absent}; "
                             "check check_schema and rerun validate")
        metrics = score_batch(predictor, serving, reality)
        if not isinstance(metrics, dict) or set(metrics) != set(METRICS):
            raise TypeError(f"score_batch must return a dict with exactly {METRICS}")
        rows.append({**row, "status": "scored", **metrics})
    types = {"n": "Int64", **dict.fromkeys(METRICS[1:], "float64")}
    return pd.DataFrame(rows, columns=COLUMNS).astype(types)


def load_predictor(model_dir):
    from autogluon.tabular import TabularPredictor

    return TabularPredictor.load(str(model_dir))


def main(argv=None, loader=load_predictor):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, type=Path, help="folder with lab07-model.json")
    parser.add_argument("--stream", required=True, type=Path, help="data/05_serving/<incident>")
    parser.add_argument("--reports", required=True, type=Path,
                        help="data/08_reporting/monitoring/<incident>, written by validate")
    args = parser.parse_args(argv)
    if not (args.model / "lab07-model.json").is_file():
        print(f"error: no trained model in {args.model} (lab07-model.json missing). The Lab 07 "
              "model is trained in Lab 07 L07-E2, not here: restore lab07/model from Git "
              "(git status model) or pass --model to the folder that holds it.",
              file=sys.stderr)
        return 1
    if not args.stream.is_dir():
        print(f"error: no stream folder {args.stream}; run highrev.monitoring simulate",
              file=sys.stderr)
        return 1
    if not args.reports.is_dir():
        print(f"error: no reports folder {args.reports}; run highrev.monitoring validate first",
              file=sys.stderr)
        return 1
    identity = model_identity(args.model, PROJECT_ROOT)
    predictor = loader(args.model)
    scores = score_stream(predictor, args.stream, args.reports, identity)
    target = args.reports / "scores.csv"
    staging = target.with_name("scores.csv.tmp")
    scores.to_csv(staging, index=False, lineterminator="\n")
    os.replace(staging, target)
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        shown = scores[["date", "status", *METRICS]].astype(object)
        print(shown.where(shown.notna(), "").to_string(index=False))
    print(f"Model {identity['model_version']}; wrote {target.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
