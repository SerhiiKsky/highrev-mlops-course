"""STUDENT TODO K1: wire the supplied functions into a Kedro graph."""

from kedro.pipeline import Pipeline, node

from .nodes import prepare_features, search_candidates, split_data


def create_pipeline(**kwargs) -> Pipeline:
    """Build three nodes using the contracts in INTEGRATION_TEMPLATE.md.

    Raw catalog inputs -> pizza_features -> pizza_split -> results + models.
    Pass configuration with params: inputs; do not call the functions here.
    Give every node a descriptive unique name.
    """
    # TODO K1: replace this exception with your Pipeline([...]).
    raise NotImplementedError("K1: connect the three Pizza Panic nodes")
