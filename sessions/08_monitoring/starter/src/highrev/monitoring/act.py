"""Turn a retraining signal into the project's own next steps (supplied).

This prints commands; it executes nothing. "Retrain" in this project means: version the
new labelled data, run a new Lab 06 comparison, train an AutoGluon candidate as in
Lab 07, score it, and let the Lab 06 gate decide. A blind retraining script would skip
every one of those checks.
"""

from highrev.monitoring.retrain import TESTS

PLACEHOLDERS = """\
Replace every placeholder before you run a line:
  <new-run>       a NEW Lab 06 run directory outside the project, for example
                  "$(dirname "$project")/lab06-run-02"; never reuse "$run"
  <next-version>  the candidate's version, for example lab07-v2; never reuse a version
  <candidate>     a new folder inside lab07/ for the candidate, for example
                  model-<next-version>; never overwrite lab07/model
  <labels-date>   the last date whose labels the new data contains"""


def _header(signal: dict) -> list[str]:
    model = signal.get("model") or {}
    lines = [
        f"Stream {signal.get('stream')}: action {signal['action']}",
        f"Reason: {signal['reason']}",
    ]
    if model:
        lines.append(
            "Model in service: {model_version} (protocol {protocol}, commit {commit}, "
            "data {data_hash})".format(
                model_version=model.get("model_version", "unknown"),
                protocol=str(model.get("protocol_id", "unknown"))[:12],
                commit=str(model.get("git_commit", "unknown"))[:12],
                data_hash=model.get("data_hash", "unknown"),
            )
        )
    tests = signal.get("tests") or {}
    fired = [name for name in TESTS if tests.get(name, {}).get("fired")]
    if fired:
        lines.append(f"Fired on {signal.get('latest_date')}: {', '.join(fired)}")
    return lines


def _retrain(signal: dict) -> list[str]:
    stream = signal.get("stream", "<stream>")
    return [
        "",
        "Nothing has been run. These are the steps, in order, with your project's commands.",
        PLACEHOLDERS,
        "",
        "1. New labelled data first. Retraining on the same partitions reproduces the",
        "   same model. Put the rows whose labels arrived into data/01_raw, then version",
        "   them as in Lab 05:",
        '     cd "$project"',
        "     uv run --locked dvc add data/01_raw",
        "     git add data/01_raw.dvc",
        '     git commit -m "Data: labels up to <labels-date>"',
        "     uv run --locked dvc push",
        "",
        "2. A new Lab 06 comparison on that data version (L06-E2; same helpers):",
        '     source "$project/lab06/shell_helpers.sh"',
        '     project_python=$(venv_python "$project/.venv")',
        '     export PYTHON_BIN="$project_python"',
        "     commit=$(git rev-parse HEAD)",
        "     data_hash=$(sed -n 's/^- md5: //p' data/01_raw.dvc)",
        '     bash "$project/lab06/new_config.sh" "$project" "<new-run>" "$commit" "$data_hash"',
        '     export PYTHONPATH="$(native_path "$project/lab06/src")"',
        "     export MLFLOW_DISABLE_AGENT_HINT=1 PYTHONUTF8=1",
        '     (cd "<new-run>" && "$project_python" -X utf8 -m highrev.lab06 run \\',
        '         --config "<new-run>/config.json")',
        "     unset PYTHONPATH",
        "",
        "3. Train an AutoGluon candidate on the new partitions (L07-E2). For a candidate",
        "   you intend to deploy, use the Dockerfile.train image of L07-E2 instead, with",
        "   --output /output/<candidate> --version <next-version>.",
        '     cd "$project/lab07"',
        '     uv run --locked python -m lab07.train --comparison "<new-run>/comparison" \\',
        "         --output <candidate> --version <next-version>",
        "",
        "4. Score this stream with the candidate, next to the champion's reports. Copying",
        "   keeps the schema verdicts the scorer needs; scores.csv is then rewritten for",
        "   the candidate. Batches whose labels the candidate trained on are not evidence.",
        '     cd "$project"',
        f"     cp -R data/08_reporting/monitoring/{stream} "
        f"data/08_reporting/monitoring/{stream}-<next-version>",
        "     (cd lab07 && uv run --locked python -m lab07.score_batches --model <candidate> \\",
        f"         --stream ../data/05_serving/{stream} \\",
        f"         --reports ../data/08_reporting/monitoring/{stream}-<next-version>)",
        "     uv run --locked python -m highrev.monitoring decide \\",
        f"         --reports data/08_reporting/monitoring/{stream}-<next-version>",
        "",
        "5. The Lab 06 gate decides, not this signal: gate_reasons(candidate, champion,",
        "   policy) in lab06/src/highrev/lab06/learning_tasks.py with the policy of",
        "   <new-run>/config.json. An empty list means the candidate may replace",
        "   lab07/model; MLflow registration of AutoGluon models comes in Lab 10. The two",
        "   validation AUCs come from different validation partitions: compare them with",
        "   step 4, on the same batches, before you trust the difference.",
        '     cd "$project"',
        "   Paste the block below unindented; the heredoc ends at the line PY.",
        'PYTHONPATH="$(native_path "$project/lab06/src")" "$project_python" - <<\'PY\'',
        "import json",
        "from highrev.lab06.learning_tasks import gate_reasons",
        "def card(path):",
        '    m = json.load(open(path, encoding="utf-8"))',
        '    return {"metrics": {"validation_roc_auc": m["validation_roc_auc"],',
        '                        "predict_p95_ms": m["prediction_p95_ms"]},',
        '            "artifact_bytes": m["artifact_bytes_before_metadata"]}',
        'policy = json.load(open("<new-run>/config.json", encoding="utf-8"))["policy"]',
        'print(gate_reasons(card("lab07/<candidate>/lab07-model.json"),',
        '                   card("lab07/model/lab07-model.json"), policy) or "passes")',
        "PY",
    ]


