"""Transparent, opt-in business rules for product snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .comparator import ComparisonResult


@dataclass(frozen=True)
class Insight:
    category: str
    key: str
    message: str


def _display_key(row: pd.Series, keys: list[str]) -> str:
    return " / ".join(str(row[key]) for key in keys)


def _number(value: Any) -> float | None:
    if pd.isna(value) or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_insights(
    result: ComparisonResult, *, price_column: str | None = None, stock_column: str | None = None
) -> list[Insight]:
    insights: list[Insight] = []
    for _, row in result.added.iterrows():
        key = _display_key(row, result.keys)
        insights.append(Insight("new_record", key, f"{key}: новая запись в выгрузке."))
    for _, row in result.missing.iterrows():
        key = _display_key(row, result.keys)
        insights.append(
            Insight(
                "missing_record",
                key,
                f"{key}: отсутствует в новом снимке. "
                "Проверьте полноту данных или изменение состава.",
            )
        )

    for _, row in result.changed.iterrows():
        key = " / ".join(str(row[item]) for item in result.keys)
        old_number, new_number = _number(row.old_value), _number(row.new_value)
        if row["column"] == price_column and old_number is not None and new_number is not None:
            direction = "выросла" if new_number > old_number else "снизилась"
            if new_number == old_number:
                continue
            delta = new_number - old_number
            percent = None if old_number == 0 else delta / abs(old_number) * 100
            detail = f" на {abs(delta):g}"
            if percent is not None:
                detail += f" ({abs(percent):.1f}%)"
            insights.append(Insight("price_change", key, f"{key}: цена {direction}{detail}."))
        elif row["column"] == stock_column and old_number is not None and new_number is not None:
            if new_number == 0 and old_number != 0:
                insights.append(
                    Insight(
                        "out_of_stock",
                        key,
                        f"{key}: остаток изменился с {old_number:g} до 0. "
                        "Проверьте доступность для продажи.",
                    )
                )
    return insights
