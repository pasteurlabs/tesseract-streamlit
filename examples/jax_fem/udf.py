import typing

import numpy as np
import pyvista as pv


def _build_geometry(
    params: np.ndarray,
    radius: float,
) -> list[pv.PolyData]:
    """Build a pyvista geometry from the parameters.

    The parameters are expected to be of shape (n_chains, n_edges_per_chain + 1, 3),
    """
    n_chains = params.shape[0]
    geometry = []

    for chain in range(n_chains):
        tube = pv.Spline(points=params[chain]).tube(radius=radius, capping=False)
        geometry.append(tube)

    return geometry


def _compute_sdf(
    params: np.ndarray,
    radius: float,
    Lx: float,
    Ly: float,
    Nx: int,
    Ny: int,
) -> pv.PolyData:
    """Create a pyvista plane that has the SDF values stored as a vertex attribute.

    The SDF field is computed based on the geometry defined by the parameters.
    """
    grid_coords = pv.Plane(
        center=(0, 0, 0),
        direction=(0, 0, 1),
        i_size=Lx,
        j_size=Ly,
        i_resolution=Nx - 1,
        j_resolution=Ny - 1,
    )
    grid_coords = grid_coords.triangulate()

    geometries = _build_geometry(
        params,
        radius=radius,
    )

    sdf_field = None

    for geometry in geometries:
        # Compute the implicit distance from the geometry to the grid coordinates.
        # The implicit distance is a signed distance field, where positive values
        # are outside the geometry and negative values are inside.
        this_sdf = grid_coords.compute_implicit_distance(geometry.triangulate())
        if sdf_field is None:
            sdf_field = this_sdf
        else:
            sdf_field["implicit_distance"] = np.minimum(
                sdf_field["implicit_distance"], this_sdf["implicit_distance"]
            )

    return sdf_field


def input_geometry(inputs: dict[str, typing.Any]) -> pv.Plotter:
    """Display the geometry defined by the parameters.

    Shows the chains formed of bars, and the signed distance field
    around them.
    """
    bar_params, bar_radius = np.array(inputs["bar_params"]), inputs["bar_radius"]
    Lx, Ly, Nx, Ny = inputs["Lx"], inputs["Ly"], inputs["Nx"], inputs["Ny"]
    geometries = _build_geometry(bar_params, bar_radius)
    # Concatenate all pipe geometries into a single PolyData object
    geometry = sum(geometries, start=pv.PolyData())
    sdf = _compute_sdf(bar_params, radius=bar_radius, Lx=Lx, Ly=Ly, Nx=Nx, Ny=Ny)
    isoval = sdf.contour(isosurfaces=[0.0], scalars="implicit_distance")

    plotter = pv.Plotter()
    plotter.add_mesh(geometry, color="lightblue", show_edges=True, edge_color="black")
    plotter.add_mesh(
        sdf, scalars="implicit_distance", cmap="coolwarm", show_edges=False
    )
    plotter.add_mesh(isoval, color="red", show_edges=True, line_width=2)
    return plotter
