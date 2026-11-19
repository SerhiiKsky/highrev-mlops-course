"""Lab 08 scorer tests with a fake predictor. Run from lab07/:

    uv run --locked python -m pytest tests/test_score_batches.py -q

The score_batch tests fail with NotImplementedError until you finish L08-E3.
"""
import json

import pandas as pd
import pytest

from lab07.contracts import FEATURES, TARGET
from lab07.score_batches import COLUMNS, main, model_identity, score_batch


class FakePredictor:
    """Positive-class probability = pages_visited / 10; records the frames it sees."""

    def __init__(self):
        self.frames = []

    def predict_proba(self, frame):
        self.frames.append(frame.copy())
        probability = frame["pages_visited"].astype(float) / 10
        return pd.DataFrame({0: 1 - probability, 1: probability}, index=frame.index)


def batch(n=8):
    serving = pd.DataFrame({
        "date": "2026-10-01",
        "row_id": [f"r{i}" for i in range(n)],
        "pages_visited": [float(i) for i in range(n)],
        "age_first_order": 30.0, "gender": "F", "campaign": True,
        "ip_address_country": "Poland", "browser": "Chrome", "os": "Windows",
    })
    # Labels 1 exactly for the highest pages_visited: a perfect ranking.
    reality = pd.DataFrame({
        "date": "2026-10-01", "row_id": serving["row_id"],
        TARGET: [int(i >= n - 2) for i in range(n)],
    })
    return serving, reality.sample(frac=1, random_state=0)  # row order must not matter


def test_perfect_ranking_scores_auc_one():
    serving, reality = batch()
    predictor = FakePredictor()
    result = score_batch(predictor, serving, reality)
    assert set(result) == {"n", "roc_auc", "accuracy", "mean_probability", "positive_rate"}
    assert result["n"] == 8 and result["roc_auc"] == 1.0
    assert result["positive_rate"] == 0.25
    assert result["mean_probability"] == pytest.approx(0.35)
    assert result["accuracy"] == pytest.approx(7 / 8)  # 0.5 cut: rows 5, 6, 7 predicted 1
    assert list(predictor.frames[0].columns) == FEATURES


@pytest.mark.parametrize("change", ["lost", "duplicated"])
def test_lost_or_duplicated_row_is_rejected(change):
    serving, reality = batch()
    if change == "lost":
        reality = reality.iloc[1:]
    else:
        reality = pd.concat([reality, reality.iloc[:1]])
    # The message must name the counts; serving has 8 rows.
    with pytest.raises(ValueError, match=r"\b8\b"):
        score_batch(FakePredictor(), serving, reality)


def test_model_identity_without_git_or_pointer(tmp_path):
    model = tmp_path / "model"
    model.mkdir()
    metadata = {"model_version": "lab07-v9", "protocol_id": "abc"}
    (model / "lab07-model.json").write_text(json.dumps(metadata), encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "01_raw.dvc").write_text(
        "outs:\n- md5: 55bd.dir\n  size: 1\n  path: 01_raw\n", encoding="utf-8")
    identity = model_identity(model, tmp_path)
    assert identity["model_version"] == "lab07-v9" and identity["protocol_id"] == "abc"
    assert identity["data_hash"] == "55bd.dir"
    assert identity["git_commit"]  # a commit, or "unknown" outside a Git repository


def test_cli_skips_dates_without_an_ok_schema(tmp_path, monkeypatch):
    model, stream, reports = tmp_path / "model", tmp_path / "stream", tmp_path / "reports"
    model.mkdir()
    (model / "lab07-model.json").write_text(
        json.dumps({"model_version": "v", "protocol_id": "p"}), encoding="utf-8")
    serving, reality = batch()
    for date, ok in (("2026-10-01", None), ("2026-10-02", False)):
        (stream / date).mkdir(parents=True)
        serving.to_csv(stream / date / "serving.csv", index=False)
        reality.to_csv(stream / date / "reality.csv", index=False)
        if ok is not None:
            (reports / date).mkdir(parents=True)
            (reports / date / "schema.json").write_text(json.dumps({"ok": ok}), encoding="utf-8")
    reports.mkdir(exist_ok=True)
    code = main(["--model", str(model), "--stream", str(stream), "--reports", str(reports)],
                loader=lambda path: FakePredictor())
    scores = pd.read_csv(reports / "scores.csv")
    assert code == 0 and list(scores.columns) == COLUMNS
    assert scores["status"].tolist() == ["skipped: schema", "skipped: schema"]
    assert scores["roc_auc"].isna().all()


def test_cli_scores_an_ok_date_with_identity(tmp_path):
    model, stream, reports = tmp_path / "model", tmp_path / "stream", tmp_path / "reports"
    model.mkdir()
    (model / "lab07-model.json").write_text(
        json.dumps({"model_version": "v", "protocol_id": "p"}), encoding="utf-8")
    serving, reality = batch()
    (stream / "2026-10-01").mkdir(parents=True)
    serving.to_csv(stream / "2026-10-01" / "serving.csv", index=False)
    reality.to_csv(stream / "2026-10-01" / "reality.csv", index=False)
    (reports / "2026-10-01").mkdir(parents=True)
    (reports / "2026-10-01" / "schema.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    args = ["--model", str(model), "--stream", str(stream), "--reports", str(reports)]
    assert main(args, loader=lambda path: FakePredictor()) == 0
    assert main(args, loader=lambda path: FakePredictor()) == 0  # rewrites, no duplicate rows
    scores = pd.read_csv(reports / "scores.csv")
    assert scores["status"].tolist() == ["scored"] and scores["roc_auc"].tolist() == [1.0]
    assert scores["model_version"].tolist() == ["v"]


def test_cli_without_a_model_points_to_lab07(tmp_path, capsys):
    code = main(["--model", str(tmp_path / "missing"), "--stream", str(tmp_path),
                 "--reports", str(tmp_path)])
    assert code == 1 and "Lab 07" in capsys.readouterr().err
