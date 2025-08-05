import random
import typing
from pathlib import Path

import orjson
import pytest
import pyvista as pv

from tesseract_streamlit import parse

PARENT_DIR = Path(__file__).parent


# Testing UDF routines:
# =====================
sample_doc_topline = "This is the first line."
sample_description = """
This is a description for the sample function.

Here is more text with a blank line above.

The three laws of robotics are:
1. a robot may not injure a human being or allow a human to come to harm
2. a robot must obey human orders unless it conflicts with the first law
3. a robot must protect its own existence as long as it does not
   conflict with the first two laws
""".strip()


def sample_func(inputs):
    """This is the first line.

    This is a description for the sample function.

    Here is more text with a blank line above.

    The three laws of robotics are:
    1. a robot may not injure a human being or allow a human to come to harm
    2. a robot must obey human orders unless it conflicts with the first law
    3. a robot must protect its own existence as long as it does not
       conflict with the first two laws
    """
    pass


def test_func_description() -> None:
    description = parse._describe_func(sample_func)
    assert description["name"] == "sample_func", "Incorrect function name extracted"
    assert description["title"] == sample_doc_topline, (
        "Incorrect docstring top line extracted"
    )
    assert description["docs"] == sample_description, (
        "Incorrect description extracted from the docstring"
    )
    assert description["backend"] == "builtin", "Incorrect plotting back-end"
    sample_func.__annotations__["return"] = pv.Plotter
    description = parse._describe_func(sample_func)
    assert description["backend"] == "pyvista", "Incorrect plotting back-end"


def _udf_message(params: typing.Literal["input", "output", "both"]) -> str:
    return f"Not correctly registering {params=} functions"


def _udf_names(udfs: list[parse.FuncDescription]) -> set[str]:
    return set(udf["name"] for udf in udfs)


def test_udf_register() -> None:
    with pytest.warns(
        parse.UserDefinedFunctionWarning,
        match="Function 'gaussian' does not have a docstring.",
    ):
        udf_register = parse._register_udfs(PARENT_DIR / "mock_udfs.py")
    in_names = _udf_names(udf_register["inputs"])
    in_expected = {"polynomial_power", "cheby_polynomial"}
    assert in_names == in_expected, _udf_message("input")
    out_names = _udf_names(udf_register["outputs"])
    out_expected = {"gaussian"}
    assert out_names == out_expected, _udf_message("output")
    both_names = _udf_names(udf_register["both"])
    both_expected = set()
    assert both_names == both_expected, _udf_message("both")


def test_udf_exception() -> None:
    with pytest.raises(
        parse.UserDefinedFunctionError,
        match="not_a_plotting_func has parameters",
    ):
        parse._register_udfs(PARENT_DIR / "bad_udfs.py")


def test_needs_pyvista(mock_udf_reg: parse.UdfRegister) -> None:
    assert not parse._needs_pyvista(mock_udf_reg), (
        "False positive detecting PyVista dependency."
    )
    group = random.choice(list(mock_udf_reg.values()))
    func_descr = random.choice(group)
    func_descr["backend"] = "pyvista"
    assert parse._needs_pyvista(mock_udf_reg), (
        "False negative detecting PyVista dependency."
    )


def test_schema_parse(mock_schema: bytes, mock_schema_fields: bytes) -> None:
    # parse the mock OAS to get the input fields
    schema_data = orjson.loads(mock_schema)
    input_schema = schema_data["components"]["schemas"]["Apply_InputSchema"]
    resolved_schema = parse._resolve_refs(input_schema, schema_data)
    mock_input_fields = parse._simplify_schema(resolved_schema["properties"])
    # check that the input fields match the pre-computed values
    precomputed_fields = orjson.loads(mock_schema_fields)
    assert mock_input_fields == precomputed_fields, (
        "Parsed OAS does not match correct pre-computed field structure."
    )


def test_metadata_extract(mock_schema: bytes) -> None:
    metadata, _ = parse._parse_tesseract_oas(mock_schema)
    reference_vals = {
        "title": "goodbyeworld",
        "version": "1.0.0",
        "description": (
            "Apply the Tesseract to the input data.\n\n"
            "Greet a person whose name is given as input."
        ),
    }
    for key, val in reference_vals.items():
        message = f"Tesseract {key} incorrectly extracted."
        assert val == metadata[key], message


def test_description_from_oas(
    goodbyeworld_url: str,
    goodbyeworld_config: dict[str, str],
    zerodim_url: str,
    zerodim_apply_docstring: str,
) -> None:
    """Checks description text in web UI is pulled properly.

    The default description blurb at the top of the web UI is the
    description provided in tesseract_config.yaml. If this is missing,
    it falls back on the docstring of the apply endpoint.
    """
    # test that default uses tesseract_config.yaml
    gbw_template = parse.extract_template_data(goodbyeworld_url, None, True)
    gbw_descr = gbw_template["metadata"]["description"]
    gbw_config_descr = goodbyeworld_config["description"]
    assert gbw_descr == gbw_config_descr
    # test that fallback uses apply endpoint docstring
    zd_template = parse.extract_template_data(zerodim_url, None, True)
    zd_descr = zd_template["metadata"]["description"]
    zd_apply_docs = (
        f"Apply the Tesseract to the input data.\n\n{zerodim_apply_docstring}"
    )
    assert zd_descr == zd_apply_docs
