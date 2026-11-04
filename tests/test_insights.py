import pandas as pd

from data_snapshot_diff import compare_snapshots
from data_snapshot_diff.insights import build_insights


def test_product_insights_control_case():
    old = pd.DataFrame(
        {"sku": ["P100", "P101", "P103"], "price": [1000, 1500, 2300], "stock": [10, 4, 8]}
    )
    new = pd.DataFrame(
        {"sku": ["P100", "P101", "P106"], "price": [1150, 1500, 1800], "stock": [10, 0, 12]}
    )
    insights = build_insights(
        compare_snapshots(old, new, ["sku"]), price_column="price", stock_column="stock"
    )
    messages = " ".join(item.message for item in insights)
    assert "15.0%" in messages and "остаток изменился с 4 до 0" in messages
    assert "P103" in messages and "P106" in messages


def test_price_decrease_zero_base_and_no_false_rules():
    old = pd.DataFrame({"id": [1, 2], "price": [10, 0], "note": ["x", "x"]})
    new = pd.DataFrame({"id": [1, 2], "price": [5, 2], "note": ["y", "x"]})
    insights = build_insights(compare_snapshots(old, new, ["id"]), price_column="price")
    assert any("снизилась" in item.message for item in insights)
    assert any("выросла на 2" in item.message for item in insights)
    assert all("note" not in item.message for item in insights)


def test_missing_business_columns_is_safe():
    data = pd.DataFrame({"id": [1], "value": [None]})
    assert build_insights(compare_snapshots(data, data, ["id"])) == []
