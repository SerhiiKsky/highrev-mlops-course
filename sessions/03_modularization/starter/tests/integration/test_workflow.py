"""Ex 6: implement the requirements in integration-requirements.md.

Use temporary paths for artifacts; do not overwrite the project's model.pickle.
"""


def test_imports_have_no_execution_side_effects():
    """Import the package and its modules in a fresh process in an empty temp directory."""
    raise NotImplementedError("Ex 6: prove imports do not read, train, print, or save")


def test_workflow_from_project_inputs(tmp_path):
    """Run the command against copied project CSVs in a temporary project-shaped directory."""
    raise NotImplementedError("Ex 6: check the complete execution contract")
