"""Streamlit interface for Data Snapshot Diff."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from data_snapshot_diff.comparator import compare_snapshots
from data_snapshot_diff.exporter import export_excel
from data_snapshot_diff.insights import build_insights
from data_snapshot_diff.loader import DataLoadError, list_excel_sheets, load_file
from data_snapshot_diff.validation import DataValidationError

st.set_page_config(page_title="Data Snapshot Diff", page_icon="🔎", layout="wide")

st.markdown(
    """
<style>
.block-container {max-width: 1200px; padding-top: 2rem;}
[data-testid="stMetric"] {
  background:#f7f9fc; border:1px solid #e2e8f0; padding:14px; border-radius:12px;
}
.hero {
  padding:22px 26px; border-radius:16px; background:linear-gradient(120deg,#102a43,#2563eb);
  color:white; margin-bottom:20px;
}
.hero h1 {margin:0; color:white;} .hero p {margin:8px 0 0; opacity:.9;}
</style>
<div class="hero">
  <h1>Data Snapshot Diff</h1>
  <p>Найдите изменения между двумя версиями бизнес-данных за несколько секунд</p>
</div>
""",
    unsafe_allow_html=True,
)

MAX_PREVIEW = 100
EXAMPLES = Path(__file__).parent / "examples"


def load_uploaded(uploaded, label: str) -> pd.DataFrame | None:
    if uploaded is None:
        return None
    try:
        sheet: str | int = 0
        if uploaded.name.lower().endswith(".xlsx"):
            sheets = list_excel_sheets(uploaded)
            uploaded.seek(0)
            sheet = st.selectbox(f"Лист: {label}", sheets, key=f"sheet_{label}")
        uploaded.seek(0)
        return load_file(uploaded, uploaded.name, sheet_name=sheet)
    except DataLoadError as exc:
        st.error(str(exc))
        return None


def demo_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    return (
        load_file((EXAMPLES / "products_before.csv").read_bytes(), "products_before.csv"),
        load_file((EXAMPLES / "products_after.csv").read_bytes(), "products_after.csv"),
    )


st.subheader("1. Загрузите два снимка данных")
st.caption(
    "CSV или XLSX, до 25 МБ каждый. Файлы обрабатываются в памяти и не отправляются во внешние API."
)
left, right = st.columns(2)
with left:
    old_upload = st.file_uploader("Старая версия", type=["csv", "xlsx"])
with right:
    new_upload = st.file_uploader("Новая версия", type=["csv", "xlsx"])

demo = st.toggle("Использовать демоданные интернет-магазина", value=True)
if demo:
    old_frame, new_frame = demo_frames()
    st.success("Демоданные загружены: каталог товаров до и после обновления.")
else:
    old_frame = load_uploaded(old_upload, "старая версия")
    new_frame = load_uploaded(new_upload, "новая версия")

if old_frame is not None and new_frame is not None:
    common_columns = [column for column in old_frame.columns if column in new_frame.columns]
    st.subheader("2. Настройте сравнение")
    preview_left, preview_right = st.columns(2)
    with preview_left:
        st.caption(f"Старая версия · {len(old_frame):,} строк")
        st.dataframe(old_frame.head(5), use_container_width=True, hide_index=True)
    with preview_right:
        st.caption(f"Новая версия · {len(new_frame):,} строк")
        st.dataframe(new_frame.head(5), use_container_width=True, hide_index=True)

    default_keys = ["sku"] if "sku" in common_columns else common_columns[:1]
    keys = st.multiselect(
        "Ключ записи (можно выбрать несколько колонок)", common_columns, default=default_keys
    )
    optional = [column for column in common_columns if column not in keys]
    business_left, business_right = st.columns(2)
    with business_left:
        price = st.selectbox(
            "Колонка цены (необязательно)",
            [None, *optional],
            index=([None, *optional].index("price") if "price" in optional else 0),
        )
    with business_right:
        stock = st.selectbox(
            "Колонка остатка (необязательно)",
            [None, *optional],
            index=([None, *optional].index("stock") if "stock" in optional else 0),
        )

    if st.button("Сравнить данные", type="primary", use_container_width=True) or demo:
        try:
            result = compare_snapshots(old_frame, new_frame, keys)
        except DataValidationError as exc:
            st.error("Сравнение остановлено: выбранный ключ небезопасен.")
            for issue in exc.issues:
                st.warning(issue.message)
                if not issue.examples.empty:
                    st.dataframe(issue.examples, hide_index=True)
        else:
            st.subheader("3. Результат сравнения")
            metrics = result.metrics
            metric_items = [
                ("Строк было", metrics["old_rows"]),
                ("Строк стало", metrics["new_rows"]),
                ("Добавлено", metrics["added_records"]),
                ("Отсутствует", metrics["missing_records"]),
                ("Изменено записей", metrics["changed_records"]),
                ("Без изменений", metrics["unchanged_records"]),
                ("Изменено ячеек", metrics["changed_cells"]),
            ]
            for columns, offset in ((st.columns(4), 0), (st.columns(3), 4)):
                for column, (label, value) in zip(columns, metric_items[offset:], strict=False):
                    column.metric(label, value)
            st.info(
                "«Отсутствует» означает, что запись не найдена в новой выгрузке. "
                "Это не доказывает, что она удалена из исходной системы."
            )

            st.subheader("4. Детализация")
            tabs = st.tabs(["Изменённые поля", "Добавленные", "Отсутствующие", "Схема"])
            with tabs[0]:
                query = st.text_input("Поиск по ключу", placeholder="Например, P100")
                details = result.changed
                if query and not details.empty:
                    mask = (
                        details[keys]
                        .astype(str)
                        .apply(lambda row: row.str.contains(query, case=False).any(), axis=1)
                    )
                    details = details.loc[mask]
                st.dataframe(details.head(MAX_PREVIEW), use_container_width=True, hide_index=True)
            with tabs[1]:
                st.dataframe(
                    result.added.head(MAX_PREVIEW), use_container_width=True, hide_index=True
                )
            with tabs[2]:
                st.dataframe(
                    result.missing.head(MAX_PREVIEW), use_container_width=True, hide_index=True
                )
            with tabs[3]:
                st.dataframe(result.schema_changes, use_container_width=True, hide_index=True)

            st.subheader("5. Business Insights")
            insights = build_insights(result, price_column=price, stock_column=stock)
            if insights:
                for insight in insights:
                    st.markdown(f"- {insight.message}")
            else:
                st.caption("Для выбранных бизнес-колонок значимых событий не найдено.")

            st.subheader("6. Экспорт")
            st.download_button(
                "Скачать Excel-отчёт",
                data=export_excel(result),
                file_name="data_snapshot_diff_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )
