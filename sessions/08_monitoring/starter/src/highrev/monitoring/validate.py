"""Check every serving batch of a stream for schema breaks and drift (layer B, supplied).

For each date folder of the stream this writes ``<reports>/<date>/schema.json``
``{"date", "ok", "problems", "unseen_open"}`` and ``<reports>/<date>/drift.json``
``{"date", "columns", "drifted", "drift_share"}``; ``drift.html`` only for the date
given as ``html_date``. A schema break still gets a ``drift.json`` for the columns that
are present. ``unseen_open`` is information, not a problem: for each open-domain
column (``monitoring.open_domain_columns``) the values the reference never had, with
their row counts (``{}`` when there are none). Rerunning rewrites the same files
(idempotent).
"""

import json
import re
from pathlib import Path

import pandas as pd

from highrev.monitoring import KEY
from highrev.monitoring.drift import drift_summary
from highrev.monitoring.schema import check_schema, reference_domain

DATE_FOLDER = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def stream_dates(stream: Path) -> list[str]:
    """Sorted ``YYYY-MM-DD`` folders of a stream that contain ``serving.csv``."""
    stream = Path(stream)
    if not stream.is_dir():
        raise FileNotFoundError(f"No stream folder {stream}; generate it with simulate first")
    dates = sorted(
        folder.name
        for folder in stream.iterdir()
        if folder.is_dir() and DATE_FOLDER.match(folder.name) and (folder / "serving.csv").is_file()
    )
    if not dates:
        raise FileNotFoundError(f"No YYYY-MM-DD/serving.csv folders in {stream}")
    return dates


def unseen_open(batch: pd.DataFrame, domain: dict, open_columns) -> dict:
    """``{column: {value: rows}}`` of values unseen in the reference, per open column."""
    found = {}
    for column in open_columns:
        if column not in batch:
            continue
        present = batch[column].dropna().astype(str)
        counts = present[~present.isin(domain["categorical"][column]["values"])].value_counts()
        found[column] = {str(value): int(count) for value, count in sorted(counts.items())}
    return found


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    path.write_text(text, encoding="utf-8")


def validate_stream(
    reference: pd.DataFrame,
    stream: Path,
    reports: Path,
    thresholds: dict,
    html_date: str | None = None,
    open_columns=(),
) -> list[dict]:
    """Write the schema and drift verdicts of every batch; return one summary per date."""
    stream, reports = Path(stream), Path(reports)
    dates = stream_dates(stream)
    if html_date is not None and html_date not in dates:
        raise ValueError(f"--html {html_date} is not a date of {stream}: {', '.join(dates)}")
    domain = reference_domain(reference)
    unknown = [column for column in open_columns if column not in domain["categorical"]]
    if unknown:
        raise ValueError(f"open_domain_columns must be categorical features: {unknown}")
    summaries = []
    for date in dates:
        batch = pd.read_csv(stream / date / "serving.csv", dtype={KEY: str})
        problems = check_schema(batch, domain, open_columns)
        if not isinstance(problems, list) or not all(isinstance(p, str) for p in problems):
            raise TypeError("check_schema must return a list of strings")
        information = unseen_open(batch, domain, open_columns)
        verdict = {"date": date, "ok": not problems, "problems": problems}
        verdict["unseen_open"] = information
        write_json(reports / date / "schema.json", verdict)
        html_path = reports / date / "drift.html" if date == html_date else None
        if html_path is None:
            # an older report would disagree with the drift.json written below
            (reports / date / "drift.html").unlink(missing_ok=True)
        drift = drift_summary(reference, batch, thresholds, html_path=html_path)
        write_json(reports / date / "drift.json", {"date": date, **drift})
        summaries.append({"date": date, "problems": problems, "unseen_open": information, **drift})
    return summaries
