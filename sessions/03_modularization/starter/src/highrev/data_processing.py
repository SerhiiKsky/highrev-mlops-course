"""Exercise 2: extract transformations from your baseline.py.

All public functions return a new DataFrame and leave their inputs unchanged.
Keep file access and model training outside this module.
"""

import pandas as pd


def prepare_orders(orders: pd.DataFrame) -> pd.DataFrame:
    """Return customer aggregates indexed by customer_id.

    Accept baseline year/month/day date strings, including unpadded month/day.
    Preserve the baseline category normalization, parse order_date, and derive
    total from tshirt_quantity and tshirt_price. Aggregate order_date (min),
    total (sum), pages_visited (mean), and order_id (count).
    Exercise 5 adds your documented negative-quantity policy.
    """
    raise NotImplementedError("Ex 2: extract order preparation")


def prepare_customers(
    customers: pd.DataFrame, orders_by_customer: pd.DataFrame, max_age: int = 100
) -> pd.DataFrame:
    """Join customerID to the aggregate index using an inner join.

    Birthdate strings follow the baseline year/month/day slash convention.
    Preserve the baseline's three birthdate repairs and fractional age in days
    divided by 365. Keep rows with age_first_order strictly below max_age.
    Parse browser and os from user_agent. Drop birthdate, order_date, order_id,
    ip_address, and user_agent. Keep total for the separate labeling step.
    """
    raise NotImplementedError("Ex 2: extract customer preparation")


def label_customers(customers_prepared: pd.DataFrame, threshold: int = 300) -> pd.DataFrame:
    """Add boolean high_revenue using strictly greater than threshold; drop total."""
    raise NotImplementedError("Ex 2: extract target creation")
