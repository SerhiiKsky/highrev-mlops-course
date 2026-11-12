import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from lab07.api import create_app


class FakePredictor:
    def predict_proba(self, frame):
        assert list(frame.columns) == ["pages_visited", "age_first_order", "gender", "campaign", "ip_address_country", "browser", "os"]
        return pd.DataFrame({0: [0.25], 1: [0.75]})


@pytest.fixture
def client(tmp_path, monkeypatch):
    (tmp_path / "lab07-model.json").write_text(json.dumps({"model_version": "example-v1"}), encoding="utf-8")
    monkeypatch.setenv("MODEL_PATH", str(tmp_path))
    with TestClient(create_app(loader=lambda _: FakePredictor())) as client:
        yield client


@pytest.fixture
def customer():
    return {"pages_visited": 5, "age_first_order": 32, "gender": "F", "campaign": True, "ip_address_country": "Poland", "browser": "Firefox", "os": "Linux"}


def test_health_and_prediction(client, customer):
    assert client.get("/").json()["health"] == "/health"
    assert client.head("/").status_code == 200
    assert client.get("/health").json() == {"status": "ready", "model_version": "example-v1", "source_revision": "local"}
    response = client.post("/predict", json=customer)
    assert response.status_code == 200
    assert response.json() == {"probability_high_revenue": 0.75, "model_version": "example-v1"}


def test_extra_target_and_invalid_campaign_rejected(client, customer):
    assert client.post("/predict", json={**customer, "high_revenue": 1}).status_code == 422
    assert client.post("/predict", json={**customer, "campaign": "yes"}).status_code == 422


def test_missing_model_prevents_startup(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_PATH", str(tmp_path))
    with pytest.raises(FileNotFoundError), TestClient(create_app(loader=lambda _: FakePredictor())):
        pass
