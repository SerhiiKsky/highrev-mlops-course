"""The system's prediction service: the Lab 07 contract, a swappable model, a request log.

Differences from ``lab07.api`` (which still serves the baked Render image):

* The model comes from the serving folder, chosen by ``$SERVING_DIR/current.json``
  that a deploy writes (by hand in Lab 09; from a registry alias once Lab 10 adds
  one). No MLflow client here: the API keeps serving if MLflow is down.
* Running, live and ready are different. The process starts without a model (live,
  not ready) and ``/ready`` answers 503 until a model is loaded. Set
  ``STRICT_STARTUP=1`` to exit instead when no model loads.
* ``POST /admin/reload`` loads the pointer again. A model that fails to load is
  refused and the previous one keeps serving.
* Every prediction is appended to ``$SERVING_DIR/predictions/<date>.jsonl`` with the
  model version and the caller's ``X-Request-ID``: the raw material for monitoring
  served traffic. The request and response bodies are unchanged from Lab 07.
"""

import json
import math
import os
import threading
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Response

from lab07.api import Customer, Prediction
from lab07.contracts import FEATURES


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _default_loader(model_dir: Path):
    from autogluon.tabular import TabularPredictor

    return TabularPredictor.load(str(model_dir))


class ModelSlot:
    """The one loaded model and its identity; swapped under a lock."""

    def __init__(self, serving_dir: Path, loader):
        self.serving_dir = serving_dir
        self.loader = loader
        self.lock = threading.Lock()
        self.predictor = None
        self.identity: dict = {}
        self.error: str | None = None

    def load(self) -> dict:
        pointer_path = self.serving_dir / "current.json"
        if not pointer_path.is_file():
            raise FileNotFoundError(f"No {pointer_path}: nothing deployed yet")
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        model_dir = self.serving_dir / pointer["path"]
        metadata = json.loads((model_dir / "lab07-model.json").read_text(encoding="utf-8"))
        if metadata.get("model_version") != pointer.get("model_version"):
            raise ValueError(
                f"Pointer names {pointer.get('model_version')} but {model_dir} holds "
                f"{metadata.get('model_version')}"
            )
        predictor = self.loader(model_dir)
        identity = {
            "model_version": pointer["model_version"],
            "registry_version": pointer.get("registry_version"),
            "data_hash": pointer.get("data_hash"),
            "loaded_at": _now(),
        }
        with self.lock:
            self.predictor, self.identity, self.error = predictor, identity, None
        return identity


def create_app(loader=None, serving_dir: Path | None = None):
    slot = ModelSlot(
        Path(serving_dir or os.environ.get("SERVING_DIR", "/serving")), loader or _default_loader
    )
    log_lock = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        try:
            slot.load()
        except Exception as exc:  # noqa: BLE001 - reported on /health, never hidden
            slot.error = f"{type(exc).__name__}: {exc}"
            if os.environ.get("STRICT_STARTUP") == "1":
                raise
        yield

    app = FastAPI(title="HighRev system API", lifespan=lifespan)
    app.state.slot = slot

    @app.api_route("/", methods=["GET", "HEAD"])
    def index():
        return {"service": "HighRev prediction API", "docs": "/docs", "health": "/health"}

    @app.get("/health")
    def health():
        """Liveness plus identity: the process answers, and says what it serves."""
        return {
            "status": "live",
            "ready": slot.predictor is not None,
            **slot.identity,
            "source_revision": os.environ.get("SOURCE_REVISION", "local"),
            "error": slot.error,
        }

    @app.get("/ready")
    def ready(response: Response):
        """Readiness: a model is loaded and can answer /predict."""
        if slot.predictor is None:
            response.status_code = 503
            return {"ready": False, "error": slot.error}
        return {"ready": True, **slot.identity}

    @app.post("/admin/reload")
    def reload(x_admin_token: str | None = Header(default=None)):
        expected = os.environ.get("ADMIN_TOKEN")
        if expected and x_admin_token != expected:
            raise HTTPException(status_code=403, detail="Wrong or missing X-Admin-Token")
        before = dict(slot.identity)
        try:
            after = slot.load()
        except Exception as exc:  # noqa: BLE001
            slot.error = f"reload refused: {type(exc).__name__}: {exc}"
            raise HTTPException(
                status_code=409,
                detail={"error": slot.error, "still_serving": before.get("model_version")},
            ) from exc
        return {"before": before.get("model_version"), "after": after["model_version"], **after}

    @app.post("/predict", response_model=Prediction)
    def predict(
        customer: Customer,
        response: Response,
        x_request_id: str | None = Header(default=None),
        x_serving_date: str | None = Header(default=None),
    ):
        with slot.lock:
            predictor, identity = slot.predictor, dict(slot.identity)
        if predictor is None:
            raise HTTPException(status_code=503, detail="No model loaded")
        record = customer.model_dump()
        frame = pd.DataFrame([record], columns=FEATURES)
        try:
            probability = float(predictor.predict_proba(frame)[1].iloc[0])
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Model prediction failed") from exc
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise HTTPException(status_code=503, detail="Model returned invalid probability")
        entry = {
            "ts": _now(),
            "request_id": x_request_id,
            "model_version": identity["model_version"],
            **record,
            "probability_high_revenue": probability,
        }
        day = x_serving_date or entry["ts"][:10]
        if not (len(day) == 10 and day[4] == "-" and day[7] == "-"):
            raise HTTPException(status_code=422, detail="X-Serving-Date must be YYYY-MM-DD")
        log = slot.serving_dir / "predictions" / f"{day}.jsonl"
        with log_lock:
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(entry) + "\n")
        response.headers["X-Model-Version"] = identity["model_version"]
        return Prediction(probability_high_revenue=probability, model_version=identity["model_version"])

    return app


app = create_app()
