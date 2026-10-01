from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def plot_tds_distribution(
    sites: pd.DataFrame,
    highlight_tds: float | None = None,
    compact: bool = False,
) -> go.Figure:
    """Histogram of mean TDS across all sites with a direct reading, log-x.

    Pass ``highlight_tds`` (one site's mean TDS) to draw a marker showing
    where that site falls in the basin-wide distribution -- used for the
    map's click panel, since individual sites have no time series of their
    own to chart. ``compact`` shrinks it for that same small panel.
    """
    fig = go.Figure()

    with_tds = sites[sites["tds_mean"].notna()]
    if with_tds.empty:
        return fig

    log_tds = np.log10(with_tds["tds_mean"].clip(lower=1))

    fig.add_trace(
        go.Histogram(
            x=log_tds,
            nbinsx=40,
            marker_color="#0e7490",
        )
    )

    fig.update_layout(
        title="" if compact else "Distribution of Mean TDS Across Sampling Sites",
        xaxis=dict(
            title="TDS (mg/L, log scale)",
            tickvals=[1, 2, 3, 4, 5],
            ticktext=["10", "100", "1,000", "10,000", "100,000"],
        ),
        yaxis_title="Number of sites",
        template="plotly_white",
        margin=dict(l=20, r=20, t=10 if compact else 60, b=20),
        bargap=0.05,
        height=220 if compact else None,
        showlegend=False,
    )
    # Freshwater / brackish / saline reference lines (USGS classification)
    for x, label in [(np.log10(1000), "1,000 (fresh limit)"), (np.log10(10000), "10,000 (saline)")]:
        fig.add_vline(x=x, line_dash="dot", line_color="#94a3b8")
        if not compact:
            fig.add_annotation(x=x, y=1, yref="paper", text=label, showarrow=False, yshift=10, font=dict(size=10))

    if highlight_tds is not None and highlight_tds > 0:
        fig.add_vline(
            x=np.log10(max(highlight_tds, 1)),
            line_color="#dc2626",
            line_width=3,
            annotation_text="This site" if compact else f"This site: {highlight_tds:,.0f} mg/L",
            annotation_position="top",
        )

    return fig


CONSTITUENT_LABELS = {"cl": "Chloride", "so4": "Sulfate", "tds": "TDS"}


def plot_station_obs_vs_sim(
    observed: pd.DataFrame,
    simulated: pd.DataFrame,
    site: str,
    constituent: str,
) -> go.Figure:
    """Real grab samples (points) against the model's annual flux-weighted
    concentration (line) at one real USGS gauge, log-y."""
    obs = observed[(observed["site"] == site) & (observed["constituent"] == constituent)].sort_values("date")
    sim = simulated[(simulated["site"] == site) & (simulated["constituent"] == constituent)].sort_values("year")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=obs["date"], y=obs["value_mgL"],
            mode="markers", name="Observed (Water Quality Portal)",
            marker=dict(size=6, color="#c0392b", opacity=0.75),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(sim["year"], format="%Y"), y=sim["value_mgL"],
            mode="markers", name="Simulated (annual flux-weighted)",
            marker=dict(size=7, color="#0e7490", symbol="diamond"),
        )
    )

    fig.update_layout(
        yaxis=dict(title=f"{CONSTITUENT_LABELS.get(constituent, constituent)} (mg/L, log scale)", type="log"),
        template="plotly_white",
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_source_contribution(contrib: dict) -> go.Figure:
    """Annual chloride load, groundwater export vs. the two mapped point sources."""
    labels = ["Groundwater (gwflow export)", "Malaga Bend brine (point source)", "Produced water (point source)"]
    values = [contrib["groundwater_t_yr"], contrib["malaga_t_yr"], contrib["prodwater_t_yr"]]
    colors = ["#0e7490", "#c0392b", "#b8862b"]

    fig = go.Figure(
        go.Bar(
            x=values, y=labels, orientation="h",
            marker_color=colors,
            text=[f"{v:,.0f} t/yr" for v in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        xaxis=dict(title="Mean annual chloride load (t/yr, log scale)", type="log"),
        template="plotly_white",
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        height=260,
    )
    return fig
