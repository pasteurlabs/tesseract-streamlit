"""Parsing module for ``tesseract-streamlit``.

Utilities for parsing and formatting inputs to be injected into the
Streamlit template.

Routines here handle both the OpenAPI Specification generated for a
Tesseract, and functions passed into the user-defined functions module.
Each are then parsed and formatted into string descriptions, and
structured with lists and dictionaries, for easy injection in the
Streamlit Jinja template.

The object to be passed to the Jinja template is an instance of
``TemplateData``, which may be created using the only entry-point to
this module: ``extract_template_data()``.

All other members are private or ``TypedDict`` definitions.
"""

import copy
import functools
import importlib.util
import inspect
import operator
import sys
import typing
import warnings
from pathlib import Path

import orjson
import pyvista as pv
import requests
from typing_extensions import NotRequired

__all__ = [
    "FuncDescription",
    "JinjaField",
    "TemplateData",
    "TesseractMetadata",
    "UdfRegister",
    "UserDefinedFunctionError",
    "UserDefinedFunctionWarning",
    "extract_template_data",
]


class FuncDescription(typing.TypedDict):
    """Represents a brief summary of a Python function.

    Stores the function's name, the first line of its docstring as the
    title, and the remaining docstring content as documentation.

    This is used in the Streamlit template to inject the functions into
    the app, and annotate their plot outputs with the title and docs
    the user provides.

    backend identifies which plotting library is supported.
    "builtin" indicates that support is provided by Streamlit natively.
    """

    name: str
    title: str
    docs: str
    backend: typing.Literal["builtin", "pyvista"]


class UserDefinedFunctionError(Exception):
    """Exception for invalid user defined functions."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class UserDefinedFunctionWarning(Warning):
    """Warning for user defined functions."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def _describe_func(func: typing.Callable[..., typing.Any]) -> FuncDescription:
    """Create ``FuncDescription`` instance from a function directly.

    Extracts the function name, the first line of the docstring as a
    title, and the remainder of the docstring as the detailed
    documentation.

    Args:
        func: The function to inspect.

    Returns:
        ``FuncDescription`` instance containing extracted metadata.
    """
    return_type = inspect.signature(func).return_annotation
    backend = "pyvista" if return_type is pv.Plotter else "builtin"
    func_name = func.__name__
    if (docstring := inspect.getdoc(func)) is None:
        warnings.warn(
            (
                f"Function '{func_name}' does not have a docstring. Plot "
                "title and descriptions will be populated with empty strings."
            ),
            UserDefinedFunctionWarning,
            stacklevel=2,
        )
        docstring = ""
    title, _, docs = docstring.partition("\n")
    return FuncDescription(
        name=func_name,
        title=title,
        docs=docs.strip(),
        backend=backend,
    )


class UdfRegister(typing.TypedDict):
    """Stores the user-defined function descriptions as a register.

    Each kind of function is stored in its own list, based on what
    parameter it takes. If it takes Tesseract inputs as a parameter,
    it is stored in the list under the 'inputs' key. Likewise for
    Tesseract outputs. If it takes both inputs and outputs, it's stored
    under 'both'.

    This register is passed for injection into the Streamlit app
    template. Storing the functions by the parameters they take enables
    them to be passed the correct parameters in the generated app.
    """

    inputs: list[FuncDescription]
    outputs: list[FuncDescription]
    both: list[FuncDescription]


def _register_udfs(file_path: Path) -> UdfRegister:
    """Populates a ``UdfRegister`` with user-defined plotting functions.

    Args:
        file_path: Location on disk of the user-provided module of
            plotting functions.

    Returns:
        Descriptions of the functions defined under ``file_path``,
        separated into whether they visualise inputs, outputs, or both.
    """
    udf_register = UdfRegister(inputs=[], outputs=[], both=[])
    module_name = file_path.stem

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)

    functions = (
        func
        for name, func in inspect.getmembers(mod, inspect.isfunction)
        if (inspect.getmodule(func) == mod) and (not name.startswith("_"))
    )

    for func in functions:
        args = inspect.getfullargspec(func).args
        if args == ["inputs"]:
            takes = "inputs"
        elif args == ["outputs"]:
            takes = "outputs"
        elif set(args) == {"inputs", "outputs"}:
            takes = "both"
        else:
            raise UserDefinedFunctionError(
                "Function signature must take parameters of 'inputs' and / or "
                f"'outputs'. {func.__name__} has parameters {args}. "
                "Please review this function and try again."
            )
        udf_register[takes].append(_describe_func(func))

    return udf_register


