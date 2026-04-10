"""CLI entrypoint for ``tesseract-streamlit``.

Defines the command-line interface for ``tesseract-streamlit``.
The main entrypoint of this module is the ``main()`` function.
"""

import os
import sys
import typing
from pathlib import Path

import typer
from jinja2 import Environment, FileSystemLoader
from requests.exceptions import ConnectionError
from rich.console import Console

from tesseract_streamlit.config import _copy_favicon
from tesseract_streamlit.parse import extract_template_data
from tesseract_streamlit.runner import (
    get_app_path,
    run_streamlit,
    serve_tesseract,
    wait_for_tesseract,
)

PACKAGE_DIR = Path(__file__).parent

err_console = Console(stderr=True)
cli = typer.Typer()


@cli.command()
def main(
    url: typing.Annotated[
        str | None,
        typer.Argument(
            help="Address to the Tesseract to use in the app. Not needed with --from-image."
        ),
    ] = None,
    output: typing.Annotated[
        str | None,
        typer.Argument(
            help=(
                "File location to write the Streamlit app script. Must have a "
                "'.py' file extension, or be a dash '-' to pipe to stdout. "
                "Omit to auto-launch Streamlit."
            )
        ),
    ] = None,
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
    from_image: typing.Annotated[
        str | None,
        typer.Option(
            "--from-image",
            help="Tesseract image to serve automatically.",
        ),
    ] = None,
) -> None:
    """Generates a Streamlit app from Tesseract OpenAPI schemas.

    When OUTPUT is omitted, the app is written to a cache file and
    Streamlit is launched automatically.
    """
    # --- Validate arguments ---
    if url is None and from_image is None:
        err_console.print(
            "[bold red]Error: [/bold red]"
            "Provide either a URL argument or the --from-image option."
        )
        raise typer.Exit(code=2)

    if url is not None and from_image is not None:
        err_console.print(
            "[bold red]Error: [/bold red]URL and --from-image are mutually exclusive."
        )
        raise typer.Exit(code=2)

    if output is not None and output != "-" and not output.endswith(".py"):
        err_console.print(
            "[bold red]Error: [/bold red]"
            "OUTPUT must either be '-' (stdout), or a script name ending with "
            "a '.py' extension. Aborting."
        )
        raise typer.Exit(code=2)

    # --- Determine output mode ---
    auto_launch = output is None
    if output == "-":
        app_path = None  # stdout
    elif output is not None:
        app_path = Path(output)
    else:
        app_path = get_app_path()

    # --- Serve Tesseract if requested ---
    tesseract_ctx = None
    try:
        if from_image is not None:
            err_console.print(
                f"[green]Serving Tesseract from image '{from_image}'...[/green]"
            )
            try:
                url, tesseract_ctx = serve_tesseract(from_image)
            except Exception as e:
                err_console.print(
                    "[bold red]Error: [/bold red]"
                    f"Failed to serve Tesseract from image '{from_image}': {e}"
                )
                raise typer.Exit(code=3) from e
            try:
                wait_for_tesseract(url)
            except TimeoutError as e:
                err_console.print(
                    "[bold red]Error: [/bold red]"
                    f"Tesseract at {url} did not become ready in time."
                )
                raise typer.Exit(code=3) from e

        # --- Generate the app ---
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

        if app_path is None:
            sys.stdout.write(rendered_code)
        else:
            app_path.write_text(rendered_code)

        # --- Auto-launch Streamlit ---
        if auto_launch:
            assert app_path is not None
            err_console.print(f"[green]App written to {app_path}[/green]")
            err_console.print("[green]Launching Streamlit...[/green]")
            exit_code = run_streamlit(app_path)
            raise typer.Exit(code=exit_code)

    finally:
        if tesseract_ctx is not None:
            tesseract_ctx.__exit__(None, None, None)