def _investigate(signal: dict) -> list[str]:
    stream = signal.get("stream", "<stream>")
    lines = ["", "Nothing has been run. Do not retrain: no outcome test fired."]
    breaks = signal.get("schema_breaks") or {}
    if breaks:
        lines += [
            "",
            "Schema breaks (these batches were not scored, so layer C is blind there):",
        ]
        for date, problems in breaks.items():
            lines.append(f"  {date}: {'; '.join(problems)}")
        first = next(iter(breaks))
        lines += [
            "Inspect the batch and the upstream producer; fix the source, not the check:",
            f"  head -3 data/05_serving/{stream}/{first}/serving.csv",
            f"  cat data/08_reporting/monitoring/{stream}/{first}/schema.json",
        ]
    drifted = signal.get("drifted_latest") or []
    if drifted:
        lines += [
            "",
            f"Drifted columns on the latest batch: {', '.join(drifted)}",
            "Open the Evidently report of that date; <date> is the latest date folder under",
            f"data/08_reporting/monitoring/{stream}/:",
            "  uv run --locked python -m highrev.monitoring validate \\",
            f'      --comparison "$run/comparison" --stream data/05_serving/{stream} --html <date>',
            f"  then open data/08_reporting/monitoring/{stream}/<date>/drift.html",
            "Decide whether the shift is real, whether layer C moved with it, and whether the",
            "threshold is wrong. Record the evidence in notes/session-08.md.",
        ]
    if signal.get("latest_date") is None:
        lines += [
            "",
            "No batch was scored: check that reality.csv files exist and run lab07.score_batches.",
        ]
    return lines


def act(signal: dict) -> str:
    """Return the text for one signal; ``action`` is retrain, investigate or none."""
    action = signal.get("action")
    if action not in ("retrain", "investigate", "none"):
        raise ValueError(f"Unknown action {action!r} in the signal")
    lines = _header(signal)
    if action == "retrain":
        lines += _retrain(signal)
    elif action == "investigate":
        lines += _investigate(signal)
    else:
        lines += ["", "No action. Keep monitoring; check again when the next labels arrive."]
    return "\n".join(lines) + "\n"
