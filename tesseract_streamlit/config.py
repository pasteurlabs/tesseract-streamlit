"""Config module for ``tesseract-streamlit``.

Utilities for configuring and setting up app data.
Currently contains no public routines.
"""

import importlib.resources
import shutil
from pathlib import Path

import platformdirs

from . import __version__


def _copy_favicon() -> Path:
    """Copies the Tesseract favicon into the user's data directory.

    Returns:
        Path to the favicon file in the user's data directory.
    """
    shared_dir = platformdirs.user_data_path(
        appname="tesseract-streamlit",
        appauthor="pasteur-labs",
        version=__version__,
    )
    shared_dir.mkdir(parents=True, exist_ok=True)
    image_name = "favicon.ico"
    target_path = shared_dir / image_name
    resources = importlib.resources.files("tesseract_streamlit.resources")
    if target_path.exists():
        return target_path
    with (
        resources.joinpath(image_name).open("rb") as src,
        target_path.open("wb") as dst,
    ):
        shutil.copyfileobj(src, dst)
    return target_path
