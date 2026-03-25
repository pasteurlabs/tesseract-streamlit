from pathlib import Path

PARENT_DIR = Path(__file__).parent


# @pytest.mark.xfail
# def test_pyvista_vis() -> None:
#     """Tests if PyVista visuals are running without throwing exceptions."""
#     app = AppTest.from_file(PARENT_DIR / "pyvista_vis.py", default_timeout=60)
#     app.run()
#     assert not app.exception


def test_visual_imports() -> None:
    import multiprocessing

    multiprocessing.set_start_method("fork", force=True)

    import pyvista as pv

    ## Initialize a plotter object
    plotter = pv.Plotter(window_size=[400, 400])

    ## Create a mesh with a cube
    mesh = pv.Cube()

    ## Add some scalar field associated to the mesh
    mesh["my_scalar"] = mesh.points[:, 2] * mesh.points[:, 0]

    ## Add mesh to the plotter
    plotter.add_mesh(mesh, scalars="my_scalar", cmap="bwr")

    ## Final touches
    plotter.view_isometric()
    plotter.add_scalar_bar()
    plotter.background_color = "white"
