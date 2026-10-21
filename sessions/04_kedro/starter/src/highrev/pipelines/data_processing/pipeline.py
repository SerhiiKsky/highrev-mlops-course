"""Ex 3: wrap existing transformations; Ex 4: add validation and reporting."""


def create_pipeline():
    """Connect preparation and labeling with named datasets and parameters.

    Reuse highrev.data_processing functions. Node names must be prepare_orders,
    prepare_customers, and label_customers. Paths belong in the catalog.
    In Ex 4, both preparation nodes must consume validated inputs so a failing
    schema check actually prevents downstream work; list order is insufficient.
    """
    raise NotImplementedError("Ex 3: build the data_processing graph")
