from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PARENT_DIR = Path(__file__).parent


# @pytest.mark.xfail
# def test_pyvista_vis() -> None:
#     """Tests if PyVista visuals are running without throwing exceptions."""
#     app = AppTest.from_file(PARENT_DIR / "pyvista_vis.py", default_timeout=60)
#     app.run()
#     assert not app.exception

def test_import_pyvista() -> None:
    import pyvista as pv
