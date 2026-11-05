"""MLflow wrapper for complete fitted classification pipelines."""

import joblib
import numpy as np
import pandas as pd
from mlflow.pyfunc import PythonModel


class ProbabilityBundle(PythonModel):
    def load_context(self, context):
        self.pipeline = joblib.load(context.artifacts["pipeline"])

    def predict(self, context, model_input, params=None):
        classes = list(self.pipeline.classes_)
        if 1 not in classes:
            raise ValueError("Model has no positive class 1")
        values = self.pipeline.predict_proba(model_input)[:, classes.index(1)]
        if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
            raise ValueError("Invalid probabilities")
        return pd.DataFrame(
            {"probability_high_revenue": values}, index=model_input.index
        )
