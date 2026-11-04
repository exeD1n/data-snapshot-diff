"""Safe CSV/XLSX loading with explicit limits and conservative inference."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

MAX_FILE_SIZE = 25 * 1024 * 1024
SUPPORTED_ENCODINGS = ("utf-8-sig", "utf-8", "cp1251")
SUPPORTED_DELIMITERS = (",", ";", "\t")


class DataLoadError(ValueError):
    """Raised for an unsupported or unreadable user file."""


@dataclass(frozen=True)
class CsvOptions:
    encoding: str | None = None
    delimiter: str | None = None


def _bytes(source: bytes | BinaryIO) -> bytes:
    if isinstance(source, bytes):
        data = source
    else:
        source.seek(0)
        data = source.read()
    if len(data) > MAX_FILE_SIZE:
        raise DataLoadError("Файл превышает лимит 25 МБ.")
    return data


def detect_csv(data: bytes) -> CsvOptions:
    text = None
    encoding = None
    for candidate in SUPPORTED_ENCODINGS:
        try:
            text = data.decode(candidate)
            encoding = candidate
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise DataLoadError("Не удалось определить кодировку CSV.")
    try:
        delimiter = (
            csv.Sniffer().sniff(text[:8192], delimiters="".join(SUPPORTED_DELIMITERS)).delimiter
        )
    except csv.Error as exc:
        raise DataLoadError("Не удалось определить разделитель CSV. Укажите его вручную.") from exc
    return CsvOptions(encoding, delimiter)


def load_csv(source: bytes | BinaryIO, options: CsvOptions | None = None) -> pd.DataFrame:
    data = _bytes(source)
    detected = detect_csv(data)
    options = options or detected
    encoding = options.encoding or detected.encoding
    delimiter = options.delimiter or detected.delimiter
    if delimiter not in SUPPORTED_DELIMITERS or encoding not in SUPPORTED_ENCODINGS:
        raise DataLoadError("Неподдерживаемая кодировка или разделитель.")
    try:
        return pd.read_csv(BytesIO(data), encoding=encoding, sep=delimiter, dtype=object)
    except Exception as exc:
        raise DataLoadError(f"Не удалось прочитать CSV: {exc}") from exc


def list_excel_sheets(source: bytes | BinaryIO) -> list[str]:
    data = _bytes(source)
    try:
        return pd.ExcelFile(BytesIO(data), engine="openpyxl").sheet_names
    except Exception as exc:
        raise DataLoadError("Не удалось открыть XLSX. Проверьте целостность файла.") from exc


def load_excel(source: bytes | BinaryIO, sheet_name: str | int = 0) -> pd.DataFrame:
    data = _bytes(source)
    try:
        return pd.read_excel(BytesIO(data), sheet_name=sheet_name, dtype=object, engine="openpyxl")
    except Exception as exc:
        raise DataLoadError(f"Не удалось прочитать лист XLSX: {exc}") from exc


def load_file(
    source: bytes | BinaryIO,
    filename: str,
    *,
    sheet_name: str | int = 0,
    csv_options: CsvOptions | None = None,
) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return load_csv(source, csv_options)
    if suffix == ".xlsx":
        return load_excel(source, sheet_name)
    raise DataLoadError("Поддерживаются только файлы CSV и XLSX.")
