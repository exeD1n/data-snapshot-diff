"""Input validation for predictable snapshot comparison."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ValidationIssue:
    source: str
    kind: str
    message: str
    examples: pd.DataFrame


class DataValidationError(ValueError):
    """Raised when comparison keys are unsafe to use."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__("; ".join(issue.message for issue in issues))


def validate_keys(old: pd.DataFrame, new: pd.DataFrame, keys: list[str]) -> None:
    """Ensure keys exist, contain values, and uniquely identify rows."""
    if not keys:
        raise DataValidationError(
            [
                ValidationIssue(
                    "both", "missing_selection", "Выберите хотя бы один ключ.", pd.DataFrame()
                )
            ]
        )

    issues: list[ValidationIssue] = []
    for source, frame in (("old", old), ("new", new)):
        missing = [key for key in keys if key not in frame.columns]
        if missing:
            issues.append(
                ValidationIssue(
                    source,
                    "missing_columns",
                    f"В {source} отсутствуют ключевые колонки: {', '.join(missing)}.",
                    pd.DataFrame({"missing_column": missing}),
                )
            )
            continue

        blank_mask = frame[keys].isna().any(axis=1)
        for key in keys:
            blank_mask |= frame[key].astype("string").str.strip().eq("").fillna(False)
        if blank_mask.any():
            issues.append(
                ValidationIssue(
                    source,
                    "blank_keys",
                    f"В {source} есть пустые значения ключа ({int(blank_mask.sum())} строк).",
                    frame.loc[blank_mask, keys].head(10).reset_index(drop=True),
                )
            )

        duplicate_mask = frame.duplicated(keys, keep=False)
        if duplicate_mask.any():
            issues.append(
                ValidationIssue(
                    source,
                    "duplicate_keys",
                    f"В {source} ключ не уникален ({int(duplicate_mask.sum())} строк).",
                    frame.loc[duplicate_mask, keys].head(10).reset_index(drop=True),
                )
            )

    if issues:
        raise DataValidationError(issues)
