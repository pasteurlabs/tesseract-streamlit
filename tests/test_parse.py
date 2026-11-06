import ast
import math
import random
import types
import typing
from pathlib import Path

import orjson
import pytest
import pyvista as pv
from jinja2 import Environment, FileSystemLoader
from streamlit.testing.v1 import AppTest

from tesseract_streamlit import parse

PACKAGE_DIR = Path(__file__).parent.parent / "tesseract_streamlit"

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
    return {udf["name"] for udf in udfs}


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
    top_level_required = set(resolved_schema.get("required", []))
    mock_input_fields = parse._simplify_schema(
        resolved_schema["properties"], required_keys=top_level_required
    )
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


@pytest.mark.parametrize("url", ["localhost:8000", "127.0.0.1:8000"])
def test_url_without_scheme(url: str, mock_schema: bytes, monkeypatch) -> None:
    requested = []

    def fake_get(request_url, *args, **kwargs):
        requested.append(request_url)
        return types.SimpleNamespace(content=mock_schema)

    monkeypatch.setattr(parse.requests, "get", fake_get)
    template_data = parse.extract_template_data(url, None, True)
    assert requested == [f"http://{url}/openapi.json"]
    assert template_data["url"] == f"http://{url}"


def test_newline_in_field_description() -> None:
    """Descriptions with newlines must not produce invalid Python (GH-87)."""
    env = Environment(
        loader=FileSystemLoader(str(PACKAGE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("templates/template.j2")
    schema = [
        parse.JinjaField(
            container="container_foo",
            parent_container="st",
            uid="foo",
            stem="foo",
            key="foo",
            type="array",
            title="Foo",
            description="first line\nsecond line",
            number_constraints={},
        ),
    ]
    rendered = template.render(
        schema=schema,
        metadata={"title": "T", "version": "0", "description": "d"},
        url="http://localhost:0",
        needs_pyvista=False,
        udfs=None,
        udf_defs=None,
        test=True,
        favicon_path="icon.png",
    )
    # The rendered code must be valid Python — this was the bug in GH-87
    ast.parse(rendered)


@pytest.mark.parametrize(
    "description",
    ['The "x" coordinate', r"Angle \theta, read from C:\xdata", 'a "b"\nc \\ d'],
)
def test_quotes_and_backslashes_in_description(description: str) -> None:
    env = Environment(
        loader=FileSystemLoader(str(PACKAGE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("templates/template.j2")
    schema = [
        parse.JinjaField(
            container="container_foo",
            parent_container="st",
            uid="foo",
            stem="foo",
            key="foo",
            type="array",
            title="Foo",
            description=description,
            number_constraints={},
        ),
    ]
    rendered = template.render(
        schema=schema,
        metadata={"title": "T", "version": "0", "description": description},
        url="http://localhost:0",
        needs_pyvista=False,
        udfs=None,
        udf_defs=None,
        test=True,
        favicon_path="icon.png",
    )
    strings = {
        node.value
        for node in ast.walk(ast.parse(rendered))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert description.replace("\n", " ") in strings


@pytest.mark.parametrize("text", ['The "x" file', r"C:\xdata\theta"])
def test_quotes_and_backslashes_in_titles_and_defaults(text: str) -> None:
    env = Environment(
        loader=FileSystemLoader(str(PACKAGE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("templates/template.j2")
    schema = [
        parse.JinjaField(
            container="container_foo",
            parent_container="st",
            uid="foo",
            stem="foo",
            key="foo",
            type="string",
            title=text,
            description="d",
            default=text,
            number_constraints={},
        ),
    ]
    udf = parse.FuncDescription(name="plot", title=text, docs="", backend="builtin")
    rendered = template.render(
        schema=schema,
        metadata={"title": text, "version": "0", "description": "d"},
        url="http://localhost:0",
        needs_pyvista=False,
        udfs={"inputs": [udf], "outputs": [], "both": []},
        udf_defs=None,
        test=True,
        favicon_path="icon.png",
    )
    strings = {
        node.value
        for node in ast.walk(ast.parse(rendered))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert text in strings
    assert f"**{text}**" in strings
    assert f"{text} v0 - Tesseract Streamlit" in strings


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


@pytest.mark.parametrize(
    "field_type,bounds,expected",
    [
        ("integer", {"exclusiveMinimum": 0, "exclusiveMaximum": 10}, (1, 9)),
        ("integer", {"exclusiveMinimum": 0.5}, (1, None)),
        (
            "number",
            {"exclusiveMinimum": 2.0, "maximum": 6.0},
            (math.nextafter(2.0, math.inf), 6.0),
        ),
        (
            "number",
            {"minimum": 1.0, "exclusiveMaximum": 5.0},
            (1.0, math.nextafter(5.0, -math.inf)),
        ),
        ("number", {"minimum": 3.0, "exclusiveMinimum": 2.0}, (3.0, None)),
    ],
)
def test_exclusive_number_bounds(field_type, bounds, expected) -> None:
    field = parse._format_field("x", {"type": field_type, **bounds}, [], use_title=True)
    constraints = field["number_constraints"]
    assert (constraints["min_value"], constraints["max_value"]) == expected


@pytest.mark.parametrize(
    "shape,expected",
    [
        ({"type": "array", "items": {"type": "integer"}}, "array"),
        ({"type": "array", "minItems": 0, "maxItems": 0}, "number"),
        ({"type": "array", "minItems": 1, "maxItems": 1}, "array"),
    ],
)
def test_array_field_type_from_shape(shape, expected) -> None:
    field_data = {
        "type": "object",
        "properties": {
            "object_type": {"type": "string", "const": "array"},
            "shape": shape,
            "dtype": {"type": "string"},
            "data": {},
        },
    }
    field = parse._format_field("x", field_data, [], use_title=True)
    assert field["type"] == expected


def _scalar_array_field(dtype: str) -> dict[str, typing.Any]:
    return {
        "type": "object",
        "properties": {
            "object_type": {"type": "string", "const": "array"},
            "shape": {"type": "array", "minItems": 0, "maxItems": 0},
            "dtype": {"type": "string", "examples": [dtype]},
            "data": {},
        },
    }


@pytest.mark.parametrize(
    "dtype,expected",
    [
        ("float32", "number"),
        ("int32", "integer"),
        ("uint8", "integer"),
        ("bool", "boolean"),
    ],
)
def test_scalar_field_type_from_dtype(dtype, expected) -> None:
    field = parse._format_field("x", _scalar_array_field(dtype), [], use_title=True)
    assert field["type"] == expected


def test_scalar_int_and_bool_widgets() -> None:
    env = Environment(
        loader=FileSystemLoader(str(PACKAGE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("templates/template.j2")
    schema = [
        parse._input_to_jinja(
            parse._format_field(key, _scalar_array_field(dtype), [], use_title=True)
        )
        for key, dtype in [("count", "int32"), ("flag", "bool")]
    ]
    rendered = template.render(
        schema=schema,
        metadata={"title": "T", "version": "0", "description": "d"},
        url="http://localhost:0",
        needs_pyvista=False,
        udfs=None,
        udf_defs=None,
        test=True,
        favicon_path="icon.png",
    )
    app = AppTest.from_string(rendered, default_timeout=10)
    app.run()
    count = app.number_input(key="int.count")
    assert count.proto.data_type == count.proto.DataType.INT
    assert app.checkbox(key="boolean.flag").value is False
