"""The Model Performance map: subbasins plus the clickable observation points.

Each layer is one named trace, so the legend hides/shows it instantly and a
click can be routed back to its dataset by trace position (see layer_order).
Each family has a "ring" trace under its points that circles whatever is currently selected, so the map
always shows which point the charts below are drawing. The ring, the halo and the points of a family share a
legend group, so hiding the family from the legend hides all three.

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

# Red (simulated too shallow) to blue (too deep). The middle is a visible grey, not the white of the
# stock red-blue scale: a well with almost no bias must still show up against its white halo.
WELL_BIAS_SCALE = [
    [0.0, "#b2182b"], [0.25, "#ef8a62"], [0.5, "#bdbdbd"], [0.75, "#67a9cf"], [1.0, "#2166ac"],
]


def expected_layer_order(enabled: set[str]) -> list[str]:
    """Trace order the map is built with, so a click's curve number can be
    checked against it before the figure exists."""
    order = ["subbasins"]
    for key in POINT_LAYERS:
        if key in enabled:
            order += [f"{key}_ring", f"{key}_halo", key]
    return order + ["subbasin_outline"]


def _ring_trace(df: pd.DataFrame | None, group: str) -> go.Scattermap:
    """Dark ring around the selected point of one family (empty when nothing of it is selected)."""
    lat = df["lat"].tolist() if df is not None and len(df) else []
    lon = df["lon"].tolist() if df is not None and len(df) else []
    return go.Scattermap(
        lat=lat, lon=lon, mode="markers",
        marker=dict(size=30, color="#111827", opacity=0.30),
        hoverinfo="skip", showlegend=False, name="selected", legendgroup=group,
    )


def _halo(lat, lon, size, group: str) -> go.Scattermap:
    """White ring under a point layer. It shares the layer's legend group, so hiding the layer from the
    legend hides its halos too (otherwise white dots would be left behind)."""
    return go.Scattermap(
        lat=lat, lon=lon, mode="markers",
        marker=dict(size=size, color=HALO_COLOR, opacity=0.95),
        hoverinfo="skip", showlegend=False, name="halo", legendgroup=group,
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

    if gauges is not None and not gauges.empty:
        extra = gauges["group"].eq("extra") if "group" in gauges else pd.Series(False, index=gauges.index)
        size = np.where(extra, 9, 14)
        fig.add_trace(_ring_trace(gauges[gauges["id"] == selected_gauge] if selected_gauge is not None else None, "streamflow"))
        layer_order.append("streamflow_ring")
        fig.add_trace(_halo(gauges["lat"], gauges["lon"], size + 5, "streamflow"))
        layer_order.append("streamflow_halo")
        fig.add_trace(go.Scattermap(
            lat=gauges["lat"], lon=gauges["lon"], mode="markers",
            marker=dict(size=size, color=np.where(extra, EXTRA_STREAMFLOW_COLOR, STREAMFLOW_COLOR)),
            text=[f"{lbl}<br>USGS {i}" for lbl, i in zip(gauges["label"], gauges["id"])],
            hovertemplate="%{text}<extra></extra>", name="Streamflow stations", legendgroup="streamflow",
        ))
        layer_order.append("streamflow")

    if reservoirs is not None and not reservoirs.empty:
        fig.add_trace(_ring_trace(reservoirs[reservoirs["flow_gage_id"] == selected_gauge] if selected_gauge is not None else None, "reservoirs"))
        layer_order.append("reservoirs_ring")
        fig.add_trace(_halo(reservoirs["lat"], reservoirs["lon"], 27, "reservoirs"))
        layer_order.append("reservoirs_halo")
        fig.add_trace(go.Scattermap(
            lat=reservoirs["lat"], lon=reservoirs["lon"], mode="markers+text",
            marker=dict(size=21, color=RESERVOIR_COLOR),
            text=reservoirs["name"], textposition="top center", textfont=dict(size=11, color="#7c2d12"),
            hovertemplate="%{text}<extra></extra>", name="Reservoirs", legendgroup="reservoirs",
        ))
        layer_order.append("reservoirs")

    if wells is not None and not wells.empty:
        bias = wells["mean_bias_m"]
        size = 7 + np.minimum(9, bias.abs() / 5)
        fig.add_trace(_ring_trace(wells[wells["id"] == selected_well] if selected_well is not None else None, "wells"))
        layer_order.append("wells_ring")
        fig.add_trace(_halo(wells["lat"], wells["lon"], size + 4, "wells"))
        layer_order.append("wells_halo")
        fig.add_trace(go.Scattermap(
            lat=wells["lat"], lon=wells["lon"], mode="markers",
            marker=dict(
                size=size, color=bias, colorscale=WELL_BIAS_SCALE,
                cmin=-60, cmax=60, showscale=True,
                colorbar=dict(title="Well bias<br>sim − obs (m)", thickness=10, len=0.4, x=1.02, y=0.28, yanchor="middle"),
            ),
            text=[
                f"Well {i}<br>Mean bias (sim − obs): {b:+.1f} m<br>{n} well-years"
                for i, b, n in zip(wells["id"], bias, wells["n_years"])
            ],
            hovertemplate="%{text}<extra></extra>", name="Groundwater wells", legendgroup="wells",
        ))
        layer_order.append("wells")

    if salinity_stations is not None and not salinity_stations.empty:
        fig.add_trace(_ring_trace(salinity_stations[salinity_stations["site"] == selected_salinity] if selected_salinity is not None else None, "salinity"))
        layer_order.append("salinity_ring")
        fig.add_trace(_halo(salinity_stations["lat"], salinity_stations["lon"], 20, "salinity"))
        layer_order.append("salinity_halo")
        fig.add_trace(go.Scattermap(
            lat=salinity_stations["lat"], lon=salinity_stations["lon"], mode="markers",
            marker=dict(size=15, color=SALINITY_COLOR),
            text=[f"{s}<br>USGS {i}" for s, i in zip(salinity_stations["station"], salinity_stations["site"])],
            hovertemplate="%{text}<extra></extra>", name="Salinity stations", legendgroup="salinity",
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
        map_zoom=(zoom + 0.9) if zoom else zoom,
        height=820,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, itemsizing="constant"),
    )
    return fig, layer_order
