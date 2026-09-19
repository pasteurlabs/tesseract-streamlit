import os
import re
import subprocess
from pathlib import Path

import orjson
import pytest
import tesseract_core
from streamlit.testing.v1 import AppTest
from tesseract_core.sdk import engine
from typer.testing import CliRunner

from tesseract_streamlit.cli import cli

pytest.importorskip("plotly")

EXAMPLE_DIR = Path(__file__).parent.parent / "examples" / "vectoradd_jax"
os.environ["TESSERACT_STREAMLIT_TESTING"] = "1"


def test_vectoradd_jax_example(tmp_path: Path) -> None:
    run_sh = (EXAMPLE_DIR / "run.sh").read_text()
    tag = re.search(r"--branch (\S+)", run_sh).group(1)
    core_dir = tmp_path / "tesseract-core"
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            tag,
            "https://github.com/pasteurlabs/tesseract-core.git",
            str(core_dir),
        ],
        check=True,
    )
    tesseract_core.build_tesseract(core_dir / "examples" / "vectoradd_jax", "latest")
    port = engine.get_free_port()
    with tesseract_core.Tesseract.from_image("vectoradd_jax", port=str(port)):
        result = CliRunner().invoke(
            cli,
            [
                "--user-code",
                str(EXAMPLE_DIR / "udf.py"),
                f"http://localhost:{port}",
                "-",
            ],
        )
        assert result.exit_code == 0
        app = AppTest.from_string(result.output, default_timeout=30)
        app.run()
        app.text_area(key="textarea.a.v").input("[1.0, 2.0]").run()
        app.text_area(key="textarea.b.v").input("[3.0, 4.0]").run()
        app.number_input(key="number.a.s").set_value(2.0).run()
        app.button[0].click().run()

    assert not app.exception
    outputs = orjson.loads(app.json[1].value)
    assert outputs["vector_add"]["result"] == [5.0, 8.0]
    assert outputs["vector_min"]["result"] == [-1.0, 0.0]
    assert len(app.get("plotly_chart")) == 1