def _chain_subscript(
    data: dict[str, typing.Any], keys: typing.Sequence[str]
) -> typing.Any:
    """Repeatedly subscripts nested dicts from a sequence of keys.

    For example, ``data["key1"]["key2"]["key3"]`` is equivalent to
    ``_chain_subscript(data, ["key1", "key2", "key3"])``.

    Args:
        data: Dictionary of dictionaries (with string keys).
        keys: Keys to be applied as subscripts in order of nesting.

    Returns:
        The value of the dictionary given by repeatedly subscripting
        ``data`` with ``keys``.
    """
    return functools.reduce(operator.getitem, keys, data)


def _resolve_refs(
    schema_node: dict[str, typing.Any], schema: dict[str, typing.Any]
) -> dict[str, typing.Any]:
    """Recursively expands '$ref' paths in the OpenAPI Specification.

    Recursively descends into the nested dictionary, locating '$ref'
    keys. Where these are found, the URI path to elsewhere in the
    dictionary is resolved, yielding a dictionary. This dictionary
    is then merged with the parent dictionary where the '$ref' key was
    located.

    This expands the OpenAPI specification dictionary, allowing more
    simple and explicit processing later.

    Args:
        schema_node: Current node beneath which we wish to resolve.
        schema: Full OpenAPI specification dictionary.

    Returns:
        Schema data stored under '$ref' keys inlined in their parent
        dictionaries.
    """
    # base case: if not a dict / has no $ref, return as-is
    if not isinstance(schema_node, dict):
        return schema_node
    if "$ref" in schema_node:
        schema_node = copy.deepcopy(schema_node)
        ref_path = schema_node.pop("$ref").lstrip("#/").split("/")
        target = copy.deepcopy(_chain_subscript(schema, ref_path))
        # recursively resolve refs
        schema_node.update(_resolve_refs(target, schema))
        return schema_node
    # if dict without $ref, process nested dicts (eg. properties or items)
    resolved = {}
    for key, value in schema_node.items():
        resolved[key] = _resolve_refs(value, schema)
    return resolved


ARRAY_PROPS = {"dtype", "shape", "data"}  # if a dict has these keys => array


def _is_scalar(shape_dict: dict[str, typing.Any]) -> bool:
    """Determines whether or not an array input is a scalar.

    Array dtypes in a Tesseract ``InputSchema`` may be used without
    being wrapped in an Array generic, *eg.* ``Float32``, rather
    than ``Array[Float32]``. In this instance, they are marked up as
    arrays in the OpenAPI Specification, but the Tesseract inputs expect
    a scalar.

    This function checks the shape of a field identified as an "array"
    and determines if it is, in fact, a scalar value.

    Args:
        shape_dict: Dictionary under the "shape" key of an array schema.

    Returns:
        ``True`` if the shape is 0-dimensional, ``False`` otherwise.
    """
    shape_dict = copy.deepcopy(shape_dict)
    min_items, max_items = shape_dict.pop("minItems"), shape_dict.pop("maxItems")
    if min_items == max_items == 0:
        return True
    return False


class _InputField(typing.TypedDict):
    """Simplified schema for an input field in the Streamlit template.

    In order to be rendered, an input needs a type (number, array, etc),
    title, description, and list of ancestors (for nested schemas).
    """

    type: str
    title: str
    description: str
    ancestors: list[str]
    default: NotRequired[typing.Any]


def _key_to_title(key: str) -> str:
    """Formats an OAS key to a title for the web UI."""
    return key.replace("_", " ").title()


