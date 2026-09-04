from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


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
