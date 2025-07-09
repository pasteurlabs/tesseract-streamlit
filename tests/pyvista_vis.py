# from https://github.com/edsaac/stpyvista?tab=readme-ov-file#-minimal-example
import asyncio

import pyvista as pv
from stpyvista.vtkjs_backend import export_vtksz, stpyvista

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

## Pass a key to avoid re-rendering at each page change
vtk_bytes = asyncio.run(export_vtksz(plotter))
stpyvista(vtk_bytes, key="pv_cube")
