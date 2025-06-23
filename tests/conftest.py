from pathlib import Path

import pytest
import tesseract_core
from tesseract_core.sdk import engine

from tesseract_streamlit import parse

PARENT_DIR = Path(__file__).parent


@pytest.fixture
def tesseract_url() -> str:
    """Builds, serves, and yields a test Tesseract URL."""
    tesseract_core.build_tesseract(PARENT_DIR / "goodbyeworld", "latest")
    tess = tesseract_core.Tesseract.from_image("goodbyeworld")
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
