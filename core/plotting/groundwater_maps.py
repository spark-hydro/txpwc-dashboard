"""Three synchronized, animated maps: salinity, recharge and depth to the water table.

Like the ET maps, every frame travels to the browser once, so stepping or playing only swaps colours
client-side. Salinity layers two things on one map -- soil salt (grid cells) and river salinity (reaches);
the water-table map carries the groundwater-river exchange on top of the depth cells.
"""

from __future__ import annotations

import numpy as np
import plotly.colors as pc
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PANEL_X = (0.165, 0.5, 0.835)


def _sample(scale, pos: float) -> str:
    return pc.sample_colorscale(scale, [pos])[0]


def _transparent_low(scale, frac: float = 0.004):
    """Values at the very bottom of the range (used for 'no data') are drawn transparent."""
    pts = list(np.linspace(frac, 1, 11))
    out = [[0.0, "rgba(0,0,0,0)"], [frac, "rgba(0,0,0,0)"]]
    out += [[float(p) if i else frac + 1e-4, _sample(scale, float(p))] for i, p in enumerate(pts)]
    out[-1][0] = 1.0
    return out


def _transparent_middle(scale, lo: float = 0.49, hi: float = 0.51):
    """Near-zero values in a diverging scale are drawn transparent."""
    left = [(float(p), _sample(scale, float(p))) for p in np.linspace(0, lo, 6)]
    right = [(float(p), _sample(scale, float(p))) for p in np.linspace(hi, 1, 6)]
    out = [[p, c] for p, c in left[:-1]] + [[lo - 1e-4, left[-1][1]], [lo, "rgba(0,0,0,0)"], [hi, "rgba(0,0,0,0)"],
                                            [hi + 1e-4, right[0][1]]] + [[p, c] for p, c in right[1:]]
    out[0][0] = 0.0
    out[-1][0] = 1.0
    return out


def _ints(a: np.ndarray, decimals: int = 0) -> list:
    return [None if not np.isfinite(v) else (int(round(v)) if decimals == 0 else round(float(v), decimals)) for v in a]


