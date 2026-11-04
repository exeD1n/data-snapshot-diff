"""Local, private history of generated comparison reports."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import pandas as pd

DEFAULT_HISTORY_DIR = Path(".data_snapshot_diff") / "history"
REPORT_SHEETS = ("Summary", "Added", "Missing", "Changed", "Schema_Changes")


@dataclass(frozen=True)
class HistoryEntry:
    id: str
    name: str
    created_at: str
    filename: str
    old_rows: int
    new_rows: int
    added_records: int
    missing_records: int
    changed_records: int
    unchanged_records: int
    changed_cells: int


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^\w\-. ]+", "_", value, flags=re.UNICODE).strip(" ._")
    return cleaned[:80] or "Сравнение"


def save_report(
    report: bytes,
    *,
    name: str,
    metrics: dict[str, int],
    history_dir: Path = DEFAULT_HISTORY_DIR,
    now: datetime | None = None,
) -> HistoryEntry:
    """Save an Excel report and compact metadata using an atomic rename."""
    history_dir.mkdir(parents=True, exist_ok=True)
    created_at = (now or datetime.now(UTC)).isoformat()
    entry_id = uuid.uuid4().hex
    filename = f"{created_at[:10]}_{entry_id[:8]}_{_safe_name(name)}.xlsx"
    entry = HistoryEntry(
        id=entry_id,
        name=_safe_name(name),
        created_at=created_at,
        filename=filename,
        **metrics,
    )
    report_path = history_dir / filename
    temporary_path = report_path.with_suffix(".tmp")
    temporary_path.write_bytes(report)
    temporary_path.replace(report_path)
    (history_dir / f"{entry_id}.json").write_text(
        json.dumps(asdict(entry), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return entry


def list_history(history_dir: Path = DEFAULT_HISTORY_DIR) -> list[HistoryEntry]:
    """Return valid history entries newest first; ignore incomplete metadata."""
    if not history_dir.exists():
        return []
    entries: list[HistoryEntry] = []
    for metadata_path in history_dir.glob("*.json"):
        try:
            entry = HistoryEntry(**json.loads(metadata_path.read_text(encoding="utf-8")))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if (history_dir / entry.filename).is_file():
            entries.append(entry)
    return sorted(entries, key=lambda item: item.created_at, reverse=True)


def load_report(entry: HistoryEntry, history_dir: Path = DEFAULT_HISTORY_DIR) -> bytes:
    """Load report bytes while preventing metadata-based path traversal."""
    report_path = (history_dir / entry.filename).resolve()
    root = history_dir.resolve()
    if root not in report_path.parents or report_path.suffix.lower() != ".xlsx":
        raise ValueError("Некорректный путь локального отчёта.")
    return report_path.read_bytes()


def read_report_sheet(report: bytes, sheet_name: str) -> pd.DataFrame:
    """Open one supported sheet from a previously generated report."""
    if sheet_name not in REPORT_SHEETS:
        raise ValueError("Неизвестный лист отчёта.")
    return pd.read_excel(BytesIO(report), sheet_name=sheet_name, engine="openpyxl")
