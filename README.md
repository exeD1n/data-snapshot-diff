# Data Snapshot Diff

[English](README.md) | [Русский](README.ru.md)

Compare business data snapshots, detect added, missing and changed records, reopen local comparison history, and export actionable Excel reports — without writing SQL or Python.

![Tests](https://github.com/exeD1n/data-snapshot-diff/actions/workflows/tests.yml/badge.svg)

## What problem does it solve?

An analyst receives yesterday's and today's product exports. Instead of maintaining fragile XLOOKUP formulas across thousands of rows, they load both snapshots, choose a stable key, and get a reviewable change list plus an Excel report. The app identifies differences; it does not invent their causes.

## Who is it for?

Data and business analysts, e-commerce managers, data engineers, catalogue owners, and anyone who regularly reconciles CSV or Excel exports.

## How it works

1. Upload two CSV/XLSX files or enable the built-in demo.
2. Choose one or more key columns.
3. Optionally map price and stock columns.
4. Review added, missing, changed, unchanged records and schema changes.
5. Download a formatted Excel report or save it to private local history.

## Business use cases

- **Product catalogue:** identify price, stock, and assortment changes; flag newly out-of-stock items.
- **Order reconciliation:** find new orders and changed statuses using an order key or composite order/product key.
- **Post-ETL validation:** detect unexpected record and schema differences after a pipeline refresh.

“Missing” means absent from the new snapshot. It does **not** prove deletion from the source system.

## Features

- CSV (UTF-8, UTF-8 BOM, Windows-1251; comma, semicolon, tab) and multi-sheet XLSX input
- Single and composite keys with null/duplicate validation and issue examples
- Order-independent row and column comparison; explicit schema changes
- Opt-in, deterministic price/stock insights
- Searchable details and formula-injection-safe styled Excel export
- Local comparison history with KPI preview, report-sheet viewer, and repeat download
- 25 MB per-file limit; in-memory processing without external APIs

## Quick start

```bash
git clone https://github.com/exeD1n/data-snapshot-diff.git
cd data-snapshot-diff
python -m venv .venv
```

Windows PowerShell: `.venv\Scripts\Activate.ps1`  
Linux/macOS: `source .venv/bin/activate`

```bash
python -m pip install -e .
streamlit run app.py
```

## Demo data

`examples/products_before.csv` and `products_after.csv` implement the documented P100–P106 control case: 1 added, 1 missing, 2 changed, 3 unchanged records, and 2 changed cells. The two order workbooks contain a larger synthetic order-status example. All data is fictional.

## Local history

After a comparison, enter a report name and select **Save to history**. The app stores the generated workbook and compact metadata in `.data_snapshot_diff/history` on the machine running Streamlit. Open **History** in the sidebar to review KPI totals, inspect any report sheet, or download the workbook again. This directory is excluded from Git and is never uploaded by the application.

## Testing

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
```

CI runs the linter and tests with an 85% coverage gate on Python 3.11 and 3.12.

## Limitations

- Maximum file size is 25 MB; the app works in memory and is not intended for warehouse-scale data.
- Keys must exist, be non-empty, and uniquely identify every row in both snapshots.
- Values are compared conservatively: `00123` differs from `123`, and numeric `123` differs from text `"123"`.
- XLSX stored values are compared, not visual formatting. CSV inference supports common encodings/delimiters only.
- Insights require explicit column mapping and indicate events, not business causality.
- History belongs to one local installation. Ephemeral cloud hosting can clear it between restarts unless persistent storage is configured.

## Roadmap

- Parquet support and configurable normalization policies
- Scheduled comparisons and SQL snapshot sources
- Local comparison history and richer change analytics

## License

[MIT](LICENSE)
