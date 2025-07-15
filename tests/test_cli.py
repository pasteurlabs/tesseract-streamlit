import os
import tempfile
from pathlib import Path

import orjson
from streamlit.testing.v1 import AppTest
from typer.testing import CliRunner

from tesseract_streamlit.cli import cli

PARENT_DIR = Path(__file__).parent
os.environ["TESSERACT_STREAMLIT_TESTING"] = "1"


def test_cli(goodbyeworld_url: str) -> None:
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        app_path = f"{temp_dir}/app.py"
        result = runner.invoke(cli, [goodbyeworld_url, app_path])
        assert result.exit_code == 0
        assert result.output == ""
        assert Path(app_path).exists()


def test_py_extension(goodbyeworld_url: str) -> None:
    """Checks that exception raised if not using '.py' extension."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        app_path = f"{temp_dir}/app"
        result = runner.invoke(cli, [goodbyeworld_url, app_path])
        assert result.exit_code != 0


def test_app(goodbyeworld_url: str) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [goodbyeworld_url, "-"])
    assert result.exit_code == 0
    assert result.output != ""
    app = AppTest.from_string(result.output, default_timeout=3)
    app.run()
    app.number_input(key="number.weight").set_value(83.0).run()
    app.text_area(key="textarea.leg_lengths").input("[100.0, 100.0]").run()
    app.text_input(key="int.hobby.name").input("hula hoop").run()
    app.checkbox(key="boolean.hobby.active").check().run()
    app.number_input(key="int.hobby.experience").set_value(3).run()
    app.button[0].click().run()
    tess_output = orjson.loads(app.json[1].value)
    with open(PARENT_DIR / "tess-out.json", "rb") as f:
        sample_output = orjson.loads(f.read())
    assert tess_output == sample_output
    assert not app.exception


def test_zerodim_pprint(zerodim_url: str) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [zerodim_url, "-"])
    assert result.exit_code == 0
    assert result.output != ""
    app = AppTest.from_string(result.output, default_timeout=3)
    app.run()
    app.number_input(key="int.max_num").set_value(10).run()
    app.button[0].click().run()
    assert not app.exception
