"""Lab 08 monitoring commands (supplied). Run them from the project root, for example:

    uv run --locked python -m highrev.monitoring simulate --comparison "$run/comparison" \\
        --incident none
    uv run --locked python -m highrev.monitoring validate --comparison "$run/comparison" \\
        --stream data/05_serving/none --html 2026-10-10
    uv run --locked python -m highrev.monitoring decide --reports data/08_reporting/monitoring/none
    uv run --locked python -m highrev.monitoring decide \\
        --reports data/08_reporting/monitoring/concept --until 2026-10-06
    uv run --locked python -m highrev.monitoring act \\
        --signal data/08_reporting/monitoring/concept/retrain_signal.json

Scoring runs in the AutoGluon environment: ``(cd lab07 && uv run --locked python -m
lab07.score_batches ...)``. Every number comes from ``monitoring`` in
``conf/base/parameters.yml``.
"""

import argparse
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import yaml

from highrev.monitoring import CATEGORICAL, FEATURES, KEY, TARGET
from highrev.monitoring.act import act
from highrev.monitoring.retrain import decide
from highrev.monitoring.simulate import DESCRIPTIONS, INCIDENTS, generate
from highrev.monitoring.validate import stream_dates, validate_stream, write_json

PARAMETERS = Path("conf/base/parameters.yml")
SERVING = Path("data/05_serving")
REPORTS = Path("data/08_reporting/monitoring")
SNIPPET = "$course/sessions/08_monitoring/parameters-snippet.yml"


class MonitoringError(Exception):
    """A problem the student can fix; printed without a traceback."""


def load_parameters(root: Path) -> dict:
    """Return the checked ``monitoring`` section of ``conf/base/parameters.yml``."""
    path = root / PARAMETERS
    if not path.is_file():
        raise MonitoringError(f"No {PARAMETERS} under {root}: run from your project root.")
    section = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("monitoring")
    if not isinstance(section, dict):
        raise MonitoringError(
            f"{PARAMETERS} has no 'monitoring' section. Append {SNIPPET} to it unchanged (L08-E1)."
        )
    problems = []
    for name in ("batch_rows", "days", "incident_start_day", "seed"):
        value = section.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            problems.append(f"{name} must be a non-negative integer")
    numbers = {"roc_auc_floor": (0.0, 1.0), "parametric_k": (0.0, math.inf)}
    for name, (low, high) in numbers.items():
        value = section.get(name)
        if isinstance(value, bool) or not isinstance(value, int | float) or not low < value <= high:
            problems.append(f"{name} must be a number in ({low}, {high}]")
    thresholds = section.get("drift_threshold")
    if not isinstance(thresholds, dict):
        problems.append("drift_threshold must map every feature to a threshold")
    else:
        for column in FEATURES:
            value = thresholds.get(column)
            if isinstance(value, bool) or not isinstance(value, int | float) or not value > 0:
                problems.append(f"drift_threshold.{column} must be a positive number")
        unknown = sorted(set(thresholds) - set(FEATURES))
        if unknown:
            problems.append(f"drift_threshold has unknown columns: {', '.join(unknown)}")
    open_columns = section.get("open_domain_columns")
    if not isinstance(open_columns, list) or not set(open_columns) <= set(CATEGORICAL):
        problems.append(
            "open_domain_columns must be a list of categorical features "
            f"({', '.join(CATEGORICAL)}); the snippet lists ip_address_country"
        )
    if problems:
        raise MonitoringError(f"Fix monitoring in {PARAMETERS}: " + "; ".join(problems))
    return section


def read_partition(comparison: Path, name: str) -> pd.DataFrame:
    """Read ``training-input/<name>.csv`` of the Lab 06 run and check its columns."""
    path = Path(comparison) / "training-input" / f"{name}.csv"
    if not path.is_file():
        raise MonitoringError(
            f"No {path}: --comparison must be the comparison folder of your Lab 06 run, "
            'usually "$run/comparison".'
        )
    frame = pd.read_csv(path, dtype={KEY: str})
    missing = [column for column in (KEY, *FEATURES, TARGET) if column not in frame]
    if missing:
        raise MonitoringError(
            f"{path} lacks {', '.join(missing)}; expected the Lab 06 export with "
            f"{KEY}, the features {', '.join(FEATURES)} and {TARGET}."
        )
    return frame


def reports_for(root: Path, stream: Path) -> Path:
    """``data/05_serving/<x>`` reports to ``data/08_reporting/monitoring/<x>``."""
    stream = (root / stream).resolve()
    try:
        relative = stream.relative_to((root / SERVING).resolve())
    except ValueError:
        raise ValueError(
            f"{stream} is outside {SERVING.as_posix()}; keep streams there "
            "(--out data/05_serving/<new-folder>) so their reports cannot collide"
        ) from None
    return root / REPORTS / relative


def _simulate(args: argparse.Namespace, root: Path) -> None:
    params = load_parameters(root)
    reports_for(root, args.out / args.incident)  # refuse a stream outside data/05_serving early
    pool = read_partition(args.comparison, "validation")
    folder = generate(
        pool,
        args.out,  # relative to the project root (the cwd), so messages stay short
        args.incident,
        days=params["days"],
        start_day=params["incident_start_day"],
        batch_rows=params["batch_rows"],
        seed=params["seed"],
    )
    print(
        f"Incident {args.incident} from day {params['incident_start_day']}: "
        f"{DESCRIPTIONS[args.incident]}"
    )
    for date in stream_dates(folder):
        reality = pd.read_csv(folder / date / "reality.csv")
        print(f"  {date}: {len(reality)} rows, {reality[TARGET].mean():.1%} positive")
    print(f"Wrote {folder.as_posix()}")


