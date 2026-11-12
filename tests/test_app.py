from streamlit.testing.v1 import AppTest


def test_app_runs_on_sample_data_and_shows_the_cheapest_plan():
    app = AppTest.from_file("../app.py").run(timeout=30)
    assert not app.exception
    assert any("Cheapest" in el.value for el in app.get("html"))


def test_no_plans_ticked_shows_a_warning_not_a_crash():
    app = AppTest.from_file("../app.py").run(timeout=30)
    for box in app.checkbox:
        box.uncheck()
    app.run(timeout=30)
    assert not app.exception
    assert "Tick at least one plan" in app.warning[0].value
