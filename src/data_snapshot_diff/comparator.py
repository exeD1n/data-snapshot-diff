"""Order-independent, key-based snapshot comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .validation import validate_keys


@dataclass(frozen=True)
class ComparisonResult:
    old_rows: int
    new_rows: int
    added: pd.DataFrame
    missing: pd.DataFrame
    changed: pd.DataFrame
    changed_records: pd.DataFrame
    unchanged: pd.DataFrame
    schema_changes: pd.DataFrame
    keys: list[str]

    @property
    def metrics(self) -> dict[str, int]:
        return {
            "old_rows": self.old_rows,
            "new_rows": self.new_rows,
            "added_records": len(self.added),
            "missing_records": len(self.missing),
            "changed_records": len(self.changed_records),
            "unchanged_records": len(self.unchanged),
            "changed_cells": len(self.changed),
        }


def _equal_values(left: Any, right: Any) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True
    if pd.isna(left) or pd.isna(right):
        return False
    return type(left) is type(right) and left == right


def _key_values(index_value: Any, keys: list[str]) -> tuple[Any, ...]:
    return index_value if len(keys) > 1 else (index_value,)


def compare_snapshots(old: pd.DataFrame, new: pd.DataFrame, keys: list[str]) -> ComparisonResult:
    """Compare two frames without coercing identifiers or business values."""
    validate_keys(old, new, keys)
    old = old.copy()
    new = new.copy()
    old_columns, new_columns = list(old.columns), list(new.columns)
    common_columns = [column for column in old_columns if column in new_columns]
    compared_columns = [column for column in common_columns if column not in keys]

    old_indexed = old.set_index(keys, drop=False)
    new_indexed = new.set_index(keys, drop=False)
    old_keys, new_keys = set(old_indexed.index), set(new_indexed.index)
    added_keys = new_keys - old_keys
    missing_keys = old_keys - new_keys
    shared_keys = old_keys & new_keys

    added = (
        new_indexed.loc[list(added_keys)].reset_index(drop=True) if added_keys else new.iloc[0:0]
    )
    missing = (
        old_indexed.loc[list(missing_keys)].reset_index(drop=True)
        if missing_keys
        else old.iloc[0:0]
    )

    change_rows: list[dict[str, Any]] = []
    changed_key_set: set[Any] = set()
    for index_value in shared_keys:
        old_row, new_row = old_indexed.loc[index_value], new_indexed.loc[index_value]
        for column in compared_columns:
            old_value, new_value = old_row[column], new_row[column]
            if not _equal_values(old_value, new_value):
                changed_key_set.add(index_value)
                record = dict(zip(keys, _key_values(index_value, keys), strict=True))
                record.update({"column": column, "old_value": old_value, "new_value": new_value})
                change_rows.append(record)

    changed_columns = [*keys, "column", "old_value", "new_value"]
    changed = pd.DataFrame(change_rows, columns=changed_columns)
    changed_records = (
        new_indexed.loc[list(changed_key_set)].reset_index(drop=True)
        if changed_key_set
        else new.iloc[0:0]
    )
    unchanged_keys = shared_keys - changed_key_set
    unchanged = (
        new_indexed.loc[list(unchanged_keys)].reset_index(drop=True)
        if unchanged_keys
        else new.iloc[0:0]
    )

    schema_rows = [
        *(
            {"change": "removed", "column": column}
            for column in old_columns
            if column not in new_columns
        ),
        *(
            {"change": "added", "column": column}
            for column in new_columns
            if column not in old_columns
        ),
    ]
    schema_changes = pd.DataFrame(schema_rows, columns=["change", "column"])

    sort_keys = keys
    for frame in (added, missing, changed_records, unchanged):
        if not frame.empty:
            frame.sort_values(sort_keys, key=lambda values: values.astype(str), inplace=True)
            frame.reset_index(drop=True, inplace=True)
    if not changed.empty:
        changed.sort_values([*keys, "column"], key=lambda values: values.astype(str), inplace=True)
        changed.reset_index(drop=True, inplace=True)

    return ComparisonResult(
        len(old),
        len(new),
        added,
        missing,
        changed,
        changed_records,
        unchanged,
        schema_changes,
        keys,
    )
