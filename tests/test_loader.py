from io import BytesIO

import pandas as pd
import pytest

from data_snapshot_diff.loader import CsvOptions, DataLoadError, list_excel_sheets, load_file


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "cp1251"])
@pytest.mark.parametrize("delimiter", [",", ";", "\t"])
def test_csv_variants(encoding, delimiter):
    content = f"id{delimiter}название\n001{delimiter}Товар".encode(encoding)
    result = load_file(content, "test.csv")
    assert result.iloc[0].to_dict() == {"id": "001", "название": "Товар"}


def test_manual_csv_options():
    result = load_file(b"id;value\n1;x", "x.csv", csv_options=CsvOptions("utf-8", ";"))
    assert result.shape == (1, 2)


def test_excel_and_sheet_selection():
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame({"a": [1]}).to_excel(writer, sheet_name="First", index=False)
        pd.DataFrame({"b": [2]}).to_excel(writer, sheet_name="Second", index=False)
    data = buffer.getvalue()
    assert list_excel_sheets(data) == ["First", "Second"]
    assert load_file(data, "x.xlsx", sheet_name="Second").columns.tolist() == ["b"]


@pytest.mark.parametrize("name,data", [("x.txt", b"x"), ("x.xlsx", b"broken")])
def test_bad_file(name, data):
    with pytest.raises(DataLoadError):
        load_file(data, name)


def test_ambiguous_csv():
    with pytest.raises(DataLoadError):
        load_file(b"single-column\nvalue", "x.csv")
