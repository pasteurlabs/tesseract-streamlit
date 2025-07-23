"""CLI entrypoint for ``tesseract-streamlit``.

Defines the command-line interface for ``tesseract-streamlit``.
The main entrypoint of this module is the ``main()`` function.
"""

import os
import typing
from pathlib import Path

import typer
from jinja2 import Environment, FileSystemLoader
from requests.exceptions import ConnectionError
from rich.console import Console

from tesseract_streamlit.config import _copy_favicon
from tesseract_streamlit.parse import extract_template_data

PACKAGE_DIR = Path(__file__).parent

err_console = Console(stderr=True)
cli = typer.Typer()


@cli.command()
def main(
    url: typing.Annotated[
        str,
        typer.Argument(help="Address to the Tesseract to use in the app."),
    ],
    output: typing.Annotated[
        typer.FileTextWrite,
        typer.Argument(
            help=(
                "File location to write the Streamlit app script. Must have a "
                "'.py' file extension, or be a dash '-' to pipe to stdout."
            )
        ),
    ],
    user_code: typing.Annotated[
        Path | None,
        typer.Option(
            "--user-code",
            "-u",
            help=(
                "User defined functions for plotting inputs / outputs of the Tesseract."
            ),
            exists=True,
        ),
    ] = None,
    pretty_headings: typing.Annotated[
        bool,
        typer.Option(
            "--pretty-headings/--no-pretty-headings",
            is_flag=True,
            help=(
                "Formats schema parameters as headings, with spaces and capitalisation."
            ),
        ),
    ] = True,
) -> None:
    """Generates a Streamlit app from Tesseract OpenAPI schemas.

    The generated script can then be passed to the 'streamlit run'
    command to serve the app.
    """
    if not (output.name.endswith(".py") or (output.name == "<stdout>")):
        err_console.print(
            "[bold red]Error: [/bold red]"
            "OUTPUT must either be '-' (stdout), or a script name ending with "
            "a '.py' extension. Aborting."
        )
        raise typer.Exit(code=2)
    test_var = os.getenv("TESSERACT_STREAMLIT_TESTING", default="0")
    test = test_var.lower() in {"1", "yes", "true", "on", "enabled"}
    env = Environment(
        loader=FileSystemLoader(PACKAGE_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("templates/template.j2")
    try:
        render_kwargs = extract_template_data(url, user_code, pretty_headings)
    except ConnectionError as e:
        err_console.print(
            "[bold red]Error: [/bold red]"
            f"Can't seem to find the Tesseract at {url}. "
            "Are you sure it's being served?\n\n"
            "[bold green]Hint: [/bold green]"
            "You can double check using `tesseract ps`. If it's being served, "
            "you can find the correct URL in the 'Host Address' column."
        )
        raise typer.Exit(code=3) from e
    rendered_code = template.render(
        **render_kwargs,
        test=test,
        favicon_path=_copy_favicon(),
    )
    output.write(rendered_code)
