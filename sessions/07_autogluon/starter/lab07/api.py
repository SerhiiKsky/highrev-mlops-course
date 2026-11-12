"""Serve one locally packaged AutoGluon predictor."""
import json
import math
import os
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, StrictBool

from lab07.contracts import FEATURES


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    pages_visited: float | None
    age_first_order: float | None
    gender: str | None
    campaign: StrictBool | None
    ip_address_country: str | None
    browser: str | None
    os: str | None


class Prediction(BaseModel):
    probability_high_revenue: float
    model_version: str


def create_app(loader=None):
    @asynccontextmanager
    async def lifespan(app):
        model_dir = Path(os.environ.get("MODEL_PATH", "model"))
        metadata = json.loads((model_dir / "lab07-model.json").read_text(encoding="utf-8"))
        if not metadata.get("model_version"):
            raise ValueError("model metadata must identify the model version")
        if loader is None:
            from autogluon.tabular import TabularPredictor
            predictor = TabularPredictor.load(str(model_dir))
        else:
            predictor = loader(model_dir)
        app.state.predictor = predictor
        app.state.model_version = metadata["model_version"]
        yield

    app = FastAPI(title="HighRev AutoGluon API", lifespan=lifespan)

    @app.api_route("/", methods=["GET", "HEAD"])
    def index():
        return {"service": "HighRev prediction API", "docs": "/docs", "health": "/health"}

    @app.get("/health")
    def health():
        return {"status": "ready", "model_version": app.state.model_version, "source_revision": os.environ.get("SOURCE_REVISION", "local")}

    @app.post("/predict", response_model=Prediction)
    def predict(customer: Customer):
        frame = pd.DataFrame([customer.model_dump()], columns=FEATURES)
        try:
            # TODO (student): call predict_proba(frame) and select label 1.
            # AutoGluon returns a DataFrame indexed by row with one column per class.
            raise NotImplementedError("Implement positive-class probability")
        except NotImplementedError:
            raise
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Model prediction failed") from exc
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise HTTPException(status_code=503, detail="Model returned invalid probability")
        return Prediction(probability_high_revenue=probability, model_version=app.state.model_version)

    return app


app = create_app()
