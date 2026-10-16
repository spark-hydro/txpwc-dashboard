from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def plot_et_spatial_map(df: pd.DataFrame, column: str, title: str, diverging: bool = False, shared_cmax: float | None = None, diverging_bound: float | None = None, unit: str = "mm/yr") -> go.Figure:
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
                        colorbar=dict(title=unit)),
            text=[f"{title}: {v:,.0f} {unit}" for v in vals],
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
    """Monthly regional ET: the two remote-sensing products (observed style) and,
    when present, the production run's monthly output (simulated style)."""
    from core.plotting.style import obs_marker, sim_color

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
    if "model_v52prod_aet_mm" in sub.columns and sub["model_v52prod_aet_mm"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=sub["date"], y=sub["model_v52prod_aet_mm"], mode="lines", name="Model — production run",
                line=dict(color=sim_color(0), width=2),
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


def plot_et_animation(
    lat: np.ndarray,
    lon: np.ndarray,
    labels: list[str],
    model: list[np.ndarray],
    product: list[np.ndarray],
    product_label: str,
    unit: str,
    slider_ticks: list[str] | None = None,
) -> go.Figure:
    """Model ET, a product's ET and their difference as three synchronized maps
    animated through every time step.

    All frames travel to the browser once, so stepping or playing only swaps the
    point colours client-side -- nothing is re-sent or re-drawn by the server. One
    slider and one Play/Pause control drive the three maps together, and each frame
    also carries its own titles and spatial skill metrics.
    """
    from plotly.subplots import make_subplots

    diff = [m - p for m, p in zip(model, product)]
    cmax = float(max(np.nanmax(a) for a in model + product))
    dbound = float(max(np.nanmax(np.abs(d)) for d in diff))
    lat, lon = np.asarray(lat), np.asarray(lon)

    def as_ints(a: np.ndarray) -> list:
        return [None if not np.isfinite(v) else int(round(v)) for v in a]

    def annotations(i: int) -> list[dict]:
        stats = compute_et_spatial_stats(pd.Series(model[i]), pd.Series(product[i]))
        skill = (
            f"PBIAS {stats['pbias']:.1f}%   ·   R² {stats['r2']:.2f}   ·   RMSE {stats['rmse']:.1f} mm   ·   n = {stats['n']:,} cells"
            if stats else ""
        )
        titles = [f"Model ET — {labels[i]}", f"{product_label} ET — {labels[i]}", f"Model − {product_label} — {labels[i]}"]
        out = [
            dict(text=t, x=x, y=1.0, xref="paper", yref="paper", xanchor="center", yanchor="bottom", showarrow=False,
                 font=dict(size=14))
            for t, x in zip(titles, (0.165, 0.5, 0.835))
        ]
        out.append(dict(text=skill, x=0.5, y=-0.30, xref="paper", yref="paper", xanchor="center", yanchor="top",
                        showarrow=False, font=dict(size=13, color="#374151")))
        return out

    fig = make_subplots(rows=1, cols=3, specs=[[{"type": "map"}] * 3], horizontal_spacing=0.01)
    specs = [
        (model[0], "YlGn", 0, cmax, "Model: %{marker.color:,.0f} " + unit, "ModelBar"),
        (product[0], "YlGn", 0, cmax, product_label + ": %{marker.color:,.0f} " + unit, "ProdBar"),
        (diff[0], "RdYlGn", -dbound, dbound, "Model − " + product_label + ": %{marker.color:+,.0f} " + unit, "DiffBar"),
    ]
    for k, (vals, scale, lo, hi, hover, _) in enumerate(specs):
        fig.add_trace(
            go.Scattermap(
                lat=lat, lon=lon, mode="markers",
                marker=dict(
                    size=9, color=as_ints(vals), colorscale=scale, cmin=lo, cmax=hi, showscale=True,
                    colorbar=dict(orientation="h", thickness=9, len=0.3, x=(0.165, 0.5, 0.835)[k], y=-0.08,
                                  title=dict(text=unit, side="right")),
                ),
                hovertemplate=hover + "<extra></extra>",
            ),
            row=1, col=k + 1,
        )

    frames = [
        go.Frame(
            name=labels[i], traces=[0, 1, 2],
            data=[go.Scattermap(marker=dict(color=as_ints(a[i]))) for a in (model, product, diff)],
            layout=dict(annotations=annotations(i)),
        )
        for i in range(len(labels))
    ]
    fig.frames = frames

    def play_args(ms: int) -> list:
        return [None, dict(frame=dict(duration=ms, redraw=True), fromcurrent=True, transition=dict(duration=0), mode="immediate")]

    ticks = slider_ticks or labels
    center = {"lat": float(lat.mean()), "lon": float(lon.mean())}
    fig.update_layout(
        annotations=annotations(0),
        height=600,
        margin=dict(l=0, r=0, t=40, b=170),
        updatemenus=[dict(
            type="buttons", direction="left", x=0.0, y=-0.17, xanchor="left", yanchor="top", showactive=False,
            buttons=[
                dict(label="▶ Play", method="animate", args=play_args(700)),
                dict(label="▶ Slow", method="animate", args=play_args(1500)),
                dict(label="▶▶ Fast", method="animate", args=play_args(250)),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            active=0, x=0.30, y=-0.15, len=0.70, xanchor="left", yanchor="top",
            currentvalue=dict(visible=False), pad=dict(t=0, b=0), ticklen=0, minorticklen=0,
            font=dict(size=11, color="#6b7280"),
            steps=[
                dict(method="animate", label=ticks[i],
                     args=[[labels[i]], dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))])
                for i in range(len(labels))
            ],
        )],
    )
    for name in ("map", "map2", "map3"):
        fig.update_layout(**{name: dict(style="open-street-map", center=center, zoom=4.85)})
    return fig
