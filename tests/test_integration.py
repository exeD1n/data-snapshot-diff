import pandas as pd

from data_snapshot_diff import compare_snapshots


def test_required_p100_p106_scenario():
    old = pd.DataFrame(
        {
            "sku": ["P100", "P101", "P102", "P103", "P104", "P105"],
            "price": [1000, 1500, 600, 2300, 450, 890],
            "stock": [10, 4, 0, 8, 20, 7],
        }
    )
    new = pd.DataFrame(
        {
            "sku": ["P100", "P101", "P102", "P104", "P105", "P106"],
            "price": [1150, 1500, 600, 450, 890, 1800],
            "stock": [10, 0, 0, 20, 7, 12],
        }
    )
    result = compare_snapshots(old, new, ["sku"])
    assert result.metrics == {
        "old_rows": 6,
        "new_rows": 6,
        "added_records": 1,
        "missing_records": 1,
        "changed_records": 2,
        "unchanged_records": 3,
        "changed_cells": 2,
    }
    assert result.added.sku.tolist() == ["P106"]
    assert result.missing.sku.tolist() == ["P103"]
    assert set(result.changed.sku) == {"P100", "P101"}
    assert set(
        zip(result.changed.column, result.changed.old_value, result.changed.new_value, strict=True)
    ) == {("price", 1000, 1150), ("stock", 4, 0)}
