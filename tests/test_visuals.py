import subprocess
from pathlib import Path

PARENT_DIR = Path(__file__).parent


def test_pyvista_vis() -> None:
    """Tests if PyVista visuals are running without throwing exceptions."""
    vis_path = PARENT_DIR / "pyvista_vis.py"
    try:
        result = subprocess.run(
            ["streamlit", "run", str(vis_path)],
            capture_output=True,
            timeout=10,
        )
        output = (result.stdout + result.stderr).decode()
    except subprocess.TimeoutExpired as e:
        output = ((e.stdout or b"") + (e.stderr or b"")).decode()
    assert "VisualizationError" not in output
