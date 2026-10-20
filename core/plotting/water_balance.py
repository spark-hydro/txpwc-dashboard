from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_annual_water_balance(wb: pd.DataFrame) -> go.Figure:
    """Four stacked panels: precipitation, soil water, the generation/
    exchange terms that move water between land, stream and aquifer, and
    a relative groundwater storage trend -- one bar per year, 2000-2025.
    """
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        row_heights=[0.16, 0.16, 0.44, 0.24],
        vertical_spacing=0.03,
    )

    years = wb["yr"]

    # Panel 1: precipitation (reversed axis -- water "falling" from the top)
    fig.add_trace(
        go.Bar(x=years, y=wb["prec"], name="Precipitation", marker_color="#6a5acd"),
        row=1, col=1,
    )
    fig.update_yaxes(title_text="mm/yr", autorange="reversed", row=1, col=1)

    # Panel 2: soil water
    fig.add_trace(
        go.Bar(x=years, y=wb["sw"], name="Soil water", marker_color="#b7e0c4"),
        row=2, col=1,
    )
    fig.update_yaxes(title_text="mm", row=2, col=1)

    # Panel 3: surface/lateral/groundwater generation (up) vs. aquifer exchange (down)
    fig.add_trace(go.Bar(x=years, y=wb["surq"], name="Surface runoff", marker_color="#7bb08a", legendgroup="s", offsetgroup="s"), row=3, col=1)
    fig.add_trace(go.Bar(x=years, y=wb["latq"], name="Lateral flow", marker_color="#4a8f63", legendgroup="s", offsetgroup="s"), row=3, col=1)
    fig.add_trace(go.Bar(x=years, y=wb["gwq"], name="Groundwater discharge to stream", marker_color="#1c5f7a", legendgroup="s", offsetgroup="s"), row=3, col=1)
    fig.add_trace(go.Bar(x=years, y=-wb["swgw"], name="Stream seepage to aquifer", marker_color="#3d7fb0", legendgroup="s", offsetgroup="s"), row=3, col=1)
    fig.add_trace(go.Bar(x=years, y=-wb["perco"], name="Recharge to water table", marker_color="#0f8fb4", legendgroup="s", offsetgroup="s"), row=3, col=1)
    fig.update_yaxes(title_text="mm/yr", row=3, col=1)

    # Panel 4: relative groundwater storage trend (reversed axis, cumulative line)
    fig.add_trace(
        go.Scatter(x=years, y=wb["gw"], name="Relative groundwater storage", mode="lines+markers",
                   line=dict(color="#6b93a8", width=1.8), marker=dict(size=4)),
        row=4, col=1,
    )
    fig.update_yaxes(title_text="mm (cum.)", autorange="reversed", row=4, col=1)

    fig.update_layout(
        barmode="relative",
        template="plotly_white",
        height=760,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=20, b=140),
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.13,
            xanchor="center", x=0.5,
            font=dict(size=11),
        ),
    )
    fig.update_xaxes(title_text="Year", row=4, col=1)
    return fig


def plot_gw_sw_interaction(wb: pd.DataFrame) -> go.Figure:
    """Groundwater discharge to streams (up), stream seepage to the aquifer
    (down), and the net exchange -- one bar per year."""
    from core.plotting.style import sim_color

    net = wb["gwq"] - wb["swgw"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=wb["yr"], y=wb["gwq"], name="Groundwater → stream", marker_color=sim_color(0)))
    fig.add_trace(go.Bar(x=wb["yr"], y=-wb["swgw"], name="Stream → aquifer", marker_color=sim_color(1)))
    fig.add_trace(
        go.Scatter(x=wb["yr"], y=net, name="Net exchange (to stream)", mode="lines+markers",
                   line=dict(color=sim_color(2), width=2), marker=dict(size=5))
    )
    fig.update_layout(
        barmode="relative",
        yaxis_title="mm/yr over the basin",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=70, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
