"""Lab 08 monitoring tests. Run: uv run --locked pytest tests/unit/test_monitoring.py -q

Tests of check_schema (names contain "schema": run them with -k schema) and of the
retraining tests (and decide, which uses them) fail with NotImplementedError until you
finish L08-E2 and L08-E4. The benchmark test is
optional: its tests are skipped while benchmark_test raises NotImplementedError.
"""

import json

import numpy as np
import pandas as pd
import pytest

from highrev.monitoring import CATEGORICAL, FEATURES, KEY, NUMERIC, TARGET
from highrev.monitoring.__main__ import MonitoringError, load_parameters, main
from highrev.monitoring.act import act
from highrev.monitoring.drift import drift_summary
from highrev.monitoring.retrain import (
    benchmark_test,
    decide,
    hard_test,
    iqr_test,
    parametric_test,
)
from highrev.monitoring.schema import check_schema, reference_domain
from highrev.monitoring.simulate import generate
from highrev.monitoring.validate import validate_stream

SETTINGS = {"days": 4, "start_day": 3, "batch_rows": 40, "seed": 7}


def make_pool(n):
    """A serving population with the Lab 06 columns and True/False labels."""
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            KEY: [f"customers:x:{i}" for i in range(n)],
            "pages_visited": rng.integers(1, 30, n).astype(float),
            "age_first_order": rng.normal(40, 10, n),
            "gender": rng.choice(np.array(["F", "M", None], dtype=object), n),
            "campaign": rng.choice([True, False], n),
            "ip_address_country": rng.choice(["Poland", "Germany", "Ukraine"], n),
            "browser": rng.choice(["Chrome", "Firefox", "Safari"], n),
            "os": rng.choice(["Windows", "Linux", "Mac OS X"], n),
            TARGET: rng.random(n) < 0.2,
        }
    )


@pytest.fixture
def pool():
    return make_pool(120)


def read_day(folder, name):
    return pd.read_csv(folder / name, dtype={KEY: str})


def day_folders(stream):
    return sorted(path for path in stream.iterdir() if path.is_dir())


# --- simulator (supplied code) ---------------------------------------------------------


def test_stream_layout_and_labels(pool, tmp_path):
    stream = generate(pool, tmp_path, "none", **SETTINGS)
    folders = day_folders(stream)
    assert [folder.name for folder in folders] == [
        "2026-10-01",
        "2026-10-02",
        "2026-10-03",
        "2026-10-04",
    ]
    serving = read_day(folders[0], "serving.csv")
    reality = read_day(folders[0], "reality.csv")
    assert list(serving.columns) == ["date", KEY, *FEATURES]
    assert list(reality.columns) == ["date", KEY, TARGET]
    assert len(serving) == SETTINGS["batch_rows"]
    assert reality[TARGET].dtype.kind in "iu" and set(reality[TARGET]) <= {0, 1}
    assert serving[KEY].tolist() == reality[KEY].tolist()


def test_same_seed_gives_the_same_stream(pool, tmp_path):
    first = generate(pool, tmp_path / "a", "concept", **SETTINGS)
    second = generate(pool, tmp_path / "b", "concept", **SETTINGS)
    for left, right in zip(day_folders(first), day_folders(second), strict=True):
        for name in ("serving.csv", "reality.csv"):
            assert (left / name).read_bytes() == (right / name).read_bytes()


def test_schema_incident_drops_browser_from_the_start_day(pool, tmp_path):
    folders = day_folders(generate(pool, tmp_path, "schema", **SETTINGS))
    assert "browser" in read_day(folders[1], "serving.csv")
    assert "browser" not in read_day(folders[2], "serving.csv")
    assert "browser" not in read_day(folders[3], "serving.csv")


