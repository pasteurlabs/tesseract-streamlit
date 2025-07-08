from pathlib import Path

import pytest
import tesseract_core
from tesseract_core.sdk import engine

from tesseract_streamlit import parse

PARENT_DIR = Path(__file__).parent


def tess_build(tess_name: str) -> tesseract_core.Tesseract:
    """Builds and returns a Tesseract.

    Tesseract and its parent directory must have the same name.
    """
    tesseract_core.build_tesseract(PARENT_DIR / tess_name, "latest")
    tess = tesseract_core.Tesseract.from_image(tess_name)
    return tess


@pytest.fixture
def goodbyeworld_url() -> str:
    """Builds, serves, and yields goodbyeworld test Tesseract URL."""
    tess = tess_build("goodbyeworld")
    port = engine.get_free_port()
    tess.serve(str(port))
    yield f"http://localhost:{port}"
    tess.teardown()


@pytest.fixture
def zerodim_url() -> str:
    """Builds, serves, and yields zerodim test Tesseract URL."""
    tess = tess_build("zerodim")
    port = engine.get_free_port()
    tess.serve(str(port))
    yield f"http://localhost:{port}"
    tess.teardown()


@pytest.fixture
def mock_schema() -> bytes:
    with open(PARENT_DIR / "mock-schema.json", "rb") as f:
        return f.read()


@pytest.fixture
def mock_schema_fields() -> bytes:
    with open(PARENT_DIR / "mock-schema-fields.json", "rb") as f:
        return f.read()


def func_descr_list(group: str) -> list[parse.FuncDescription]:
    return [
        parse.FuncDescription(
            name=f"test_{group}_func_{num}",
            title=f"This function is test {num}.",
            docs="This is some documentation.\nOh my.",
            backend="builtin",
        )
        for num in range(1, 10)
    ]


@pytest.fixture
def mock_udf_reg() -> parse.UdfRegister:
    return parse.UdfRegister(
        inputs=func_descr_list("in"),
        outputs=func_descr_list("out"),
        both=func_descr_list("both"),
    )
