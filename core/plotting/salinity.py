from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def plot_salinity_sites_map(sites: pd.DataFrame) -> go.Figure:
    """4,283 real TDS/salinity sampling sites, colored by mean TDS (log scale)."""
    fig = go.Figure()

    if sites.empty:
        fig.update_layout(mapbox_style="open-street-map", height=480)
        return fig

    with_tds = sites[sites["tds_mean"].notna()].copy()
    no_tds = sites[sites["tds_mean"].isna()]

    if not no_tds.empty:
        fig.add_trace(
            go.Scattermapbox(
                lat=no_tds["lat"], lon=no_tds["lon"],
                mode="markers",
                marker=dict(size=5, color="#94a3b8", opacity=0.5),
                text=no_tds["desc"],
                name="No direct TDS reading",
                hovertemplate="%{text}<br>Conductance/ion samples only<extra></extra>",
            )
        )

    if not with_tds.empty:
        log_tds = np.log10(with_tds["tds_mean"].clip(lower=1))
        fig.add_trace(
            go.Scattermapbox(
                lat=with_tds["lat"], lon=with_tds["lon"],
                mode="markers",
                marker=dict(
                    size=7,
                    color=log_tds,
                    colorscale="YlOrRd",
                    cmin=1, cmax=5.3,  # 10 to ~200,000 mg/L
                    showscale=True,
                    colorbar=dict(
                        title="TDS (mg/L)",
                        tickvals=[1, 2, 3, 4, 5],
                        ticktext=["10", "100", "1,000", "10,000", "100,000"],
                    ),
                ),
                text=[
                    f"{d}<br>Mean TDS: {t:,.0f} mg/L ({n} samples)"
                    for d, t, n in zip(with_tds["desc"], with_tds["tds_mean"], with_tds["n_tds"])
                ],
                name="TDS observed",
                hovertemplate="%{text}<extra></extra>",
            )
        )

    center_lat = sites["lat"].mean()
    center_lon = sites["lon"].mean()
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": center_lat, "lon": center_lon},
        mapbox_zoom=6,
        margin=dict(l=10, r=10, t=10, b=10),
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def plot_tds_distribution(sites: pd.DataFrame) -> go.Figure:
    """Histogram of mean TDS across all sites with a direct reading, log-x."""
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
        title="Distribution of Mean TDS Across Sampling Sites",
        xaxis=dict(
            title="TDS (mg/L, log scale)",
            tickvals=[1, 2, 3, 4, 5],
            ticktext=["10", "100", "1,000", "10,000", "100,000"],
        ),
        yaxis_title="Number of sites",
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
        bargap=0.05,
    )
    # Freshwater / brackish / saline reference lines (USGS classification)
    for x, label in [(np.log10(1000), "1,000 (fresh limit)"), (np.log10(10000), "10,000 (saline)")]:
        fig.add_vline(x=x, line_dash="dot", line_color="#94a3b8")
        fig.add_annotation(x=x, y=1, yref="paper", text=label, showarrow=False, yshift=10, font=dict(size=10))

    return fig
