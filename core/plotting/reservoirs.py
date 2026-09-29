from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_reservoir_timeseries(df: pd.DataFrame, dam_name: str) -> go.Figure:
    """Monthly release + storage for one dam, real 2000-2020 record."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df["release_Mm3"],
            mode="lines", name="Release (Mm³/mo)",
            line=dict(color="#0e7490"),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df["storage_af"],
            mode="lines", name="Storage (acre-ft)",
            line=dict(color="#f59e0b", dash="dot"),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=f"{dam_name} — Monthly Release &amp; Storage (2000–2020)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Release (Mm³/mo)", secondary_y=False)
    fig.update_yaxes(title_text="Storage (acre-ft)", secondary_y=True)
    fig.update_xaxes(title_text="Month")
    return fig
