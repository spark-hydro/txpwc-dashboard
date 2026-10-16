"""The Model Performance map: subbasins plus the clickable observation points.

Each layer is one named trace, so the legend hides/shows it instantly and a
click can be routed back to its dataset by trace position (see layer_order).
A "highlight" trace sits under the points and rings whatever is currently
selected, so the map always shows which point the charts below are drawing.

Every point layer is drawn twice -- a white halo, then the coloured dot -- so
the points stay readable over any subbasin colour. The map basemap has no
icon sprites, so categories are told apart by colour and size, not by shape.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.plotting.maps import plot_subbasins_map

STREAMFLOW_COLOR = "#1d4ed8"
EXTRA_STREAMFLOW_COLOR = "#60a5fa"
RESERVOIR_COLOR = "#ea580c"
SALINITY_COLOR = "#7e22ce"
HALO_COLOR = "#ffffff"

# Pale terrain tones: the subbasins read as a backdrop, not as data competing
# with the points drawn on top of them.
SUBBASIN_COLORSCALE = [[0.0, "#f7f4ec"], [0.5, "#e2d9c3"], [1.0, "#b9a982"]]

POINT_LAYERS = ["streamflow", "reservoirs", "wells", "salinity"]


def expected_layer_order(enabled: set[str]) -> list[str]:
    """Trace order the map is built with, so a click's curve number can be
    checked against it before the figure exists."""
    order = ["subbasins", "highlight"]
    for key in POINT_LAYERS:
        if key in enabled:
            order += [f"{key}_halo", key]
    return order + ["subbasin_outline"]


def _highlight_trace(points: list[tuple[float, float]]) -> go.Scattermap:
    lat = [p[0] for p in points]
    lon = [p[1] for p in points]
    return go.Scattermap(
        lat=lat, lon=lon, mode="markers",
        marker=dict(size=30, color="#111827", opacity=0.30),
        hoverinfo="skip", showlegend=False, name="selected",
    )


def _halo(lat, lon, size) -> go.Scattermap:
    return go.Scattermap(
        lat=lat, lon=lon, mode="markers",
        marker=dict(size=size, color=HALO_COLOR, opacity=0.95),
        hoverinfo="skip", showlegend=False, name="halo",
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
    fig = plot_subbasins_map(
        subbasins_geojson, color_field=color_field,
        colorscale=SUBBASIN_COLORSCALE, opacity=0.75, line_color="#8b8578",
        colorbar=dict(thickness=10, len=0.4, y=0.78, x=1.02, yanchor="middle"),
    )
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
        size = np.where(extra, 9, 14)
        fig.add_trace(_halo(gauges["lat"], gauges["lon"], size + 5))
        layer_order.append("streamflow_halo")
        fig.add_trace(go.Scattermap(
            lat=gauges["lat"], lon=gauges["lon"], mode="markers",
            marker=dict(size=size, color=np.where(extra, EXTRA_STREAMFLOW_COLOR, STREAMFLOW_COLOR)),
            text=[f"{lbl}<br>USGS {i}" for lbl, i in zip(gauges["label"], gauges["id"])],
            hovertemplate="%{text}<extra></extra>", name="Streamflow stations",
        ))
        layer_order.append("streamflow")

    if reservoirs is not None and not reservoirs.empty:
        fig.add_trace(_halo(reservoirs["lat"], reservoirs["lon"], 27))
        layer_order.append("reservoirs_halo")
        fig.add_trace(go.Scattermap(
            lat=reservoirs["lat"], lon=reservoirs["lon"], mode="markers+text",
            marker=dict(size=21, color=RESERVOIR_COLOR),
            text=reservoirs["name"], textposition="top center", textfont=dict(size=11, color="#7c2d12"),
            hovertemplate="%{text}<extra></extra>", name="Reservoirs",
        ))
        layer_order.append("reservoirs")

    if wells is not None and not wells.empty:
        bias = wells["mean_bias_m"]
        size = 7 + np.minimum(9, bias.abs() / 5)
        fig.add_trace(_halo(wells["lat"], wells["lon"], size + 4))
        layer_order.append("wells_halo")
        fig.add_trace(go.Scattermap(
            lat=wells["lat"], lon=wells["lon"], mode="markers",
            marker=dict(
                size=size, color=bias, colorscale="RdBu",
                cmin=-60, cmax=60, showscale=True,
                colorbar=dict(title="Well bias<br>sim − obs (m)", thickness=10, len=0.4, x=1.02, y=0.28, yanchor="middle"),
            ),
            text=[
                f"Well {i}<br>Mean bias (sim − obs): {b:+.1f} m<br>{n} well-years"
                for i, b, n in zip(wells["id"], bias, wells["n_years"])
            ],
            hovertemplate="%{text}<extra></extra>", name="Groundwater wells",
        ))
        layer_order.append("wells")

    if salinity_stations is not None and not salinity_stations.empty:
        fig.add_trace(_halo(salinity_stations["lat"], salinity_stations["lon"], 20))
        layer_order.append("salinity_halo")
        fig.add_trace(go.Scattermap(
            lat=salinity_stations["lat"], lon=salinity_stations["lon"], mode="markers",
            marker=dict(size=15, color=SALINITY_COLOR),
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

    zoom = fig.layout.map.zoom
    lats, lons = [], []

    def _collect(coords):
        if isinstance(coords[0], (int, float)):
            lons.append(coords[0])
            lats.append(coords[1])
        else:
            for c in coords:
                _collect(c)

    for feature in subbasins_geojson.get("features", []):
        _collect(feature["geometry"]["coordinates"])
    if lats:
        # centre on the basin's bounding box (the default is the mean of the vertices,
        # which sits off-centre for an elongated basin)
        fig.update_layout(map_center={"lat": (min(lats) + max(lats)) / 2, "lon": (min(lons) + max(lons)) / 2})
    fig.update_layout(
        map_zoom=(zoom + 0.7) if zoom else zoom,
        height=680,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, itemsizing="constant"),
    )
    return fig, layer_order
