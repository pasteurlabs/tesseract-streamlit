"""CLI entrypoint for ``tesseract-streamlit``.

Defines the command-line interface for ``tesseract-streamlit``.
The main entrypoint of this module is the ``main()`` function.
"""

import io
import os
from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader

from tesseract_streamlit.parse import extract_template_data

PACKAGE_DIR = Path(__file__).parent


@click.command()
@click.argument("url", type=click.STRING)
@click.argument("output", type=click.File("wt"))
@click.option(
    "-u",
    "--user-code",
    type=click.Path(exists=True, path_type=Path),
    help="User defined functions for plotting inputs / outputs of the Tesseract.",
)
@click.option(
    "--submit/--no-submit",
    is_flag=True,
    help="Use a submit button to trigger output generation.",
    default=True,
    show_default=True,
)
@click.option(
    "--exponential-floats/--no-exponential-floats",
    is_flag=True,
    help="All float input fields formatted as exponential.",
    default=False,
    show_default=True,
)
def main(
    url: str,
    output: io.TextIOWrapper,
    user_code: Path | None,
    submit: bool,
    exponential_floats: bool,
) -> None:
    """Generates a Streamlit app from Tesseract OpenAPI schemas.

    URL is the address to the Tesseract you'd like to generate your
    interface for.

    OUTPUT is the file location to write the Streamlit app script.
    """
    test_var = os.getenv("TESSERACT_STREAMLIT_TESTING", default="0")
    test = test_var.lower() in {"1", "yes", "true", "on", "enabled"}
    env = Environment(
        loader=FileSystemLoader(PACKAGE_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("templates/template.j2")
    render_kwargs = extract_template_data(url, user_code, submit)
    rendered_code = template.render(
        **render_kwargs,
        test=test,
        exponential_floats=exponential_floats,
    )
    output.write(rendered_code)
