"""Ex 4: validate raw inputs and return the two frames without changing their values."""

CUSTOMER_COLUMNS = {
    "customerID",
    "birthdate",
    "gender",
    "campaign",
    "ip_address_country",
    "ip_address",
    "user_agent",
}
ORDER_COLUMNS = {
    "customer_id",
    "order_id",
    "order_date",
    "tshirt_category",
    "tshirt_quantity",
    "tshirt_price",
    "pages_visited",
}


def validate_inputs(customers, orders):
    """Return (validated_customers, validated_orders), in this order.

    Reject missing required columns, empty tables, null/blank customer identifiers,
    and nonnumeric/nonfinite quantity or price. Raise ValueError with table/field.
    Preserve values, row order, duplicates, and input frames. Do not reject repeated
    customer IDs: the course data already contains them. Keep your Session 3
    negative-quantity policy in prepare_orders. This is a limited schema check.
    """
    raise NotImplementedError("Ex 4: implement the raw-data gate")
