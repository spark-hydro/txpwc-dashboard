"""The Model Performance map: subbasins plus the clickable observation points.

Each layer is one named trace, so the legend hides/shows it instantly and a
click can be routed back to its dataset by trace position (see layer_order).
A "highlight" trace sits under the points and rings whatever is currently
selected, so the map always shows which point the charts below are drawing.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.plotting.maps import plot_subbasins_map

STREAMFLOW_COLOR = "#0369a1"
EXTRA_STREAMFLOW_COLOR = "#38bdf8"
RESERVOIR_COLOR = "#f59e0b"
SALINITY_COLOR = "#b45309"


def _highlight_trace(points: list[tuple[float, float]]) -> go.Scattermap:
    lat = [p[0] for p in points]
    lon = [p[1] for p in points]
    return go.Scattermap(
        lat=lat, lon=lon, mode="markers",
        marker=dict(size=26, color="#111827", opacity=0.30),
        hoverinfo="skip", showlegend=False, name="selected",
    )


def plot_observation_map(
    subbasins_geojson: dict,
    color_field: str | None,
    *,
    gauges: pd.DataFrame | None = None,
    reservoirs: pd.DataFrame | None = None,
    wells: pd.DataFrame | None = None,
    salinity_stations: pd.DataFrame | None = None,
    selected_gauge: str | None = None,
    selected_well: str | None = None,
    selected_salinity: str | None = None,
    selected_subbasin: int | None = None,
) -> tuple[go.Figure, list[str]]:
    """Returns (fig, layer_order); layer_order[i] names the layer of trace i."""
    fig = plot_subbasins_map(subbasins_geojson, color_field=color_field)
    layer_order = ["subbasins"]

    ring: list[tuple[float, float]] = []
    if gauges is not None and selected_gauge is not None:
        row = gauges[gauges["id"] == selected_gauge]
        ring += [(r.lat, r.lon) for r in row.itertuples()]
    if reservoirs is not None and selected_gauge is not None:
        row = reservoirs[reservoirs["flow_gage_id"] == selected_gauge]
        ring += [(r.lat, r.lon) for r in row.itertuples()]
    if wells is not None and selected_well is not None:
        row = wells[wells["id"] == selected_well]
        ring += [(r.lat, r.lon) for r in row.itertuples()]
    if salinity_stations is not None and selected_salinity is not None:
        row = salinity_stations[salinity_stations["site"] == selected_salinity]
        ring += [(r.lat, r.lon) for r in row.itertuples()]

    fig.add_trace(_highlight_trace(ring))
    layer_order.append("highlight")

    if gauges is not None and not gauges.empty:
        extra = gauges["group"].eq("extra") if "group" in gauges else pd.Series(False, index=gauges.index)
        fig.add_trace(go.Scattermap(
            lat=gauges["lat"], lon=gauges["lon"], mode="markers",
            marker=dict(size=np.where(extra, 8, 12), color=np.where(extra, EXTRA_STREAMFLOW_COLOR, STREAMFLOW_COLOR)),
            text=[f"{lbl}<br>USGS {i}" for lbl, i in zip(gauges["label"], gauges["id"])],
            hovertemplate="%{text}<extra></extra>", name="Streamflow stations",
        ))
        layer_order.append("streamflow")

    if reservoirs is not None and not reservoirs.empty:
        fig.add_trace(go.Scattermap(
            lat=reservoirs["lat"], lon=reservoirs["lon"], mode="markers+text",
            marker=dict(size=17, color=RESERVOIR_COLOR),
            text=reservoirs["name"], textposition="top center", textfont=dict(size=11),
            hovertemplate="%{text}<extra></extra>", name="Reservoirs",
        ))
        layer_order.append("reservoirs")

    if wells is not None and not wells.empty:
        bias = wells["mean_bias_m"]
        fig.add_trace(go.Scattermap(
            lat=wells["lat"], lon=wells["lon"], mode="markers",
            marker=dict(
                size=6 + np.minimum(10, bias.abs() / 5), color=bias, colorscale="RdBu",
                cmin=-60, cmax=60, showscale=True,
                colorbar=dict(title="Sim − obs (m)", x=1.15),
            ),
            text=[
                f"Well {i}<br>Mean bias (sim − obs): {b:+.1f} m<br>{n} well-years"
                for i, b, n in zip(wells["id"], bias, wells["n_years"])
            ],
            hovertemplate="%{text}<extra></extra>", name="Groundwater wells",
        ))
        layer_order.append("wells")

    if salinity_stations is not None and not salinity_stations.empty:
        fig.add_trace(go.Scattermap(
            lat=salinity_stations["lat"], lon=salinity_stations["lon"], mode="markers",
            marker=dict(size=13, color=SALINITY_COLOR),
            text=[f"{s}<br>USGS {i}" for s, i in zip(salinity_stations["station"], salinity_stations["site"])],
            hovertemplate="%{text}<extra></extra>", name="Salinity stations",
        ))
        layer_order.append("salinity")

    # Outline of the picked subbasin. Always the last trace (empty when nothing is
    # picked) so the trace order -- and with it click routing -- never changes.
    chosen = [f for f in subbasins_geojson.get("features", []) if f["properties"].get("Subbasin") == selected_subbasin]
    fig.add_trace(go.Choroplethmap(
        geojson={"type": "FeatureCollection", "features": chosen},
        locations=[selected_subbasin] if chosen else [], z=[1] if chosen else [],
        featureidkey="properties.Subbasin",
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
        marker=dict(line=dict(color="#111827", width=3)),
        hoverinfo="skip", showlegend=False, name="selected subbasin",
    ))
    layer_order.append("subbasin_outline")

    fig.update_layout(
        height=560,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig, layer_order
