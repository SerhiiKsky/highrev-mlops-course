"""Kedro nodes connecting prepared customers to the isolated workers."""

from .execution import run_comparison
from .protocol import make_bundle


def create_pipeline():
    from kedro.pipeline import Pipeline, node

    return Pipeline(
        [
            node(
                make_bundle,
                ["customers_labeled", "params:lab06_protocol"],
                "lab06_bundle",
                name="lab06_make_bundle",
            ),
            node(
                run_comparison,
                ["lab06_bundle", "params:lab06_execution"],
                "lab06_comparison",
                name="lab06_train_comparison",
            ),
        ]
    )


def create_integrated_pipeline():
    from highrev.pipelines.data_processing.pipeline import (
        create_pipeline as preparation_pipeline,
    )

    return preparation_pipeline() + create_pipeline()
