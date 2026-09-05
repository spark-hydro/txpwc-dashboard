from __future__ import annotations

import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def plot_station_map(stations: pd.DataFrame):
    if stations.empty or not {"lat", "lon"}.issubset(stations.columns):
        return px.scatter_map(
            pd.DataFrame({"lat": [31.5], "lon": [-103.0], "label": ["No stations loaded"]}),
            lat="lat",
            lon="lon",
            hover_name="label",
            zoom=5,
            height=500,
        )

    df = stations.copy()
    if "name" not in df.columns:
        df["name"] = df["site_id"]

    fig = px.scatter_map(
        df,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data=["site_id", "kind"] if "kind" in df.columns else ["site_id"],
        zoom=6,
        height=500,
    )
    fig.update_layout(title="TxPWC Monitoring / Model Locations")
    return fig


def _get_map_center_and_zoom(subbasins_geojson: dict):
    lats = []
    lons = []

    for feature in subbasins_geojson.get("features", []):
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [])

        # Handle MultiPolygon and Polygon
        def extract_coords(c):
            if isinstance(c[0][0], (float, int)):  # single ring
                return [c]
            return c

        for polygon in coords:
            for ring in extract_coords(polygon):
                for lon, lat in ring:
                    lats.append(lat)
                    lons.append(lon)

    if not lats or not lons:
        return {"lat": 31.5, "lon": -103.0}, 6  # fallback

    center = {
        "lat": sum(lats) / len(lats),
        "lon": sum(lons) / len(lons),
    }

    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)
    max_range = max(lat_range, lon_range)

    if max_range > 10:
        zoom = 4
    elif max_range > 5:
        zoom = 5
    elif max_range > 2:
        zoom = 6
    elif max_range > 1:
        zoom = 7
    else:
        zoom = 8

    return center, zoom


def plot_subbasins_map(subbasins_geojson: dict, color_field: str | None = None):
    features = subbasins_geojson.get("features", [])

    locations = []
    z_values = []
    hover_text = []

    for feature in features:
        props = feature.get("properties", {})

        subbasin_id = props.get("Subbasin")
        if subbasin_id is None:
            continue

        locations.append(subbasin_id)

        if color_field is not None:
            z_values.append(props.get(color_field, 0))
        else:
            z_values.append(subbasin_id)

        hover_lines = [f"Subbasin: {subbasin_id}"]
        if color_field is not None:
            hover_lines.append(f"{color_field}: {props.get(color_field, 'NA')}")
        hover_text.append("<br>".join(hover_lines))

    fig = go.Figure()

    fig.add_trace(
        go.Choroplethmapbox(
            geojson=subbasins_geojson,
            locations=locations,
            z=z_values,
            customdata=locations,
            featureidkey="properties.Subbasin",
            colorscale="Turbo",  # more contrast for hydrologic variables
            marker_opacity=0.40,
            marker_line_width=0.8,
            showscale=True if color_field is not None else False,
            colorbar=dict(
                title=color_field if color_field else "",
            ),
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
        )
    )
    center, zoom = _get_map_center_and_zoom(subbasins_geojson)
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_center=center,
        mapbox_zoom=zoom,
        dragmode="pan",
        margin=dict(l=10, r=10, t=10, b=10),
        height=600,
    )

    return fig

def plot_station_map(stations_df: pd.DataFrame):
    fig = go.Figure()

    fig.add_trace(
        go.Scattermapbox(
            lat=stations_df["lat"],
            lon=stations_df["lon"],
            mode="markers",
            marker=dict(size=9),
            text=stations_df["station_id"],
            hovertemplate="Station: %{text}<extra></extra>",
        )
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        margin=dict(l=10, r=10, t=10, b=10),
        height=600,
    )

    return fig