def _validate(args: argparse.Namespace, root: Path) -> None:
    params = load_parameters(root)
    reference = read_partition(args.comparison, "fit")
    reports = reports_for(root, args.stream)
    summaries = validate_stream(
        reference,
        root / args.stream,
        reports,
        params["drift_threshold"],
        html_date=args.html,
        open_columns=tuple(params["open_domain_columns"]),
    )
    for summary in summaries:
        problems = "; ".join(summary["problems"])
        schema = f"schema: {problems}" if problems else "schema ok"
        drifted = [
            f"{column} {summary['columns'][column]['score']:.3f}" for column in summary["drifted"]
        ]
        counts = {column: sum(values.values()) for column, values in summary["unseen_open"].items()}
        new = [
            f"{column} {count} row{'' if count == 1 else 's'}"
            for column, count in counts.items()
            if count
        ]
        print(
            f"  {summary['date']}: {schema}; drifted: {', '.join(drifted) or 'none'}"
            + (f"; new values (open): {', '.join(new)}" if new else "")
        )
    print(f"Wrote {reports.relative_to(root).as_posix()}/<date>/{{schema,drift}}.json")
    if args.html:
        print(f"HTML report: {reports.relative_to(root).as_posix()}/{args.html}/drift.html")


def _decide(args: argparse.Namespace, root: Path) -> None:
    params = load_parameters(root)
    reports = root / args.reports
    scores_path = reports / "scores.csv"
    if not scores_path.is_file():
        raise MonitoringError(
            f"No {scores_path}: run validate, then lab07.score_batches "
            f"with --reports {args.reports}."
        )
    scores = pd.read_csv(scores_path, dtype={"date": str})
    dates = sorted(
        folder.name for folder in reports.iterdir() if (folder / "schema.json").is_file()
    )
    if not dates:
        raise MonitoringError(f"No <date>/schema.json under {reports}: run validate first.")
    if args.until is not None:
        # Replay the decision as it would have been made on that day.
        scores = scores[scores["date"] <= args.until]
        dates = [date for date in dates if date <= args.until]
        if not dates:
            raise MonitoringError(f"No validated date on or before --until {args.until}.")
    schema_breaks, drifted_latest = {}, []
    for date in dates:
        verdict = json.loads((reports / date / "schema.json").read_text(encoding="utf-8"))
        if not verdict["ok"]:
            schema_breaks[date] = verdict["problems"]
    drift_path = reports / dates[-1] / "drift.json"
    if drift_path.is_file():
        drifted_latest = json.loads(drift_path.read_text(encoding="utf-8"))["drifted"]
    decision = decide(
        scores, schema_breaks, drifted_latest, params["roc_auc_floor"], params["parametric_k"]
    )
    try:
        stream = reports.resolve().relative_to((root / REPORTS).resolve()).as_posix()
    except ValueError:
        stream = reports.name
    signal = {
        "checked_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "stream": stream,
        **decision,
    }
    name = "retrain_signal.json" if args.until is None else f"retrain_signal_{args.until}.json"
    write_json(reports / name, signal)
    print(json.dumps(signal, indent=2, ensure_ascii=False))


def _act(args: argparse.Namespace, root: Path) -> None:
    path = root / args.signal
    if not path.is_file():
        raise MonitoringError(f"No {path}: run decide first.")
    print(act(json.loads(path.read_text(encoding="utf-8"))), end="")


def _date(text: str) -> str:
    try:
        return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {text!r}") from exc


def parser() -> argparse.ArgumentParser:
    main_parser = argparse.ArgumentParser(
        prog="python -m highrev.monitoring",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = main_parser.add_subparsers(dest="command", required=True)
    simulate = commands.add_parser("simulate", help="write a dated stream of serving batches")
    simulate.add_argument("--comparison", required=True, type=Path, help='"$run/comparison"')
    simulate.add_argument("--incident", required=True, choices=INCIDENTS)
    simulate.add_argument(
        "--out",
        type=Path,
        default=SERVING,
        help="parent folder of the stream (default data/05_serving)",
    )
    validate = commands.add_parser("validate", help="schema and drift verdicts for every batch")
    validate.add_argument("--comparison", required=True, type=Path, help='"$run/comparison"')
    validate.add_argument("--stream", required=True, type=Path)
    validate.add_argument("--html", metavar="DATE", help="also write drift.html for this date")
    decide_parser = commands.add_parser("decide", help="write and print the retraining signal")
    decide_parser.add_argument("--reports", required=True, type=Path)
    decide_parser.add_argument(
        "--until",
        type=_date,
        metavar="YYYY-MM-DD",
        help="decide as on that day: ignore later dates; writes retrain_signal_<until>.json",
    )
    act_parser = commands.add_parser("act", help="print the next steps for a signal")
    act_parser.add_argument("--signal", required=True, type=Path)
    return main_parser


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path.cwd().resolve()
    handlers = {"simulate": _simulate, "validate": _validate, "decide": _decide, "act": _act}
    try:
        handlers[args.command](args, root)
    except (
        MonitoringError,
        NotImplementedError,
        FileExistsError,
        FileNotFoundError,
        ValueError,
        TypeError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
