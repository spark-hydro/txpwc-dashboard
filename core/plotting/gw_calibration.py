from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def plot_gw_obs_vs_sim_scatter(pairs: pd.DataFrame) -> go.Figure:
    """Observed against simulated depth to water table, every well-year."""
    fig = go.Figure()

    if pairs.empty:
        return fig

    lo = min(pairs["obs_depth_m"].min(), pairs["sim_depth_m"].min())
    hi = max(pairs["obs_depth_m"].max(), pairs["sim_depth_m"].max())
    lo = np.floor(lo / 10) * 10
    hi = np.ceil(hi / 10) * 10

    fig.add_trace(
        go.Scatter(
            x=[lo, hi], y=[lo, hi],
            mode="lines", name="1:1",
            line=dict(color="#94a3b8", dash="dash", width=1),
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=pairs["obs_depth_m"], y=pairs["sim_depth_m"],
            mode="markers", name="Well-year",
            marker=dict(size=6, color="#0e7490", opacity=0.7),
            text=[f"{wid} ({y})" for wid, y in zip(pairs["id"], pairs["year"])],
            hovertemplate="%{text}<br>Observed: %{x:.0f} m<br>Simulated: %{y:.0f} m<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis=dict(title="Depth to water table, observed (m bgs)", range=[lo, hi]),
        yaxis=dict(title="Depth to water table, simulated (m bgs)", range=[lo, hi]),
        template="plotly_white",
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def plot_gw_well_timeseries(well_pairs: pd.DataFrame, well_label: str) -> go.Figure:
    """One well's observed and simulated depth to water table, through time."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=well_pairs["year"], y=well_pairs["obs_depth_m"],
            mode="markers", name="Observed",
            marker=dict(size=8, color="#111827"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=well_pairs["year"], y=well_pairs["sim_depth_m"],
            mode="lines+markers", name="Simulated",
            line=dict(color="#0e7490", width=2),
            marker=dict(size=5),
        )
    )

    fig.update_layout(
        title=f"{well_label} — Depth to Water Table",
        xaxis_title="Year",
        # Reversed: 0 (surface) at top, depth increasing downward.
        yaxis=dict(title="Depth to water table (m bgs)", autorange="reversed"),
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
