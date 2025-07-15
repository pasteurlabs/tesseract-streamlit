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
def main(
    url: str,
    output: io.TextIOWrapper,
    user_code: Path | None,
) -> None:
    """Generates a Streamlit app from Tesseract OpenAPI schemas.

    URL is the address to the Tesseract you'd like to generate your
    interface for.

    OUTPUT is the file location to write the Streamlit app script. Must
    have a '.py' file extension, or be a dash '-' to pipe to stdout.

    The generated script can then be passed to the 'streamlit run'
    command to serve the app.
    """
    if not (output.name.endswith(".py") or (output.name == "<stdout>")):
        raise click.UsageError(
            "OUTPUT must either be '-' (stdout), or a script name ending with "
            "a '.py' extension."
        )
    test_var = os.getenv("TESSERACT_STREAMLIT_TESTING", default="0")
    test = test_var.lower() in {"1", "yes", "true", "on", "enabled"}
    env = Environment(
        loader=FileSystemLoader(PACKAGE_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("templates/template.j2")
    render_kwargs = extract_template_data(url, user_code)
    rendered_code = template.render(**render_kwargs, test=test)
    output.write(rendered_code)