def test_concept_keeps_marginals_and_labels(pool, tmp_path):
    clean = day_folders(generate(pool, tmp_path / "clean", "none", **SETTINGS))
    concept = day_folders(generate(pool, tmp_path / "concept", "concept", **SETTINGS))
    before, after = read_day(clean[2], "serving.csv"), read_day(concept[2], "serving.csv")
    for column in FEATURES:
        assert sorted(map(repr, before[column])) == sorted(map(repr, after[column]))
    assert before[KEY].tolist() == after[KEY].tolist()
    assert read_day(clean[2], "reality.csv").equals(read_day(concept[2], "reality.csv"))
    assert not before[FEATURES].equals(after[FEATURES])
    assert read_day(clean[1], "serving.csv").equals(read_day(concept[1], "serving.csv"))


def test_covariate_resamples_unique_rows_that_keep_their_labels(pool, tmp_path):
    folders = day_folders(generate(pool, tmp_path, "covariate", **SETTINGS))
    labels = pool.set_index(KEY)[TARGET].astype(int)
    for folder in folders[2:]:
        serving, reality = read_day(folder, "serving.csv"), read_day(folder, "reality.csv")
        assert serving[KEY].is_unique
        assert reality[TARGET].tolist() == labels.loc[reality[KEY]].tolist()
        original = pool.set_index(KEY).loc[serving[KEY], "pages_visited"]
        assert serving["pages_visited"].tolist() == original.tolist()


def test_existing_stream_is_refused_and_kept(pool, tmp_path):
    stream = generate(pool, tmp_path, "none", **SETTINGS)
    before = {path: path.read_bytes() for path in stream.rglob("*.csv")}
    with pytest.raises(FileExistsError, match="new name"):
        generate(pool, tmp_path, "none", **SETTINGS)
    assert {path: path.read_bytes() for path in stream.rglob("*.csv")} == before


@pytest.mark.parametrize(
    ("incident", "changes"),
    [
        ("unknown", {}),
        ("none", {"batch_rows": 121}),
        ("none", {"start_day": 5}),
        ("none", {"days": 0}),
    ],
)
def test_invalid_settings_write_nothing(pool, tmp_path, incident, changes):
    with pytest.raises(ValueError):
        generate(pool, tmp_path / "out", incident, **{**SETTINGS, **changes})
    assert not (tmp_path / "out").exists()


def test_infeasible_weighted_sampling_writes_nothing(pool, tmp_path):
    pool.loc[10:, "pages_visited"] = np.nan  # only 10 rows keep a positive weight
    with pytest.raises(ValueError, match="positive weight"):
        generate(pool, tmp_path / "out", "covariate", **SETTINGS)
    assert not (tmp_path / "out").exists()


# --- schema check (L08-E2 TODO) --------------------------------------------------------


@pytest.fixture
def domain(pool):
    return reference_domain(pool)


@pytest.fixture
def batch(pool):
    frame = pool.drop(columns=TARGET).head(30).copy()
    frame.insert(0, "date", "2026-10-01")
    return frame


def test_reference_domain_lists_values_as_strings(domain):
    assert domain["numeric"] == NUMERIC
    assert set(domain["categorical"]) == set(CATEGORICAL)
    assert domain["categorical"]["campaign"]["values"] == ["False", "True"]
    assert domain["categorical"]["gender"] == {"values": ["F", "M"], "missing": True}
    assert domain["categorical"]["os"]["missing"] is False


def test_check_schema_clean_batch_has_no_problems_and_is_not_modified(batch, domain):
    before = batch.copy()
    assert check_schema(batch, domain) == []
    pd.testing.assert_frame_equal(batch, before)


def test_check_schema_missing_column_is_reported_once(batch, domain):
    problems = check_schema(batch.drop(columns="browser"), domain)
    assert len(problems) == 1 and "browser" in problems[0]


def test_check_schema_unexpected_column_is_reported(batch, domain):
    problems = check_schema(batch.assign(high_revenue=1), domain)
    assert len(problems) == 1 and "high_revenue" in problems[0]


def test_check_schema_numeric_column_that_is_text_is_reported(batch, domain):
    problems = check_schema(batch.assign(pages_visited="many"), domain)
    assert len(problems) == 1 and "pages_visited" in problems[0]


