"""Optional extension after Ex 8: compare orchestration with direct function calls.

Keep this file outside pytest discovery until you are ready to implement it.
Retain the existing Session 3 tests and workflow.
"""


def test_kedro_matches_direct_functions(tmp_path):
    """Run the full CLI in an isolated project copy with copied raw inputs.

    Compare its saved labeled frame, predictions, and metrics to direct calls of
    your Session 3 functions on identical inputs and parameters. Do not compare
    only rounded scores. Never overwrite the working project's model or reports.
    """
    raise NotImplementedError("Extension: verify orchestration preserves behavior")


def test_modeling_requires_persisted_input(tmp_path):
    """In fresh CLI processes, observe missing-input failure, then prepare and succeed.

    Use a temporary project, check nonzero/zero exit codes, and ensure the failure
    names customers_labeled, rather than an unrelated import/setup error.
    """
    raise NotImplementedError("Extension: verify the persisted pipeline boundary")
