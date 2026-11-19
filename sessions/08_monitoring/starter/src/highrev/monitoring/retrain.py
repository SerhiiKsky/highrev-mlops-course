"""Retraining tests on the outcome metric (layer C) and the retraining decision.

The three tests are the L08-E4 TODO; ``benchmark_test`` is optional. ``decide`` is
supplied. Every test compares the latest ROC AUC (higher is better) with a limit and
fires only when ``current < limit`` (strict). Each returns a dict::

    {"fired": bool, "limit": float}    # evaluated
    {"fired": False, "limit": None}    # not evaluated: not enough history

``history`` is the list of ROC AUC values of every earlier scored batch, oldest first.
"""

import pandas as pd

NOT_EVALUATED = {"fired": False, "limit": None}
TESTS = ("hard", "parametric", "iqr")
IDENTITY = ("model_version", "protocol_id", "git_commit", "data_hash")


def hard_test(current: float, floor: float) -> dict:
    """L08-E4 TODO. Fire when ``current`` is below the fixed ``floor``.

    The floor is the business's minimum (``monitoring.roc_auc_floor``); it needs no
    history. The limit is the floor itself. Return the dict shape of the module
    docstring with plain Python ``bool`` and ``float`` values.
    """
    raise NotImplementedError("L08-E4: implement hard_test in src/highrev/monitoring/retrain.py")


def parametric_test(current: float, history: list[float], k: float, min_history: int = 3) -> dict:
    """L08-E4 TODO. Fire when ``current`` is more than ``k`` standard deviations below normal.

    Too short a history (fewer than ``min_history`` readings) is not evaluated. The
    limit is ``k`` sample standard deviations below the historical mean; "sample"
    matters (see the API card). Return the dict shape of the module docstring.
    """
    raise NotImplementedError(
        "L08-E4: implement parametric_test in src/highrev/monitoring/retrain.py"
    )


def iqr_test(current: float, history: list[float], min_history: int = 4) -> dict:
    """L08-E4 TODO. Fire when ``current`` is below the lower Tukey fence of the history.

    Too short a history (fewer than ``min_history`` readings) is not evaluated. The
    limit is Tukey's lower fence: the first quartile minus 1.5 interquartile ranges,
    with numpy's default quantile method. Return the dict shape of the module docstring.
    """
    raise NotImplementedError("L08-E4: implement iqr_test in src/highrev/monitoring/retrain.py")


def benchmark_test(current: float, history: list[float]) -> dict:
    """Optional L08-E4 TODO. Fire when ``current`` is below the best earlier reading.

    An empty history is not evaluated; the limit is the best earlier reading. Not part
    of ``decide``: work out how often it would fire on your clean ``scores.csv``.
    """
    raise NotImplementedError(
        "L08-E4 (optional): implement benchmark_test in src/highrev/monitoring/retrain.py"
    )


def _checked(name: str, result: object) -> dict:
    """Plain JSON values, and a clear message when a test returns the wrong shape."""
    if not isinstance(result, dict) or set(result) != {"fired", "limit"}:
        raise TypeError(f"{name}_test must return {{'fired': bool, 'limit': float or None}}")
    limit = result["limit"]
    return {"fired": bool(result["fired"]), "limit": None if limit is None else float(limit)}


def _describe(name: str, result: dict, current: float) -> str:
    labels = {"hard": "the floor", "parametric": "mean - k*std", "iqr": "the IQR fence"}
    if result["limit"] is None:
        return f"{name}: not evaluated (history too short)"
    relation = "below" if result["fired"] else "not below"
    return f"{name}: {current:.3f} {relation} {labels[name]} {result['limit']:.3f}"


def decide(
    scores: pd.DataFrame,
    schema_breaks: dict,
    drifted_latest: list[str],
    floor: float,
    k: float,
) -> dict:
    """Combine the three tests, schema breaks and drift into one decision (supplied).

    ``scores`` is ``scores.csv`` of one stream; only rows with ``status == "scored"`` count.
    The latest scored batch is tested against every earlier scored batch (its history).
    ``schema_breaks`` maps each date whose ``schema.json`` is not ok to its problems;
    ``drifted_latest`` lists the drifted columns of the stream's latest ``drift.json``.

    ``action`` is ``retrain`` if any test fires on the latest scored batch,
    ``investigate`` if none fires but a schema break or a drifted column exists, else
    ``none``. Returns the signal without ``checked_at`` and ``stream`` (the CLI adds them).
    """
    scored = scores[scores["status"] == "scored"].sort_values("date")
    drifted_latest = list(drifted_latest)
    evidence = []
    if schema_breaks:
        dates = sorted(schema_breaks)
        problems = sorted({problem for found in schema_breaks.values() for problem in found})
        evidence.append(
            f"schema breaks on {len(dates)} date(s) {dates[0]}..{dates[-1]} "
            f"({'; '.join(problems)}); those batches were not scored"
        )
    if drifted_latest:
        evidence.append(f"drifted columns on the latest batch: {', '.join(drifted_latest)}")

    if scored.empty:
        tests = {name: dict(NOT_EVALUATED) for name in TESTS}
        identity = {}
        latest_date, current, history = None, None, []
        action = "investigate"
        reason = "; ".join(
            ["no batch has been scored yet: check the labels and run the scorer", *evidence]
        )
    else:
        latest = scored.iloc[-1]
        latest_date, current = str(latest["date"]), float(latest["roc_auc"])
        earlier = scored.iloc[:-1]
        history = [
            {"date": str(date), "roc_auc": float(auc)}
            for date, auc in zip(earlier["date"], earlier["roc_auc"], strict=True)
        ]
        values = [item["roc_auc"] for item in history]
        tests = {
            "hard": _checked("hard", hard_test(current, floor)),
            "parametric": _checked("parametric", parametric_test(current, values, k)),
            "iqr": _checked("iqr", iqr_test(current, values)),
        }
        identity = {name: str(latest[name]) for name in IDENTITY if name in latest}
        fired = [name for name in TESTS if tests[name]["fired"]]
        details = "; ".join(_describe(name, tests[name], current) for name in TESTS)
        if fired:
            action = "retrain"
            reason = (
                f"ROC AUC {current:.3f} on {latest_date} fired {', '.join(fired)} "
                f"against {len(values)} earlier batch(es) ({details})"
            )
        elif evidence:
            action = "investigate"
            reason = "; ".join(
                [f"no test fired on {latest_date} (ROC AUC {current:.3f}; {details})", *evidence]
            )
        else:
            action = "none"
            reason = (
                f"no test fired on {latest_date} (ROC AUC {current:.3f}; {details}); "
                "no schema break and no drifted column"
            )
    return {
        "latest_date": latest_date,
        "latest_roc_auc": current,
        "history": history,
        "tests": tests,
        "schema_breaks": {date: list(schema_breaks[date]) for date in sorted(schema_breaks)},
        "drifted_latest": drifted_latest,
        "action": action,
        "reason": reason,
        "model": identity,
    }
