"""Styled and formula-safe Excel report generation."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .comparator import ComparisonResult

DANGEROUS_PREFIXES = ("=", "+", "-", "@")
SHEET_COLORS = {
    "Summary": "1F4E78",
    "Added": "70AD47",
    "Missing": "C65911",
    "Changed": "FFC000",
    "Schema_Changes": "8064A2",
}


def safe_excel_value(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(DANGEROUS_PREFIXES):
        return "'" + value
    return value


def _safe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.map(safe_excel_value)


def export_excel(result: ComparisonResult) -> bytes:
    summary = pd.DataFrame(
        [(key, value) for key, value in result.metrics.items()], columns=["Metric", "Value"]
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        _safe_frame(result.added).to_excel(writer, sheet_name="Added", index=False)
        _safe_frame(result.missing).to_excel(writer, sheet_name="Missing", index=False)
        _safe_frame(result.changed).to_excel(writer, sheet_name="Changed", index=False)
        _safe_frame(result.schema_changes).to_excel(
            writer, sheet_name="Schema_Changes", index=False
        )

    output.seek(0)
    workbook = load_workbook(output)
    for worksheet in workbook.worksheets:
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        color = SHEET_COLORS[worksheet.title]
        for cell in worksheet[1]:
            cell.fill = PatternFill("solid", fgColor=color)
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        for index, column_cells in enumerate(worksheet.columns, start=1):
            width = min(50, max(10, max(len(str(cell.value or "")) for cell in column_cells) + 2))
            worksheet.column_dimensions[get_column_letter(index)].width = width

    final = BytesIO()
    workbook.save(final)
    return final.getvalue()
