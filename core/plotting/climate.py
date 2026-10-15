from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def plot_et_spatial_map(df: pd.DataFrame, column: str, title: str, diverging: bool = False, shared_cmax: float | None = None, diverging_bound: float | None = None) -> go.Figure:
    """One 0.1-deg ET grid as colored points: model, a product, or their difference.

    Pass ``shared_cmax`` (the max of both the model and the product) so the
    two non-diverging maps share one color scale -- otherwise each map
    scales to its own max and a visually "deeper green" cell can actually
    be the lower value.
    """
    fig = go.Figure()
    vals = df[column]

    if diverging:
        bound = diverging_bound if diverging_bound is not None else max(abs(vals.min()), abs(vals.max()), 1)
        colorscale, cmin, cmax = "RdYlGn", -bound, bound
    else:
        colorscale, cmin, cmax = "YlGn", 0, shared_cmax if shared_cmax is not None else vals.max()

    fig.add_trace(
        go.Scattermap(
            lat=df["lat"], lon=df["lon"],
            mode="markers",
            marker=dict(size=9, color=vals, colorscale=colorscale, cmin=cmin, cmax=cmax, showscale=True,
                        colorbar=dict(title="mm/yr")),
            text=[f"{title}: {v:,.0f} mm/yr" for v in vals],
            hovertemplate="%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        map_style="open-street-map",
        map_center={"lat": df["lat"].mean(), "lon": df["lon"].mean()},
        map_zoom=4.85,
        margin=dict(l=0, r=0, t=30, b=0),
        height=380,
        title=title,
    )
    return fig


def compute_et_spatial_stats(model: pd.Series, product: pd.Series) -> dict | None:
    """Spatial goodness-of-fit: every grid cell pair is one sample (not a time series)."""
    pairs = pd.DataFrame({"m": model, "p": product}).dropna()
    if len(pairs) < 5:
        return None
    m, p = pairs["m"].to_numpy(dtype=float), pairs["p"].to_numpy(dtype=float)
    mp = p.mean()
    nse = 1 - np.sum((m - p) ** 2) / np.sum((p - mp) ** 2)
    pbias = 100 * (m.sum() - p.sum()) / p.sum()
    r = np.corrcoef(m, p)[0, 1]
    r2 = r ** 2
    rmse = np.sqrt(np.mean((m - p) ** 2))
    alpha, beta = m.std() / p.std(), m.mean() / p.mean()
    kge = 1 - np.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2)
    return {"nse": nse, "kge": kge, "pbias": pbias, "r2": r2, "rmse": rmse, "n": len(pairs)}


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


def plot_et_region_monthly(monthly: pd.DataFrame, start_year: int = 2010) -> go.Figure:
    """Monthly regional ET from the two remote-sensing products (observed style)."""
    from core.plotting.style import obs_marker

    sub = monthly[monthly["date"].dt.year >= start_year].sort_values("date")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sub["date"], y=sub["ssebop_aet_mm"], mode="markers", name="SSEBop",
            marker=obs_marker(6),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=sub["date"], y=sub["terraclimate_aet_mm"], mode="markers", name="TerraClimate",
            marker=obs_marker(6, symbol="diamond"),
        )
    )
    fig.update_layout(
        yaxis_title="Actual ET (mm/month)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_et_region_annual(annual: pd.DataFrame, start_year: int = 2010) -> go.Figure:
    """Annual regional ET: both products (observed style) against the model runs."""
    from core.plotting.style import obs_marker, sim_color

    sub = annual[annual["year"] >= start_year].sort_values("year")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub["year"], y=sub["ssebop_mm"], mode="markers", name="SSEBop", marker=obs_marker(9)))
    fig.add_trace(go.Scatter(x=sub["year"], y=sub["terraclimate_mm"], mode="markers", name="TerraClimate",
                             marker=obs_marker(9, symbol="diamond")))
    runs = [
        ("model_v52prod_mm", "Model — production run"),
        ("model_v33_mm", "Model — improved channel geometry"),
        ("model_v30ext_mm", "Model — base run"),
    ]
    for i, (col, label) in enumerate(runs):
        if col in sub.columns and sub[col].notna().any():
            fig.add_trace(go.Scatter(x=sub["year"], y=sub[col], mode="lines+markers", name=label,
                                     line=dict(color=sim_color(i), width=2), marker=dict(size=5)))
    fig.update_layout(
        yaxis_title="Actual ET (mm/yr)",
        xaxis=dict(dtick=2),
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
