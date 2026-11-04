from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_demo_user_journey_renders_expected_results():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"), default_timeout=15).run()

    assert not app.exception
    metric_values = {metric.label: metric.value for metric in app.metric}
    assert metric_values == {
        "Строк было": "6",
        "Строк стало": "6",
        "Добавлено": "1",
        "Отсутствует": "1",
        "Изменено записей": "2",
        "Без изменений": "3",
        "Изменено ячеек": "2",
    }
    markdown = "\n".join(item.value for item in app.markdown)
    assert "P100: цена выросла на 150 (15.0%)." in markdown
    assert "P101: остаток изменился с 4 до 0" in markdown
    assert len(app.download_button) == 1
