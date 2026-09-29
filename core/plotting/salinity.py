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
