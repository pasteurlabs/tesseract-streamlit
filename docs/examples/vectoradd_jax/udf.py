import numpy as np
import plotly.graph_objects as go


def plot_vector_addition(inputs, outputs) -> go.Figure:
    """Plot vector addition using the triangle method with Plotly.

    Adds the input vectors A and B, scaled by their associated factors.
    This only works for 2D vectors. If higher dimensional vectors are
    passed, only the first two components are shown.
    """
    scalar_a, scalar_b = inputs["a"]["s"], inputs["b"]["s"]
    vec_a = scalar_a * np.array(inputs["a"]["v"][:2])
    vec_b = scalar_b * np.array(inputs["b"]["v"][:2])
    result = outputs["vector_add"]["result"]

    fig = go.Figure()

    # Vector A: from origin to A
    fig.add_trace(
        go.Scatter(
            x=[0, vec_a[0]],
            y=[0, vec_a[1]],
            mode="lines+markers+text",
            name="Vector A",
            text=["", "A"],
            textposition="top center",
        )
    )

    # Vector B: from tip of A to A + B
    fig.add_trace(
        go.Scatter(
            x=[vec_a[0], vec_a[0] + vec_b[0]],
            y=[vec_a[1], vec_a[1] + vec_b[1]],
            mode="lines+markers+text",
            name="Vector B",
            text=["", "B"],
            textposition="top center",
        )
    )

    # Resultant vector: from origin to A + B
    fig.add_trace(
        go.Scatter(
            x=[0, result[0]],
            y=[0, result[1]],
            mode="lines+markers+text",
            name="A + B",
            line={"dash": "dash", "color": "green"},
            text=["", "A + B"],
            textposition="top center",
        )
    )

    fig.update_layout(
        title="Vector Addition (Triangle Method)",
        xaxis={"title": "X", "zeroline": True},
        yaxis={"title": "Y", "zeroline": True},
        showlegend=True,
        width=600,
        height=600,
    )

    return fig
