"""Fresh-process MLflow reload; deliberately independent of local source paths."""

import json
import sys
from pathlib import Path

import mlflow
import pandas as pd

mlflow.set_tracking_uri(sys.argv[1])
model = mlflow.pyfunc.load_model(sys.argv[2])
frame = pd.read_csv(sys.argv[3])
result = model.predict(frame)["probability_high_revenue"].tolist()
Path(sys.argv[4]).write_text(json.dumps(result, allow_nan=False), encoding="utf-8")
