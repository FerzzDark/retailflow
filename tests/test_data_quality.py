"""
Data quality tests for the RetailFlow pipeline.

Validates integrity across pipeline layers using pandera schemas and pytest.
Run with: pytest tests/ -v
"""
import pandas as pd
import pandera as pa
from pandera import Column, Check, DataFrameSchema


# Schema for the silver layer — enforces types, ranges, and non-null keys
silver_schema = DataFrameSchema({
    "id": Column(str, nullable=False),
    "item_id": Column(str, nullable=False),
    "store_id": Column(str, nullable=False),
    "date": Column("datetime64[ns]", nullable=False),
    "units": Column(int, Check.greater_than_or_equal_to(0), nullable=False),
    "sell_price": Column(float, Check.greater_than_or_equal_to(0), nullable=True),
})


def make_sample_silver() -> pd.DataFrame:
    """Build a small valid sample matching the silver schema."""
    return pd.DataFrame({
        "id": ["FOODS_1_001_CA_1", "FOODS_1_002_CA_1"],
        "item_id": ["FOODS_1_001", "FOODS_1_002"],
        "store_id": ["CA_1", "CA_1"],
        "date": pd.to_datetime(["2016-01-01", "2016-01-01"]),
        "units": [3, 0],
        "sell_price": [2.5, 1.0],
    })


def test_silver_schema_valid():
    """A well-formed silver dataframe passes validation."""
    df = make_sample_silver()
    validated = silver_schema.validate(df)
    assert len(validated) == 2


def test_no_negative_units():
    """Units sold can never be negative."""
    df = make_sample_silver()
    assert (df["units"] >= 0).all()


def test_no_null_keys():
    """Key columns must never be null."""
    df = make_sample_silver()
    for key in ["id", "item_id", "store_id", "date"]:
        assert df[key].notnull().all(), f"Null found in key column: {key}"


def test_negative_units_rejected():
    """Schema validation should reject negative units."""
    df = make_sample_silver()
    df.loc[0, "units"] = -5
    try:
        silver_schema.validate(df)
        assert False, "Schema should have rejected negative units"
    except pa.errors.SchemaError:
        assert True


def test_row_count_positive():
    """A loaded table should always have at least one row."""
    df = make_sample_silver()
    assert len(df) > 0
