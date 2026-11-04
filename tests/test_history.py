from datetime import UTC, datetime
from io import BytesIO

import pandas as pd
import pytest

from data_snapshot_diff import compare_snapshots
from data_snapshot_diff.exporter import export_excel
from data_snapshot_diff.history import (
    HistoryEntry,
    list_history,
    load_report,
    read_report_sheet,
    save_report,
)


def sample_report():
    old = pd.DataFrame({"id": ["A", "B"], "value": [1, 2]})
    new = pd.DataFrame({"id": ["A", "C"], "value": [3, 4]})
    result = compare_snapshots(old, new, ["id"])
    return result, export_excel(result)


def test_save_list_reopen_and_download(tmp_path):
    result, report = sample_report()
    entry = save_report(
        report,
        name="Ежедневная / сверка",
        metrics=result.metrics,
        history_dir=tmp_path,
        now=datetime(2026, 11, 4, 8, 0, tzinfo=UTC),
    )

    assert entry.name == "Ежедневная _ сверка"
    assert list_history(tmp_path) == [entry]
    reopened = load_report(entry, tmp_path)
    assert reopened == report
    assert pd.ExcelFile(BytesIO(reopened)).sheet_names == [
        "Summary",
        "Added",
        "Missing",
        "Changed",
        "Schema_Changes",
    ]
    assert read_report_sheet(reopened, "Changed").iloc[0]["column"] == "value"


def test_history_ignores_broken_metadata_and_missing_report(tmp_path):
    (tmp_path / "broken.json").write_text("not json", encoding="utf-8")
    missing = HistoryEntry("x", "Missing", "2026-01-01", "missing.xlsx", 0, 0, 0, 0, 0, 0, 0)
    (tmp_path / "missing.json").write_text(
        __import__("json").dumps(missing.__dict__), encoding="utf-8"
    )
    assert list_history(tmp_path) == []


def test_rejects_unknown_sheet_and_unsafe_path(tmp_path):
    _, report = sample_report()
    with pytest.raises(ValueError):
        read_report_sheet(report, "Secrets")
    unsafe = HistoryEntry("x", "Unsafe", "2026-01-01", "../outside.xlsx", 0, 0, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        load_report(unsafe, tmp_path)