def test_check_schema_unseen_category_names_values_and_counts(batch, domain):
    batch.loc[:11, "os"] = "Unknown-42"
    problems = check_schema(batch, domain)
    assert len(problems) == 1
    assert "os" in problems[0] and "Unknown-42" in problems[0] and "12" in problems[0]


def test_check_schema_missing_values_only_when_the_reference_had_none(batch, domain):
    batch.loc[:2, "gender"] = None  # the reference has missing gender: allowed
    assert check_schema(batch, domain) == []
    batch.loc[:2, "os"] = None  # the reference has no missing os
    problems = check_schema(batch, domain)
    assert len(problems) == 1 and "os" in problems[0] and "3" in problems[0]


def test_check_schema_unseen_value_in_an_open_column_is_not_a_problem(batch, domain):
    batch.loc[:1, "ip_address_country"] = "Togo"
    assert check_schema(batch, domain, open_columns=("ip_address_country",)) == []
    problems = check_schema(batch, domain)  # not listed as open: a closed domain
    assert len(problems) == 1 and "ip_address_country" in problems[0] and "Togo" in problems[0]


def test_validate_schema_json_reports_unseen_open_values_and_rewrites(pool, tmp_path):
    stream = generate(pool, tmp_path / "serving", "none", **{**SETTINGS, "days": 1, "start_day": 1})
    batch = read_day(stream / "2026-10-01", "serving.csv")
    batch.loc[:2, "ip_address_country"] = "Togo"
    batch.to_csv(stream / "2026-10-01" / "serving.csv", index=False)
    reports = tmp_path / "reports"
    for _ in range(2):  # idempotent: the second run rewrites the same files
        validate_stream(pool, stream, reports, THRESHOLDS, open_columns=("ip_address_country",))
    verdict = json.loads((reports / "2026-10-01" / "schema.json").read_text(encoding="utf-8"))
    assert verdict["ok"] is True and verdict["problems"] == []
    assert verdict["unseen_open"] == {"ip_address_country": {"Togo": 3}}
    drift = json.loads((reports / "2026-10-01" / "drift.json").read_text(encoding="utf-8"))
    assert drift["date"] == "2026-10-01" and set(drift["columns"]) == set(FEATURES)


# --- drift summary (supplied) ----------------------------------------------------------

THRESHOLDS = dict.fromkeys(FEATURES, 0.1)


@pytest.fixture(scope="module")
def large():
    # Above 1,000 reference rows Evidently uses distances (larger = more drift); at or
    # below it uses p-value tests, as for the 4,600-row fit.csv it does not.
    return make_pool(1500)


def test_identical_batch_shows_no_drift(large):
    summary = drift_summary(large, large, THRESHOLDS)
    assert list(summary["columns"]) == FEATURES
    assert summary["drifted"] == [] and summary["drift_share"] == 0.0
    for result in summary["columns"].values():
        assert set(result) == {"method", "score", "threshold", "drifted"}


def test_shifted_column_drifts_and_missing_column_is_left_out(large):
    batch = large.sample(500, random_state=1)
    shifted = batch.drop(columns="browser").assign(pages_visited=batch["pages_visited"] + 20)
    summary = drift_summary(large, shifted, THRESHOLDS)
    assert "browser" not in summary["columns"]
    assert summary["columns"]["pages_visited"]["method"] == "Wasserstein distance (normed)"
    assert summary["columns"]["gender"]["method"] == "Jensen-Shannon distance"
    assert summary["drifted"] == ["pages_visited"]


def test_evidently_counts_a_score_on_the_threshold_as_drift(large):
    # Identical data scores 0.0; with a threshold of 0.0 Evidently uses score >= threshold.
    summary = drift_summary(large, large, {**THRESHOLDS, "gender": 0.0})
    assert summary["columns"]["gender"]["score"] == 0.0
    assert summary["drifted"] == ["gender"]


