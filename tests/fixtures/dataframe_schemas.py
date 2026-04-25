import pandera.pandas as pa

orders_schema = pa.DataFrameSchema(
    name="orders",
    description="E-commerce order records",
    columns={
        "order_id": pa.Column(int, checks=pa.Check.greater_than(0), description="Unique order identifier"),
        "customer_id": pa.Column(int, nullable=False, description="FK to customers table"),
        "amount": pa.Column(
            float,
            checks=[pa.Check.greater_than_or_equal_to(0.0), pa.Check.less_than(1_000_000)],
            description="Order total in USD",
        ),
        "status": pa.Column(
            str,
            checks=pa.Check.isin(["pending", "shipped", "delivered", "cancelled"]),
            description="Current order status",
        ),
        "created_at": pa.Column("datetime64[ns]", nullable=False),
    },
    coerce=True,
)

products_schema = pa.DataFrameSchema(
    name="products",
    columns={
        "sku": pa.Column(str, checks=pa.Check.str_matches(r"^[A-Z]{2}-\d{4}$")),
        "name": pa.Column(str, nullable=False),
        "price": pa.Column(float, checks=pa.Check.greater_than(0)),
        "in_stock": pa.Column(bool, nullable=False),
    },
)
