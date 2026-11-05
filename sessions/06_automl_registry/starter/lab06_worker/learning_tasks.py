"""Implement these two functions during Lab 06."""


def comparison_options(models, budget_seconds):
    """Return options: supplied model IDs, AUC sort, budget in minutes,
    one selected model, and raised errors. Reject empty models or nonpositive budget.
    """
    raise NotImplementedError("Implement the bounded AutoML comparison")


def log_validation_metrics(metrics):
    """Log the supplied numeric validation metrics to the active MLflow run."""
    raise NotImplementedError("Log the validation metrics")
