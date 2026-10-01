from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, FiniteFloat

bundle = joblib.load(Path(__file__).parent / "artifacts" / "model.joblib")
app = FastAPI()

class PredictionRequest(BaseModel):
    features: dict[str, FiniteFloat]

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": True}

@app.post("/predict")
def predict(request: PredictionRequest):
    names = bundle["feature_names"]
    if set(request.features) != set(names):
        raise HTTPException(status_code=422, detail={"required_features": names})
    row = pd.DataFrame([request.features], columns=names)
    prediction = float(bundle["model"].predict(row)[0])
    return {"prediction": prediction, "target": bundle["target"]}