def plot_watershed_overview(
    subbasins_geojson: dict,
    color_field: str | None = None,
    stations_geojson: dict | None = None,
    wells_meta: pd.DataFrame | None = None,
    reservoirs_meta: pd.DataFrame | None = None,
    salinity_sites: pd.DataFrame | None = None,
) -> tuple[go.Figure, list[str]]:
    """One shared watershed map with optional, toggleable real-data overlays.

    Each optional dataset becomes its own named Scattermapbox trace with its
    own legend entry -- once shown, click the legend to hide/show a layer
    without a rerun. Returns (fig, layer_order), where layer_order[i] names
    the layer for curve_number i, so click events can be routed back to the
    right dataset (subbasin vs. well vs. dam) by the caller.
    """
    fig = plot_subbasins_map(subbasins_geojson, color_field=color_field)
    layer_order = ["subbasins"]

    if stations_geojson is not None:
        fig = add_station_geojson_points(fig, stations_geojson)
        layer_order.append("stations")

    if wells_meta is not None and not wells_meta.empty:
        sizes = 6 + np.minimum(4, np.log2(1 + wells_meta["n_obs"].fillna(0)))
        fig.add_trace(
            go.Scattermapbox(
                lat=wells_meta["lat"],
                lon=wells_meta["lon"],
                mode="markers",
                marker=dict(size=sizes, color="#7c3aed"),
                text=wells_meta["label"],
                hovertemplate="%{text}<extra></extra>",
                name="Groundwater wells",
            )
        )
        layer_order.append("wells")

    if reservoirs_meta is not None and not reservoirs_meta.empty:
        colors = reservoirs_meta["state"].map({"NM": "#4cc9f0", "TX": "#f4a261"}).fillna("#4cc9f0")
        fig.add_trace(
            go.Scattermapbox(
                lat=reservoirs_meta["lat"],
                lon=reservoirs_meta["lon"],
                mode="markers+text",
                marker=dict(size=16, color=colors),
                text=reservoirs_meta["name"],
                textposition="top center",
                hovertemplate="%{text}<extra></extra>",
                name="Reservoirs",
            )
        )
        layer_order.append("reservoirs")

    if salinity_sites is not None and not salinity_sites.empty:
        with_tds = salinity_sites[salinity_sites["tds_mean"].notna()]
        if not with_tds.empty:
            log_tds = np.log10(with_tds["tds_mean"].clip(lower=1))
            fig.add_trace(
                go.Scattermapbox(
                    lat=with_tds["lat"],
                    lon=with_tds["lon"],
                    mode="markers",
                    marker=dict(
                        size=5,
                        color=log_tds,
                        colorscale="YlOrRd",
                        cmin=1, cmax=5.3,
                        showscale=True,
                        colorbar=dict(
                            title="TDS (mg/L)",
                            x=1.15,
                            tickvals=[1, 2, 3, 4, 5],
                            ticktext=["10", "100", "1,000", "10,000", "100,000"],
                        ),
                    ),
                    text=[
                        f"{d}<br>Mean TDS: {t:,.0f} mg/L"
                        for d, t in zip(with_tds["desc"], with_tds["tds_mean"])
                    ],
                    hovertemplate="%{text}<extra></extra>",
                    name="Salinity sites",
                )
            )
            layer_order.append("salinity")

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig, layer_order


def add_station_geojson_points(fig, stations_geojson: dict):
    features = stations_geojson.get("features", [])

    lats = []
    lons = []
    labels = []

    for feature in features:
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})

        if geom.get("type") != "Point":
            continue

        coords = geom.get("coordinates", [])
        if len(coords) < 2:
            continue

        lon, lat = coords[:2]

        lons.append(lon)
        lats.append(lat)
        site_no = props.get("SITENO", "NA")
        site_name = props.get("SITENAME", "NA")
        category = props.get("CATEGORY", "NA")
        agency = props.get("AGENCY", "NA")

        labels.append(
            f"Site No: {site_no}<br>"
            f"Name: {site_name}<br>"
            f"Category: {category}<br>"
            f"Agency: {agency}"
        )

    fig.add_trace(
        go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode="markers",
            marker=dict(
                size=8,
                color="red",
                opacity=0.5,
            ),
            text=labels,
            # hovertemplate="Station: %{text}<extra></extra>",
            hovertemplate="%{text}<extra></extra>",
            name="Stations",
        )
    )

    return fig