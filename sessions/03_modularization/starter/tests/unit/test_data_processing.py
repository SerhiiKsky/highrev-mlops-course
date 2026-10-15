"""Ex 3 and Ex 5: replace each placeholder with your own arrange/act/assert test.

Load tiny CSVs from tests/fixtures using a path based on this file, not the cwd.
Keep customer IDs as strings. Calculate expectations independently on paper.
"""


def test_order_aggregation_contract():
    """Check the aggregate index, schema, and values for a repeated customer."""
    raise NotImplementedError("Ex 3: write the aggregation test")


def test_customer_age_keeps_fractional_years():
    """Choose a non-whole-year interval; independently calculate its expected age."""
    raise NotImplementedError("Ex 3: write a fractional-age test")


def test_label_threshold_boundary():
    """Cover below, equal to, and above the default threshold."""
    raise NotImplementedError("Ex 3: write a boundary test")


def test_transformations_leave_inputs_unchanged():
    """Compare each input with a deep copy after its transformation returns."""
    raise NotImplementedError("Ex 3: write input immutability tests")


def test_negative_quantity_policy():
    """Test your documented policy and show valid order behavior is preserved."""
    raise NotImplementedError("Ex 5: decide, implement, and test the policy")
