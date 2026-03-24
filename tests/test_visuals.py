import subprocess
import tempfile
from pathlib import Path

PARENT_DIR = Path(__file__).parent
TIMEOUT = 3  # seconds


def test_pyvista_vis_happy() -> None:
    """Tests if PyVista visuals are running without throwing exceptions."""
    vis_path = PARENT_DIR / "pyvista_vis.py"
    try:
        result = subprocess.run(
            ["streamlit", "run", str(vis_path)],
            capture_output=True,
            timeout=TIMEOUT,
        )
        output = (result.stdout + result.stderr).decode()
    except subprocess.TimeoutExpired as e:
        output = ((e.stdout or b"") + (e.stderr or b"")).decode()
    assert "VisualizationError" not in output


def test_pyvista_vis_sad() -> None:
    """Tests if PyVista visuals throws exception when app has mistakes."""
    vis_path = PARENT_DIR / "pyvista_vis.py"
    vis_bytes = vis_path.read_bytes()
    vis_bytes = vis_bytes.replace(
        b'plotter.background_color = "white"',
        b'plotter.background_color = "not a real color"',
        1,
    )
    with tempfile.NamedTemporaryFile("wb", suffix=".py") as tf:
        tf.write(vis_bytes)
        tf.flush()
        try:
            result = subprocess.run(
                ["streamlit", "run", tf.name],
                capture_output=True,
                timeout=TIMEOUT,
            )
            output = (result.stdout + result.stderr).decode()
        except subprocess.TimeoutExpired as e:
            output = ((e.stdout or b"") + (e.stderr or b"")).decode()
    assert "VisualizationError" in output
