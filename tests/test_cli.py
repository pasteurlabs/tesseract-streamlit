import os
import tempfile
from pathlib import Path
from unittest.mock import patch

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


def test_no_url_no_from_image() -> None:
    """Error when neither URL nor --from-image is provided."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code != 0


def test_url_and_from_image_exclusive(goodbyeworld_url: str) -> None:
    """Error when both URL and --from-image are provided."""
    runner = CliRunner()
    result = runner.invoke(cli, [goodbyeworld_url, "--from-image", "some-image"])
    assert result.exit_code != 0


def test_auto_launch(goodbyeworld_url: str) -> None:
    """When output is omitted, app is written to cache and streamlit is launched."""
    runner = CliRunner()
    with patch("tesseract_streamlit.cli.run_streamlit", return_value=0) as mock_run:
        result = runner.invoke(cli, [goodbyeworld_url])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    app_path = mock_run.call_args[0][0]
    assert app_path.exists()
    assert app_path.suffix == ".py"


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

    # Note: AppTest.set_value() bypasses UI validation, so we only test valid values
    # The min_value/max_value constraints are enforced by the browser UI, not Python

    # Test manually set step
    app.number_input(key="number.height").increment().run()
    height_after_decrement = app.number_input(key="number.height").value
    assert height_after_decrement == 175.1, (
        f"Height should be incremented in steps 0.1, but got {height_after_decrement - 175}"
    )
    # reset to original default
    app.number_input(key="number.height").decrement().run()

    app.number_input(key="number.weight").set_value(83.0).run()
    app.text_area(key="textarea.leg_lengths").input("[100.0, 100.0]").run()
    app.text_input(key="int.hobby.name").input("hula hoop").run()
    app.checkbox(key="boolean.hobby.active").check().run()
    app.number_input(key="int.hobby.experience").set_value(3).run()
    app.button[0].click().run()
    assert not app.exception
    tess_output = orjson.loads(app.json[1].value)
    with open(PARENT_DIR / "tess-out.json", "rb") as f:
        sample_output = orjson.loads(f.read())
    assert tess_output == sample_output


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