def _format_field(
    field_key: str,
    field_data: dict[str, typing.Any],
    ancestors: list[str],
    use_title: bool,
) -> _InputField:
    """Formats a node of the OAS tree representing an input field.

    Args:
        field_key: key of the node in the OAS tree.
        field_data: dictionary of data representing the field.
        ancestors: ordered list of ancestors in which the field is
            nested.
        use_title: whether to use the OAS formatted title, or the
            field_key.

    Returns:
        Formatted input field data.
    """
    field = _InputField(
        type=field_data["type"],
        title=field_data.get("title", field_key) if use_title else field_key,
        description=field_data.get("description", None),
        ancestors=[*ancestors, field_key],
    )
    if "properties" not in field_data:  # signals a Python primitive type
        if field["type"] != "object":
            default_val = field_data.get("default", None)
            if (field_data["type"] == "string") and (default_val is None):
                default_val = ""
            field["default"] = default_val
        return field
    field["title"] = _key_to_title(field_key) if use_title else field_key
    if ARRAY_PROPS <= set(field_data["properties"]):
        data_type = "array"
        if _is_scalar(field_data["properties"]["shape"]):
            data_type = "number"
            field["default"] = field_data.get("default", None)
        field["type"] = data_type
        return field
    # at this point, not an array or primitive, so must be composite
    field["type"] = "composite"
    return field


def _simplify_schema(
    schema_node: dict[str, typing.Any],
    accum: list | None = None,
    ancestors: list | None = None,
    use_title: bool = True,
) -> list[_InputField]:
    """Returns a flat simplified representation of the ``InputSchema``.

    The resolved OpenAPI specification dictionary is visited recursively
    to accumulate ``_InputField`` descriptions of each input field
    required by the Tesseract. These are accumulated in a list, and have
    no nested structure, for ease-of-use in the Streamlit template.

    Nesting is removed by instead creating a list of ancestors for each
    field. This lists each schema below which the input was nested in.

    ``_InputField`` instances may have a "type" of "composite",
    indicating that they aren't inputs at all, but instead get rendered
    as containers in the Streamlit web UI.

    Args:
        schema_node: Current node beneath which we collect inputs.
        accum: List containing the inputs we are accumulating.
        ancestors: Ancestors which the parent node is nested beneath,
            *eg.* the names of the parent schemas, in order.
        use_title: Sets whether to use the OAS generated title. These
            are the parameter names, with spaces instead of underscores,
            and capitalised. If False, will use the parameter name
            without formatting. Default is True.

    Returns:
        List of ``_InputField`` instances, describing the structure of
        the inputs for the Streamlit app.
    """
    if accum is None:
        accum = []
    if ancestors is None:
        ancestors = []
    for child_key, child_val in schema_node.items():
        child_data = _format_field(child_key, child_val, ancestors, use_title)
        accum.append(child_data)
        if child_data["type"] != "composite":
            continue
        accum.extend(
            _simplify_schema(
                child_val["properties"], [], child_data["ancestors"], use_title
            )
        )
    return accum


class TesseractMetadata(typing.TypedDict):
    """Basic info about the Tesseract being interfaced.

    Title, description, and version information to be injected into the
    header of the Streamlit template.
    """

    title: str
    description: str
    version: str


class JinjaField(typing.TypedDict):
    """Input field schema preprocessed for Jinja template compatibilityping.

    Replaces "ancestors" from ``_InputField`` with "parent_container",
    "container", "uid", "stem", and "key".
    """

    parent_container: str
    container: str
    uid: str
    stem: str
    key: str
    type: str
    description: str
    title: str
    default: NotRequired[typing.Any]


