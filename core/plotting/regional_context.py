from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def plot_annual_flow_trend(df: pd.DataFrame) -> go.Figure:
    """Annual mean streamflow trend, e.g. USGS gauge 08446500 (Pecos River near Girvin, TX)."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["year"],
            y=df["mean_cfs"],
            mode="lines+markers",
            name="Annual mean flow",
            line=dict(color="#0e7490"),
            marker=dict(size=5),
        )
    )

    if len(df) >= 10:
        rolling = df.set_index("year")["mean_cfs"].rolling(10, min_periods=5).mean()
        fig.add_trace(
            go.Scatter(
                x=rolling.index,
                y=rolling.values,
                mode="lines",
                name="10-yr rolling mean",
                line=dict(color="#f59e0b", width=3, dash="dash"),
            )
        )

    fig.update_layout(
        title="Pecos River near Girvin, TX — Annual Mean Streamflow (USGS 08446500)",
        xaxis_title="Year",
        yaxis_title="Mean flow (cfs)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig
