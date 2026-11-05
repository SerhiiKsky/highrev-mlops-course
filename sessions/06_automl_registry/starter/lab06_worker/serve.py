"""Serve one immutable MLflow model version with a small JSON contract."""

import os
import re
from contextlib import asynccontextmanager

import mlflow
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field, StrictBool

FEATURES = [
    "pages_visited",
    "age_first_order",
    "gender",
    "campaign",
    "ip_address_country",
    "browser",
    "os",
]


class CustomerFeatures(BaseModel):
    """Prepared features, available at the agreed prediction time."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    pages_visited: float | None
    age_first_order: float | None
    gender: str | None
    campaign: StrictBool | None
    ip_address_country: str | None
    browser: str | None
    os: str | None


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: list[CustomerFeatures] = Field(min_length=1, max_length=256)


class PredictionResponse(BaseModel):
    model_uri: str
    probabilities: list[float]


def create_app(model_loader=None):
    """A loader argument keeps request tests independent of training."""

    @asynccontextmanager
    async def lifespan(application):
        model_uri = os.environ["LAB06_MODEL_URI"]
        if not re.fullmatch(r"models:/[^/]+/[1-9][0-9]*", model_uri):
            raise ValueError(
                "LAB06_MODEL_URI must pin a registered version: models:/NAME/1"
            )
        mlflow.set_tracking_uri(os.environ["LAB06_TRACKING_URI"])
        loader = model_loader or mlflow.pyfunc.load_model
        application.state.model = loader(model_uri)
        application.state.model_uri = model_uri
        yield
        del application.state.model

    application = FastAPI(title="HighRev prediction demo", lifespan=lifespan)

    @application.get("/health")
    def health():
        return {"status": "ready", "model_uri": application.state.model_uri}

    @application.post("/predict", response_model=PredictionResponse)
    def predict(request: PredictionRequest):
        # The saved model owns preprocessing. The API only validates and orders fields.
        frame = pd.DataFrame(
            [row.model_dump() for row in request.rows], columns=FEATURES
        )
        for column in FEATURES[:2]:
            frame[column] = frame[column].astype(float)
        frame = frame.replace({None: np.nan})
        output = application.state.model.predict(frame)
        probabilities = output["probability_high_revenue"].to_numpy(dtype=float)
        if len(probabilities) != len(frame) or not np.isfinite(probabilities).all():
            raise RuntimeError(
                "Model returned invalid prediction count or nonfinite values"
            )
        if ((probabilities < 0) | (probabilities > 1)).any():
            raise RuntimeError("Model returned probabilities outside [0, 1]")
        return PredictionResponse(
            model_uri=application.state.model_uri,
            probabilities=probabilities.tolist(),
        )

    return application


app = create_app()