def plot_groundwater_animation(
    cells_lat, cells_lon, reach_lat, reach_lon, labels, ticks, unit_time,
    soil, river, recharge, depth, exchange,
    caps: dict,
) -> go.Figure:
    """soil/river/recharge/depth/exchange: one array per frame (cells, or reaches for `river`).

    `unit_time` is 'mm/month' or 'mm/yr' (recharge). `caps` sets the colour ranges.
    """
    n = len(labels)
    soil_scale = _transparent_low(pc.get_colorscale("YlOrBr"))
    river_scale = _transparent_low(pc.get_colorscale("Plasma"))
    rech_scale = pc.get_colorscale("Blues")
    depth_scale = _transparent_low([[0.0, "#2c7fb8"], [0.5, "#f7f4ec"], [1.0, "#8c510a"]])  # 0 m = no data
    exch_scale = _transparent_middle(pc.get_colorscale("RdBu"))

    def summary(i: int) -> str:
        r = river[i]
        parts = [
            f"Recharge {np.nanmean(recharge[i]):.2f} {unit_time}",
            f"Depth to water table {np.nanmedian(depth[i]):.0f} m (median)",
            f"River salinity {np.nanmedian(r[r > 0]):,.0f} mg/L (median, flowing reaches)" if np.any(r > 0) else "River salinity —",
            f"Net exchange {np.nansum(exchange[i]):+.1f} m³/s to the river",
        ]
        return "   ·   ".join(parts)

    def annotations(i: int) -> list[dict]:
        titles = [f"Salinity — {labels[i]}", f"Recharge — {labels[i]}", f"Depth to water table — {labels[i]}"]
        out = [dict(text=t, x=x, y=1.0, xref="paper", yref="paper", xanchor="center", yanchor="bottom",
                    showarrow=False, font=dict(size=14)) for t, x in zip(titles, PANEL_X)]
        out.append(dict(text=summary(i), x=0.5, y=-0.50, xref="paper", yref="paper", xanchor="center", yanchor="top",
                        showarrow=False, font=dict(size=13, color="#374151")))
        return out

    def bar(x, y, title):
        return dict(orientation="h", thickness=9, len=0.3, x=x, y=y, yanchor="top", title=dict(text=title, side="right"))

    soil0 = np.nan_to_num(soil[0], nan=0.0)
    river0 = np.nan_to_num(river[0], nan=0.0)
    ex0 = np.nan_to_num(exchange[0], nan=0.0)
    rech0 = np.nan_to_num(recharge[0], nan=0.0)
    depth0 = np.nan_to_num(depth[0], nan=0.0)
    fig = make_subplots(rows=1, cols=3, specs=[[{"type": "map"}] * 3], horizontal_spacing=0.01)
    # 0: soil salt (cells)   1: river salinity (reaches)   -> panel 1
    fig.add_trace(go.Scattermap(
        lat=cells_lat, lon=cells_lon, mode="markers", name="Soil salt (kg/ha)",
        marker=dict(size=9, color=_ints(soil0), colorscale=soil_scale, cmin=0, cmax=caps["soil"], showscale=True,
                    colorbar=bar(PANEL_X[0], -0.03, "kg/ha soil")),
        hovertemplate="Soil salt: %{marker.color:,.0f} kg/ha<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scattermap(
        lat=reach_lat, lon=reach_lon, mode="markers", name="River salinity (mg/L)",
        marker=dict(size=5, color=_ints(river0), colorscale=river_scale, cmin=0, cmax=caps["river"], showscale=True,
                    colorbar=bar(PANEL_X[0], -0.13, "mg/L river")),
        hovertemplate="River salinity: %{marker.color:,.0f} mg/L<extra></extra>"), row=1, col=1)
    # 2: recharge -> panel 2
    fig.add_trace(go.Scattermap(
        lat=cells_lat, lon=cells_lon, mode="markers", name="Recharge",
        marker=dict(size=9, color=_ints(rech0, 2), colorscale=rech_scale, cmin=0, cmax=caps["recharge"], showscale=True,
                    colorbar=bar(PANEL_X[1], -0.03, unit_time)),
        hovertemplate="Recharge: %{marker.color:,.2f} " + unit_time + "<extra></extra>"), row=1, col=2)
    # 3: depth to the water table, 4: exchange on top -> panel 3
    fig.add_trace(go.Scattermap(
        lat=cells_lat, lon=cells_lon, mode="markers", name="Depth to water table",
        marker=dict(size=9, color=_ints(depth0), colorscale=depth_scale, cmin=0, cmax=caps["depth"], showscale=True,
                    colorbar=bar(PANEL_X[2], -0.03, "m deep")),
        hovertemplate="Depth to water table: %{marker.color:,.0f} m<extra></extra>"), row=1, col=3)
    fig.add_trace(go.Scattermap(
        lat=cells_lat, lon=cells_lon, mode="markers", name="River–aquifer exchange (m³/s)",
        marker=dict(size=6, color=_ints(ex0, 3), colorscale=exch_scale, cmin=-caps["exchange"], cmax=caps["exchange"],
                    showscale=True, colorbar=bar(PANEL_X[2], -0.13, "m³/s to river")),
        hovertemplate="Exchange: %{marker.color:+,.3f} m³/s (+ aquifer feeds the river, − river loses water)<extra></extra>"),
        row=1, col=3)

    fig.frames = [
        go.Frame(
            name=labels[i], traces=[0, 1, 2, 3, 4],
            data=[
                go.Scattermap(marker=dict(color=_ints(np.nan_to_num(soil[i], nan=0.0)))),
                go.Scattermap(marker=dict(color=_ints(np.nan_to_num(river[i], nan=0.0)))),
                go.Scattermap(marker=dict(color=_ints(np.nan_to_num(recharge[i], nan=0.0), 2))),
                go.Scattermap(marker=dict(color=_ints(np.nan_to_num(depth[i], nan=0.0)))),
                go.Scattermap(marker=dict(color=_ints(np.nan_to_num(exchange[i], nan=0.0), 3))),
            ],
            layout=dict(annotations=annotations(i)),
        )
        for i in range(n)
    ]

    def play_args(ms: int) -> list:
        return [None, dict(frame=dict(duration=ms, redraw=True), fromcurrent=True, transition=dict(duration=0), mode="immediate")]

    center = {"lat": float((np.min(cells_lat) + np.max(cells_lat)) / 2), "lon": float((np.min(cells_lon) + np.max(cells_lon)) / 2)}
    fig.update_layout(
        annotations=annotations(0), height=780, margin=dict(l=0, r=0, t=70, b=300),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.07, xanchor="left", x=0, font=dict(size=11)),
        updatemenus=[dict(
            type="buttons", direction="left", x=0.0, y=-0.31, xanchor="left", yanchor="top", showactive=False,
            buttons=[
                dict(label="▶ Play", method="animate", args=play_args(700)),
                dict(label="▶ Slow", method="animate", args=play_args(1500)),
                dict(label="▶▶ Fast", method="animate", args=play_args(250)),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            active=0, x=0.30, y=-0.29, len=0.70, xanchor="left", yanchor="top",
            currentvalue=dict(visible=False), pad=dict(t=0, b=0), ticklen=0, minorticklen=0,
            font=dict(size=11, color="#6b7280"),
            steps=[
                dict(method="animate", label=ticks[i],
                     args=[[labels[i]], dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))])
                for i in range(n)
            ],
        )],
    )
    for name in ("map", "map2", "map3"):
        fig.update_layout(**{name: dict(style="open-street-map", center=center, zoom=5.15)})
    return fig
