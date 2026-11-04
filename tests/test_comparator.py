import pandas as pd
import pytest

from data_snapshot_diff import DataValidationError, compare_snapshots


def frame(rows, columns=("id", "value")):
    return pd.DataFrame(rows, columns=columns)


def test_identical_and_order_independent():
    old = frame([("001", "А"), ("002", "Б")])
    new = frame([("002", "Б"), ("001", "А")], columns=("id", "value"))[["value", "id"]]
    result = compare_snapshots(old, new, ["id"])
    assert result.metrics == {
        "old_rows": 2,
        "new_rows": 2,
        "added_records": 0,
        "missing_records": 0,
        "changed_records": 0,
        "unchanged_records": 2,
        "changed_cells": 0,
    }


def test_added_missing_and_multiple_changes():
    old = pd.DataFrame({"id": [1, 2], "name": ["a", "b"], "qty": [1, 2]})
    new = pd.DataFrame({"id": [2, 3], "name": ["B", "c"], "qty": [20, 3]})
    result = compare_snapshots(old, new, ["id"])
    assert result.added.id.tolist() == [3]
    assert result.missing.id.tolist() == [1]
    assert set(result.changed.column) == {"name", "qty"}
    assert result.metrics["changed_records"] == 1


def test_composite_key():
    old = pd.DataFrame({"order": [1, 1], "product": ["A", "B"], "status": ["new", "new"]})
    new = old.copy()
    new.loc[1, "status"] = "done"
    result = compare_snapshots(old, new, ["order", "product"])
    assert result.changed.iloc[0].to_dict() == {
        "order": 1,
        "product": "B",
        "column": "status",
        "old_value": "new",
        "new_value": "done",
    }


@pytest.mark.parametrize(
    "bad",
    [pd.DataFrame({"id": [1, 1]}), pd.DataFrame({"id": [1, None]}), pd.DataFrame({"id": [1, ""]})],
)
def test_invalid_keys(bad):
    with pytest.raises(DataValidationError):
        compare_snapshots(bad, pd.DataFrame({"id": [1]}), ["id"])


def test_missing_key_and_no_selection():
    data = pd.DataFrame({"id": [1]})
    with pytest.raises(DataValidationError):
        compare_snapshots(data, data, ["other"])
    with pytest.raises(DataValidationError):
        compare_snapshots(data, data, [])


def test_schema_changes_and_empty_frames():
    old = pd.DataFrame(columns=["id", "old_only"])
    new = pd.DataFrame(columns=["id", "new_only"])
    result = compare_snapshots(old, new, ["id"])
    assert set(map(tuple, result.schema_changes.to_numpy())) == {
        ("removed", "old_only"),
        ("added", "new_only"),
    }
    assert result.metrics["changed_cells"] == 0


def test_null_fields_equal_and_type_differences_explicit():
    old = pd.DataFrame({"id": ["001", "002"], "value": [None, 123]})
    new = pd.DataFrame({"id": ["001", "002"], "value": [None, "123"]})
    result = compare_snapshots(old, new, ["id"])
    assert result.changed_records.id.tolist() == ["002"]
    assert result.unchanged.id.tolist() == ["001"]
