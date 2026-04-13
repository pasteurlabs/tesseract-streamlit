"""Runner utilities for ``tesseract-streamlit``.

Provides functions for serving Tesseracts, launching Streamlit,
and managing temporary app files.
"""

import subprocess
import sys
import time
from pathlib import Path

import platformdirs
import requests


def get_app_path() -> Path:
    """Return a path in the user cache dir for the generated app."""
    cache_dir = platformdirs.user_cache_path(
        appname="tesseract-streamlit",
        appauthor="pasteur-labs",
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "app.py"


def wait_for_tesseract(
    url: str, timeout: float = 60.0, poll_interval: float = 0.5
) -> None:
    """Block until the Tesseract at *url* responds, or raise on timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = requests.get(f"{url}/openapi.json", timeout=2)
            if resp.status_code == 200:
                return
        except requests.ConnectionError:
            pass
        time.sleep(poll_interval)
    raise TimeoutError(f"Tesseract at {url} did not become ready within {timeout}s")


def serve_tesseract(image_name: str) -> tuple[str, object]:
    """Serve a Tesseract from a container image.

    Returns:
        A ``(url, context_manager)`` tuple. The context manager's
        ``__exit__`` tears down the served Tesseract.
    """
    import tesseract_core
    from tesseract_core.sdk import engine

    port = engine.get_free_port()
    ctx = tesseract_core.Tesseract.from_image(image_name, port=str(port))
    ctx.__enter__()
    url = f"http://localhost:{port}"
    return url, ctx


def run_streamlit(app_path: Path) -> int:
    """Launch ``streamlit run`` and block until it exits.

    Returns:
        The process exit code.
    """
    result = subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path)],
        check=False,
    )
    return result.returncode