def _input_to_jinja(field: _InputField) -> JinjaField:
    """Preprocesses field description for Streamlit Jinja template.

    Takes the minimal ``_InputField`` description of the Tesseract input
    and replaces the "ancestors" list with the formatted strings in
    ``JinjaField``. This improves compatibility with both Jinja and
    Streamlit.

    Args:
        field: The minimal Tesseract input field description.

    Returns:
        JinjaField: Expanded description for the Jinja template.
    """
    field_ = copy.deepcopy(field)
    ancestors = field_.pop("ancestors")
    uid = "_".join(ancestors)
    parent_container = "st"
    if len(ancestors) > 1:
        parent_container = "container_" + "_".join(ancestors[:-1])
    return JinjaField(
        parent_container=parent_container,
        container=f"container_{uid}",
        uid=uid,
        stem=ancestors[-1],
        key=".".join(ancestors),
        **field_,
    )


def _parse_tesseract_oas(
    oas_data: bytes, pretty_headings: bool = True
) -> tuple[TesseractMetadata, list[JinjaField]]:
    """Parses Tesseract OAS into a flat list of dictionaries.

    Recursively resolves the arbitrarily nested ``InputSchema`` for a
    Tesseract API Input Schema. This is primarily to enable a simple
    compatibility layer between Tesseract API and templating engines.

    Args:
        oas_data: the JSON data as an unparsed string.
        pretty_headings: whether to format parameter names as headings.
            Default is True.

    Returns:
        TesseractMetadata:
            Basic info regarding the Tesseract we are interfacing with.
        list[JinjaField]:
            The flattened schema describing the inputs required for the
            Tesseract.
    """
    data = orjson.loads(oas_data)
    apply_descr = data["paths"]["/apply"]["post"]["description"]
    metadata = TesseractMetadata(
        title=data["info"]["title"],
        version=data["info"]["version"],
        description=data["info"].get("description", apply_descr),
    )
    input_schema = data["components"]["schemas"]["Apply_InputSchema"]
    resolved_schema = _resolve_refs(input_schema, data)
    input_fields = _simplify_schema(
        resolved_schema["properties"], use_title=pretty_headings
    )
    jinja_fields = [_input_to_jinja(field) for field in input_fields]
    return metadata, jinja_fields


def _needs_pyvista(udf_register: UdfRegister) -> bool:
    """Determines if Streamlit app needs to support PyVista."""
    for udfs in udf_register.values():
        for udf in udfs:
            if udf["backend"] == "pyvista":
                return True
    return False


class TemplateData(typing.TypedDict):
    """Schema for passing data directly to Jinja template for injection.

    The following key value pairs are:
        metadata: background information on the Tesseract instance.
        schema: structure of the input form.
        url: URI of the running Tesseract instance.
        needs_pyvista: whether to enable PyVista support for the UDFs.
        udf_defs: source code for the UDF definitions.
        udfs: register of the UDFs, sorted by their input parameters.
    """

    metadata: TesseractMetadata
    schema: list[JinjaField]
    url: str
    needs_pyvista: bool
    udf_defs: NotRequired[str]
    udfs: NotRequired[UdfRegister]


def extract_template_data(
    url: str,
    user_code: Path | None,
    pretty_headings: bool,
) -> TemplateData:
    """Formats Tesseract and user-defined function inputs for template.

    Retrieves and parses the OpenAPI specification of the running
    Tesseract. User code is also analysed. These inputs are then
    formatted and pre-processed according to the ``TemplateData`` schema
    to provide all data required to statically render the Streamlit app.

    Args:
        url: URI of the running Tesseract instance.
        user_code: path of the user-defined plotting function module.
        pretty_headings: whether to format parameters names as headings.

    Returns:
        TemplateData:
            Preprocessed data describing the Streamlit app based on the
            ``InputSchema``, ready for injection into the app template.
    """
    response = requests.get(f"{url}/openapi.json")
    metadata, schema = _parse_tesseract_oas(
        response.content, pretty_headings=pretty_headings
    )
    render_kwargs = TemplateData(
        metadata=metadata,
        schema=schema,
        url=url,
        needs_pyvista=False,
    )
    if user_code is not None:
        render_kwargs["udf_defs"] = user_code.read_text()
        udf_register = _register_udfs(user_code)
        render_kwargs["udfs"] = udf_register
        render_kwargs["needs_pyvista"] = _needs_pyvista(udf_register)
    return render_kwargs
