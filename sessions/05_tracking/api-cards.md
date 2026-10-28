# Ex 4: MLflow API cards

Use these cards to identify the MLflow API functions needed for the three TODOs
in `track_run.py`. Read the linked MLflow documentation and decide what
arguments each call needs, which data belongs in it, and what it stores. The
cards intentionally name the APIs without giving you their call syntax or
completed implementations.

## `record_parameters(params, overrides)`

- **Searchable parameter values:** [`mlflow.log_params`](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.html#mlflow.log_params)
- **Full effective configuration artifact:** [`mlflow.log_dict`](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.html#mlflow.log_dict)
- **Runtime override artifact:** [`mlflow.log_dict`](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.html#mlflow.log_dict)
- Supplied helper: `flatten(params)` converts nested parameters into a flat
  mapping suitable for the searchable parameter record.

As you read the docs, determine why the searchable record and full
configuration artifact are both useful, and why runtime overrides should be
recorded separately from effective parameters.

## `record_metrics(metrics, metrics_path)`

- **Numeric measurements:** [`mlflow.log_metrics`](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.html#mlflow.log_metrics)
- **Evaluation report file:** [`mlflow.log_artifact`](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.html#mlflow.log_artifact)

Determine which input belongs in each call and why the metrics file is an
artifact in addition to the individual numeric values.

## `record_model(model)`

- **Scikit-learn model artifact:** [`mlflow.sklearn.log_model`](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.sklearn.html#mlflow.sklearn.log_model)
- Supplied helpers: `model_requirements()` and the prepared `src/highrev`
  source directory.

Read the argument documentation and determine how to preserve the model's
runtime requirements and the custom HighRev transform. The driver needs the
function's returned model information to record the model URI.

## Before you run A

Complete only the three TODO functions. The driver already opens and closes a
run, checks provenance, gathers Kedro's effective configuration, and executes
the existing pipeline. After implementing the functions, remove their
`NotImplementedError` statements. Run A and inspect the run to confirm the
parameters, artifacts, metrics and model appear in the expected places. Explain
why metrics are not available until training completes, and why effective
parameters can differ without a Git change.

Use MLflow's API reference links above as the source of truth. A logged model
artifact is not the same thing as a registered or promoted production model.
