from io import BytesIO

import pandas as pd
from openpyxl import load_workbook

from data_snapshot_diff import compare_snapshots
from data_snapshot_diff.exporter import export_excel, safe_excel_value


def test_excel_report_content_and_format():
    old = pd.DataFrame({"id": ["A", "B"], "value": ["=CMD()", "old"]})
    new = pd.DataFrame({"id": ["A", "C"], "value": ["safe", "+danger"]})
    report = export_excel(compare_snapshots(old, new, ["id"]))
    workbook = load_workbook(BytesIO(report), data_only=False)
    assert workbook.sheetnames == ["Summary", "Added", "Missing", "Changed", "Schema_Changes"]
    assert workbook["Added"]["B2"].value == "'+danger"
    assert workbook["Changed"]["C2"].value == "'=CMD()"
    assert workbook["Summary"].freeze_panes == "A2"


def test_formula_safety_prefixes_and_non_strings():
    assert [safe_excel_value(value) for value in ["=x", "+x", "-x", "@x", "x", 1]] == [
        "'=x",
        "'+x",
        "'-x",
        "'@x",
        "x",
        1,
    ]
