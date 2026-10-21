"""Ex 3: split, fit, and evaluate using your existing modeling functions."""


def create_pipeline():
    """Name nodes split_data, train_model, and evaluate_model.

    split_data returns two frames: map them to train_set and test_set in that order.
    Use input dictionaries when function arguments and dataset names differ.
    Pass params:model_options to train_model through its new optional argument.
    """
    raise NotImplementedError("Ex 3: build the modeling graph")


def create_split_pipeline():
    """Ex 6: extract just the split node so both variants consume the same frames."""
    raise NotImplementedError("Ex 6: extract the shared split")


def create_training_pipeline():
    """Ex 6: return a reusable training/evaluation template without a split node."""
    raise NotImplementedError("Ex 6: extract the reusable two-node template")