# --- retraining tests (L08-E4 TODO) ----------------------------------------------------


def test_hard_test_is_strict():
    assert hard_test(0.64, 0.65) == {"fired": True, "limit": 0.65}
    assert hard_test(0.65, 0.65) == {"fired": False, "limit": 0.65}


def test_parametric_test_needs_history():
    assert parametric_test(0.1, [0.8, 0.8], k=2.0) == {"fired": False, "limit": None}


def test_parametric_test_uses_sample_std_and_strict_limit():
    history = [0.5, 0.75, 1.0]  # mean 0.75, sample std 0.25, limit 0.75 - 2 * 0.25
    assert parametric_test(0.25, history, k=2.0) == {"fired": False, "limit": 0.25}
    assert parametric_test(0.2499, history, k=2.0)["fired"] is True


def test_parametric_test_with_zero_spread():
    result = parametric_test(0.75, [0.75, 0.75, 0.75], k=2.0)
    assert result == {"fired": False, "limit": pytest.approx(0.75)}
    assert parametric_test(0.74, [0.75, 0.75, 0.75], k=2.0)["fired"] is True


def test_iqr_test_needs_four_readings():
    assert iqr_test(0.1, [0.7, 0.7, 0.7]) == {"fired": False, "limit": None}


def test_iqr_test_fence_is_strict():
    history = [0.5, 0.625, 0.75, 0.875]  # q1 0.59375, q3 0.78125, fence 0.3125
    assert iqr_test(0.3125, history) == {"fired": False, "limit": 0.3125}
    assert iqr_test(0.3, history)["fired"] is True


def test_iqr_test_with_zero_spread():
    assert iqr_test(0.75, [0.75] * 4) == {"fired": False, "limit": pytest.approx(0.75)}
    assert iqr_test(0.74, [0.75] * 4)["fired"] is True


def test_benchmark_test_optional():
    try:
        result = benchmark_test(0.75, [0.7, 0.8])
    except NotImplementedError:
        pytest.skip("optional benchmark_test not implemented")
    assert result == {"fired": True, "limit": 0.8}
    assert benchmark_test(0.8, [0.7, 0.8])["fired"] is False
    assert benchmark_test(0.5, []) == {"fired": False, "limit": None}


# L08-E4: add one boundary test of your own below.


# --- decision (supplied; uses your tests) ----------------------------------------------


def scores_frame(aucs, skipped=()):
    rows = []
    for day, auc in enumerate(aucs, start=1):
        date = f"2026-10-{day:02d}"
        status = "skipped: schema" if date in skipped else "scored"
        rows.append(
            {
                "date": date,
                "status": status,
                "roc_auc": None if status != "scored" else auc,
                "model_version": "lab07-v1",
                "protocol_id": "p",
                "git_commit": "c",
                "data_hash": "h.dir",
            }
        )
    return pd.DataFrame(rows)


CLEAN = [0.80, 0.70, 0.73, 0.71, 0.71]


def test_decide_retrains_when_the_latest_batch_falls_below_the_floor():
    signal = decide(scores_frame([*CLEAN, 0.58]), {}, [], floor=0.65, k=2.0)
    assert signal["action"] == "retrain"
    assert signal["latest_date"] == "2026-10-06" and signal["latest_roc_auc"] == 0.58
    assert [item["roc_auc"] for item in signal["history"]] == CLEAN
    assert signal["tests"]["hard"] == {"fired": True, "limit": 0.65}
    assert signal["model"]["model_version"] == "lab07-v1"
    json.dumps(signal, allow_nan=False)


def test_decide_investigates_a_missing_column_without_scores():
    aucs = [*CLEAN, 0.0, 0.0]
    skipped = ("2026-10-06", "2026-10-07")
    breaks = dict.fromkeys(skipped, ["missing column: browser"])
    signal = decide(scores_frame(aucs, skipped), breaks, [], floor=0.65, k=2.0)
    assert signal["action"] == "investigate"
    assert signal["latest_date"] == "2026-10-05" and len(signal["history"]) == 4
    assert "browser" in signal["reason"]


