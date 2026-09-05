from __future__ import annotations

import plotly.graph_objects as go
import pandas as pd


def plot_well_timeseries(df: pd.DataFrame, well_label: str) -> go.Figure:
    """Real observed head (m AMSL) at one USGS/TWDB monitoring well."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df["head_m"],
            mode="lines+markers",
            name="Observed head",
            line=dict(color="#22d3ee"),
            marker=dict(size=4),
        )
    )

    fig.update_layout(
        title=f"{well_label} — Observed Head",
        xaxis_title="Date",
        yaxis_title="Head (m AMSL)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def plot_groundwater_scatter(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    if {"observed", "simulated"}.issubset(df.columns):
        fig.add_trace(
            go.Scatter(
                x=df["observed"],
                y=df["simulated"],
                mode="markers",
                text=df["site_id"] if "site_id" in df.columns else None,
                name="Groundwater sites",
            )
        )

        min_val = min(df["observed"].min(), df["simulated"].min())
        max_val = max(df["observed"].max(), df["simulated"].max())
        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode="lines",
                name="1:1 line",
            )
        )

    fig.update_layout(
        title="Groundwater Observed vs Simulated",
        xaxis_title="Observed",
        yaxis_title="Simulated",
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig
