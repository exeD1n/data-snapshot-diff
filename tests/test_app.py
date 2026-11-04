from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_demo_user_journey_renders_expected_results(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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

    save_button = next(button for button in app.button if button.label == "Сохранить в историю")
    save_button.click().run()
    assert any("сохранён локально" in success.value for success in app.success)

    app.sidebar.radio[0].set_value("История").run()
    assert any(header.value == "История сравнений" for header in app.subheader)
    assert len(app.download_button) == 1
    assert app.selectbox[0].value.endswith("Сравнение данных")