def test_decide_none_on_a_quiet_stream():
    signal = decide(scores_frame([*CLEAN, 0.74]), {}, [], floor=0.65, k=2.0)
    assert signal["action"] == "none"
    assert not any(result["fired"] for result in signal["tests"].values())


def test_decide_until_replays_an_earlier_day(tmp_path, monkeypatch, capsys):
    hard_test(0.5, 0.65)  # the CLI prints a NotImplementedError as an error; surface it here
    (tmp_path / "conf" / "base").mkdir(parents=True)
    snippet = {
        "monitoring": {
            **{"batch_rows": 500, "days": 10, "incident_start_day": 6, "seed": 7},
            "drift_threshold": THRESHOLDS,
            "open_domain_columns": ["ip_address_country"],
            "roc_auc_floor": 0.65,
            "parametric_k": 2.0,
        }
    }
    (tmp_path / "conf" / "base" / "parameters.yml").write_text(json.dumps(snippet), "utf-8")
    reports = tmp_path / "data" / "08_reporting" / "monitoring" / "concept"
    reports.mkdir(parents=True)
    scores_frame([*CLEAN, 0.58, 0.74]).to_csv(reports / "scores.csv", index=False)
    for day in range(1, 8):
        date = f"2026-10-{day:02d}"
        (reports / date).mkdir()
        (reports / date / "schema.json").write_text('{"ok": true, "problems": []}', "utf-8")
        (reports / date / "drift.json").write_text('{"drifted": []}', "utf-8")
    monkeypatch.chdir(tmp_path)
    args = ["decide", "--reports", "data/08_reporting/monitoring/concept"]
    assert main([*args, "--until", "2026-10-06"]) == 0
    replay = json.loads((reports / "retrain_signal_2026-10-06.json").read_text("utf-8"))
    assert replay["latest_date"] == "2026-10-06" and replay["action"] == "retrain"
    assert not (reports / "retrain_signal.json").exists()
    assert main(args) == 0
    latest = json.loads((reports / "retrain_signal.json").read_text("utf-8"))
    assert latest["latest_date"] == "2026-10-07" and latest["stream"] == "concept"
    capsys.readouterr()


def test_decide_without_any_scored_batch_investigates():
    signal = decide(scores_frame([0.0], ("2026-10-01",)), {"2026-10-01": ["x"]}, [], 0.65, 2.0)
    assert signal["action"] == "investigate" and signal["latest_date"] is None


# --- act and parameters (supplied) -----------------------------------------------------


def test_act_prints_commands_with_placeholders_for_retrain():
    signal = {
        "stream": "concept",
        "action": "retrain",
        "reason": "ROC AUC below the floor",
        "latest_date": "2026-10-10",
        "tests": {"hard": {"fired": True, "limit": 0.65}},
        "model": {"model_version": "lab07-v1"},
    }
    text = act(signal)
    for expected in ("<new-run>", "<next-version>", "lab07.train", "gate_reasons", "concept"):
        assert expected in text


def test_act_lists_what_to_inspect():
    signal = {
        "stream": "schema",
        "action": "investigate",
        "reason": "schema breaks",
        "latest_date": "2026-10-05",
        "schema_breaks": {"2026-10-06": ["missing column: browser"]},
        "drifted_latest": ["pages_visited"],
    }
    text = act(signal)
    assert "missing column: browser" in text and "--html" in text and "lab07.train" not in text


def test_missing_monitoring_section_names_the_snippet(tmp_path):
    (tmp_path / "conf" / "base").mkdir(parents=True)
    (tmp_path / "conf" / "base" / "parameters.yml").write_text("max_age: 100\n", encoding="utf-8")
    with pytest.raises(MonitoringError, match="parameters-snippet.yml"):
        load_parameters(tmp_path)
