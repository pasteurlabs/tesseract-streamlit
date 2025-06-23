from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib.figure import Figure


def _poly_eval(
    coeffs: list[float], x: npt.NDArray[np.floating]
) -> npt.NDArray[np.floating]:
    poly = np.polynomial.Polynomial(coeffs)
    return poly(x)


def polynomial_power(inputs: dict[str, Any]) -> Figure:
    """Displays the polynomial defined by coeffs provided in the inputs.

    The polynomial displayed here is a power series. It's nice. Thank
    you, numpy.
    """
    x = np.linspace(0.0, 10.0, 100)
    y = _poly_eval(inputs["coeffs"], x)
    fig, ax = plt.subplots()
    ax.plot(x, y)
    return fig


def _cheby_eval(
    coeffs: list[float], x: npt.NDArray[np.floating]
) -> npt.NDArray[np.floating]:
    poly = np.polynomial.chebyshev.Chebyshev(coeffs)
    return poly(x)


def cheby_polynomial(inputs: dict[str, Any]) -> Figure:
    """Displays the polynomial defined by coeffs provided in the inputs.

    The polynomial displayed here is a Chebyshev series. It's nice.
    Thank you, numpy.
    """
    x = np.linspace(0.0, 10.0, 100)
    y = _cheby_eval(inputs["coeffs"], x)
    fig, ax = plt.subplots()
    ax.plot(x, y)
    return fig


def _gaussian_grid(
    x: npt.NDArray[np.float32],
    y: npt.NDArray[np.float32],
    var_x: float,
    var_y: float,
    mean_x: float,
    mean_y: float,
) -> npt.NDArray[np.float32]:
    x_grid, y_grid = np.meshgrid(x, y)
    return np.exp(
        -(
            (0.5 * np.square(x_grid - mean_x) / var_x)
            + (0.5 * np.square(y_grid - mean_y) / var_y)
        )
    )


def gaussian(outputs: dict[str, Any]) -> Figure:
    fig, ax = plt.subplots()
    x, y = outputs["x_data"], outputs["y_data"]
    data = _gaussian_grid(
        x,
        y,
        outputs["var_x"],
        outputs["var_y"],
        outputs["mean_x"],
        outputs["mean_y"],
    )
    ax.contourf(x, y, data)
    return fig
