from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def plot_et_grid_distribution(
    et_grid: pd.DataFrame,
    highlight_aet: float | None = None,
    compact: bool = False,
) -> go.Figure:
    """Histogram of mean annual actual ET across the basin's 6,300 grid cells.

    Each cell is a 2000-2020 annual normal (TerraClimate), not a time series
    -- pass ``highlight_aet`` (one clicked cell's value) to mark where it
    falls in the basin-wide spread.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=et_grid["aet_mm_yr"],
            nbinsx=40,
            marker_color="#0e7490",
        )
    )

    fig.update_layout(
        title="" if compact else "Distribution of Mean Actual ET Across Grid Cells",
        xaxis_title="Actual ET (mm/yr)",
        yaxis_title="Number of grid cells",
        template="plotly_white",
        margin=dict(l=20, r=20, t=10 if compact else 60, b=20),
        bargap=0.05,
        height=220 if compact else None,
        showlegend=False,
    )

    if highlight_aet is not None:
        fig.add_vline(
            x=highlight_aet,
            line_color="#dc2626",
            line_width=3,
            annotation_text="This cell" if compact else f"This cell: {highlight_aet:,.0f} mm/yr",
            annotation_position="top",
        )

    return fig


def plot_et_water_balance(df: pd.DataFrame) -> go.Figure:
    """Monthly basin-average precipitation, potential ET, and actual ET (2000-2020)."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df["ppt_mm"],
            mode="lines", name="Precipitation",
            line=dict(color="#4cc9f0"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df["pet_mm"],
            mode="lines", name="Potential ET",
            line=dict(color="#f4a261", dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df["aet_mm"],
            mode="lines", name="Actual ET",
            line=dict(color="#0e7490", width=2),
            fill="tozeroy",
            fillcolor="rgba(14,116,144,0.15)",
        )
    )

    fig.update_layout(
        title="Basin Water Balance — TerraClimate, 2000–2020",
        xaxis_title="Month",
        yaxis_title="mm / month",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
