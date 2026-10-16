"""The three views of the Model Performance page.

1. Streamflow · Groundwater · Reservoirs · Salinity -- one map; clicking a
   point redraws the matching chart below it (streamflow and reservoirs
   share a chart because dam outlets are streamflow gauges).
2. ET -- model vs. remote-sensing products: maps, metrics, time series.
3. Hydrologic responses -- the basin water balance and GW-SW exchange.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.io.climate_reader import (
    read_et_basin_monthly,
    read_et_grid,
    read_et_region_annual,
    read_et_region_monthly,
    read_et_regions,
    read_et_spatial_by_month,
    read_et_spatial_by_year,
)
from core.io.gw_calibration_reader import read_gw_calibration_pairs, read_gw_calibration_wells
from components.data_download import Family, render_download_panel
from core.io.reservoir_reader import read_reservoirs_meta, read_reservoirs_monthly
from core.io.salinity_reader import read_salinity_sites
from core.io.salinity_simulation_reader import (
    read_salinity_source_contrib,
    read_salinity_station_meta,
    read_salinity_station_observed,
    read_salinity_station_simulated,
)
from core.io.streamflow_runs_reader import (
    RUN_KEYS,
    RUN_LABELS,
    read_model_subbasins,
    read_streamflow_stations_all,
    read_subbasin_outlet_flow,
)
from core.io.water_balance_reader import read_water_balance_annual
from core.plotting.climate import (
    compute_et_spatial_stats,
    plot_et_grid_distribution,
    plot_et_region_annual,
    plot_et_animation,
    plot_et_region_monthly,
    plot_et_spatial_map,
    plot_et_water_balance,
)
from core.plotting.duration_curves import plot_fdc
from core.plotting.gw_calibration import plot_gw_well_timeseries
from core.plotting.observation_map import expected_layer_order, plot_observation_map
from core.plotting.salinity import (
    CONSTITUENT_LABELS,
    plot_source_contribution,
    plot_station_obs_vs_sim,
    plot_tds_distribution,
)
from core.plotting.streamflow_runs import compute_gauge_stats, plot_multirun_timeseries
from core.plotting.water_balance import plot_annual_water_balance, plot_gw_sw_interaction

LAYERS = [
    ("Streamflow stations", "streamflow"),
    ("Reservoirs", "reservoirs"),
    ("Groundwater wells", "wells"),
    ("Salinity stations", "salinity"),
]
DEFAULT_GAUGE = "08401500"  # Brantley outlet
DEFAULT_SALINITY_SITE = "08407500"  # Red Bluff


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _persistent_select(label, options, state_key, format_func=None, container=None):
    """A selectbox whose value survives view switches and map clicks."""
    target = container or st
    current = st.session_state.get(state_key)
    if current not in options:
        current = options[0]
    kwargs = {"format_func": format_func} if format_func else {}
    value = target.selectbox(label, options=options, index=options.index(current), **kwargs)
    st.session_state[state_key] = value
    return value


def _handle_map_click(points, layer_order, layers):
    """Turn the latest map click into the matching chart's selection.

    The plotly selection persists across reruns, so a click is applied only
    when it differs from the last one processed -- otherwise it would keep
    overriding what the dropdowns below were just set to.
    """
    ss = st.session_state
    if ss.get("_perf_layers") != tuple(layer_order):
        # Layer set changed: trace numbering changed with it, so the stored
        # selection can't be trusted. Remember it without applying.
        ss["_perf_layers"] = tuple(layer_order)
        ss["_perf_click"] = _click_signature(points)
        return
    sig = _click_signature(points)
    if sig is None:
        ss["_perf_click"] = None
        return
    if sig == ss.get("_perf_click"):
        return
    ss["_perf_click"] = sig

    curve, idx = sig
    layer = layer_order[curve] if curve is not None and curve < len(layer_order) else None
    if idx is None or layer is None:
        return
    if layer == "subbasins":
        ids = layers["subbasin_ids"]
        if idx < len(ids):
            ss["sel_subbasin"] = ids[idx]
    elif layer == "streamflow":
        ss["sel_gauge"] = layers["gauges"].iloc[idx]["id"]
    elif layer == "reservoirs":
        gauge = layers["reservoirs"].iloc[idx]["flow_gage_id"]
        if gauge in set(layers["gauges"]["id"]):
            ss["sel_gauge"] = gauge
    elif layer == "wells":
        ss["sel_well"] = layers["wells"].iloc[idx]["id"]
    elif layer == "salinity":
        ss["sel_salinity"] = layers["salinity"].iloc[idx]["site"]


# map layer -> (key in `layers`, id column) for the families a box/lasso can pick
_GROUP_SOURCES = {
    "streamflow": ("gauges", "id"),
    "reservoirs": ("reservoirs", "dam_key"),
    "wells": ("wells", "id"),
    "salinity": ("salinity", "site"),
}


def _group_from_points(points, layer_order, layers) -> dict[str, list[str]] | None:
    """Ids picked by a box/lasso selection, grouped by family. A point is
    selected on both its dot and its halo, so ids are de-duplicated."""
    out: dict[str, set[str]] = {}
    for p in points:
        curve, idx = p.get("curve_number"), p.get("point_index")
        if curve is None or idx is None or curve >= len(layer_order):
            continue
        family = layer_order[curve].removesuffix("_halo")
        if family not in _GROUP_SOURCES:
            continue
        key, col = _GROUP_SOURCES[family]
        out.setdefault(family, set()).add(str(layers[key].iloc[idx][col]))
    return {k: sorted(v) for k, v in out.items()} or None


def _click_signature(points):
    if not points:
        return None
    p = points[0]
    return (p.get("curve_number"), p.get("point_index"))


def _metrics_table(flow_monthly, gauge_id, run_keys) -> pd.DataFrame:
    rows = []
    for run in run_keys:
        s = compute_gauge_stats(flow_monthly, gauge_id, run)
        if s is None:
            continue
        rows.append({
            "Run": RUN_LABELS.get(run, run), "NSE": round(s["nse"], 2), "KGE": round(s["kge"], 2),
            "PBIAS (%)": round(s["pbias"], 1), "R²": round(s["r2"], 2),
            "RMSE (m³/s)": round(s["rmse"], 2), "n (months)": s["n"],
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# view 1: observations on one map
# --------------------------------------------------------------------------
def render_observation_view(bundle, context) -> None:
    basin_dir = bundle.basin_dir
    subbasins = read_model_subbasins(basin_dir) if context.basin_id == "Pecos" else None
    if subbasins is None:
        st.info("Observation points are only available for the Pecos basin right now.")
        return
    subbasin_flow = read_subbasin_outlet_flow(basin_dir)
    gauges, flow_monthly = read_streamflow_stations_all(basin_dir)
    res_meta = read_reservoirs_meta(basin_dir)
    res_meta = res_meta.assign(flow_gage_id=res_meta["flow_gage"].astype(str).str.zfill(8))
    wells = read_gw_calibration_wells(basin_dir)
    gw_pairs = read_gw_calibration_pairs(basin_dir)
    sal_meta = read_salinity_station_meta(basin_dir)
    sal_obs = read_salinity_station_observed(basin_dir)
    sal_sim = read_salinity_station_simulated(basin_dir)

    subbasin_ids = [f["properties"]["Subbasin"] for f in subbasins["features"] if f["properties"].get("Subbasin") is not None]
    layers = {"gauges": gauges, "reservoirs": res_meta, "wells": wells, "salinity": sal_meta, "subbasin_ids": subbasin_ids}
    ss = st.session_state
    ss.setdefault("sel_gauge", DEFAULT_GAUGE if DEFAULT_GAUGE in set(gauges["id"]) else gauges["id"].iloc[0])
    ss.setdefault("sel_well", wells["id"].iloc[0])
    ss.setdefault("sel_salinity", DEFAULT_SALINITY_SITE if DEFAULT_SALINITY_SITE in set(sal_meta["site"]) else sal_meta["site"].iloc[0])

    # --- map controls
    features = subbasins.get("features", [])
    numeric = [
        k for k, v in (features[0].get("properties", {}) if features else {}).items()
        if isinstance(v, (int, float)) and k not in ("Subbasin", "outlet_channel")
    ]
    col_layers, col_color = st.columns([3, 1])
    shown = col_layers.multiselect("Map layers", options=[n for n, _ in LAYERS], default=[n for n, _ in LAYERS])
    color_var = col_color.selectbox(
        "Color subbasins by", options=numeric, index=numeric.index("Elev") if "Elev" in numeric else 0, key="perf_color_var",
    ) if numeric else None
    enabled = {key for name, key in LAYERS if name in shown}

    expected_order = expected_layer_order(enabled)
    map_key = f"perf_map_{ss.get('perf_map_n', 0)}"
    map_state = ss.get(map_key) or {}
    points = (map_state.get("selection") or {}).get("points", []) if hasattr(map_state, "get") else []
    if len(points) > 1:
        # A box/lasso: collect the picked points for the download panel instead of
        # treating it as a click on one of them.
        trusted = ss.get("_perf_layers") == tuple(expected_order)
        ss["map_group"] = _group_from_points(points, expected_order, layers) if trusted else None
        ss["_perf_layers"] = tuple(expected_order)
        ss["_perf_click"] = _click_signature(points)
    else:
        ss["map_group"] = None
        _handle_map_click(points, expected_order, layers)

    fig, layer_order = plot_observation_map(
        subbasins, color_var,
        gauges=gauges if "streamflow" in enabled else None,
        reservoirs=res_meta if "reservoirs" in enabled else None,
        wells=wells if "wells" in enabled else None,
        salinity_stations=sal_meta if "salinity" in enabled else None,
        selected_gauge=ss["sel_gauge"], selected_well=ss["sel_well"], selected_salinity=ss["sel_salinity"],
        selected_subbasin=ss.get("sel_subbasin"),
    )
    map_col, side_col = st.columns([4, 2])
    with map_col:
        tool = st.segmented_control(
            "Map tool", options=["Pan / click", "Select box", "Select lasso"], default="Pan / click",
            key="perf_map_tool", help="Box and lasso pick a group of points (only the layers switched on) for the download panel.",
        ) or "Pan / click"
        fig.update_layout(dragmode={"Pan / click": "pan", "Select box": "select", "Select lasso": "lasso"}[tool])
        st.plotly_chart(
            fig, width="stretch", on_select="rerun", selection_mode=("points", "box", "lasso"),
            config={"scrollZoom": True, "displayModeBar": True}, key=map_key,
        )
        st.caption(
            "Click a point — or a subbasin — to chart it below. The highlighted ring and outline mark what the charts are showing. "
            "To pick a group, switch the map tool to Select box or Select lasso and drag over the map: only the layers switched on are included."
        )

    sal_series = pd.concat([
        sal_obs.assign(source="observed", date=sal_obs["date"].astype(str)),
        sal_sim.assign(source="simulated (annual)", date=sal_sim["year"].astype(str)).drop(columns="year"),
    ], ignore_index=True)[["station", "site", "constituent", "source", "date", "value_mgL"]]
    group = ss.get("map_group")
    with side_col:
        render_download_panel([
            Family("streamflow", "Streamflow stations", gauges, flow_monthly, "id", "gauge_id", "label"),
            Family("reservoirs", "Reservoirs", res_meta.drop(columns="flow_gage_id"), read_reservoirs_monthly(basin_dir), "dam_key", "dam_key", "name"),
            Family("wells", "Groundwater wells", wells, gw_pairs, "id", "id"),
            Family("salinity", "Salinity stations", sal_meta, sal_series, "site", "site", "station"),
        ], basin=context.basin_id, map_selection=group)
        if group:
            summary = ", ".join(f"{len(v)} {k}" for k, v in group.items())
            st.success(f"Selected on the map: {summary}.")
            if st.button("Clear map selection", key="clear_map_group"):
                ss["perf_map_n"] = ss.get("perf_map_n", 0) + 1
                ss["map_group"] = None
                ss["_perf_click"] = None
                st.rerun()

    # --- chart 1: streamflow + reservoir outlets
    st.divider()
    st.subheader("Streamflow & reservoir outlets")
    gauge_labels = dict(zip(gauges["id"], gauges["label"]))
    dam_by_gauge = dict(zip(res_meta["flow_gage_id"], res_meta["name"]))
    c1, c2 = st.columns([2, 3])
    gauge_id = _persistent_select(
        "Gauge", gauges["id"].tolist(), "sel_gauge",
        format_func=lambda g: gauge_labels.get(g, g) + (f" · {dam_by_gauge[g]}" if g in dam_by_gauge else ""),
        container=c1,
    )
    run_keys = c2.multiselect("Simulations", options=RUN_KEYS, default=RUN_KEYS, format_func=lambda r: RUN_LABELS.get(r, r))
    log_scale = st.checkbox("Log scale (flow spans orders of magnitude)", value=True)
    sb_options = [None, *subbasin_ids]
    sb_current = ss.get("sel_subbasin")
    sb_pick = st.selectbox(
        "Subbasin outlet (simulated)", options=sb_options,
        index=sb_options.index(sb_current) if sb_current in sb_options else 0,
        format_func=lambda i: "None — click a subbasin on the map" if i is None else f"Subbasin {i}",
    )
    ss["sel_subbasin"] = sb_pick
    picked = gauges[gauges["id"] == gauge_id].iloc[0]
    if picked.get("group") == "extra":
        window = (
            "Monthly means of the daily USGS record, 2000–2025, against the model channel closest to the station "
            f"({picked['snap_m']:,.0f} m away, draining about {picked['drain_km2']:,.0f} km²). Where the station sits "
            "on a small tributary, or just below a dam, the model channel can differ from what the gauge sees."
        )
    else:
        window = "The comparison window is 2002–2007."
    st.caption(
        f"**{gauge_labels.get(gauge_id, gauge_id)}** — USGS {gauge_id}. Observed monthly flow (hollow red) "
        f"against the model runs that cover the full 2000–2025 period. {window}"
        + (" Dotted lines: the model's flow at the outlet of the selected subbasin (no observations exist there)." if sb_pick is not None else "")
    )
    st.plotly_chart(
        plot_multirun_timeseries(flow_monthly, gauge_id, run_keys, log_scale=log_scale,
                                 subbasin_flow=subbasin_flow, subbasin_id=sb_pick),
        width="stretch", key="perf_flow_chart",
    )
    table = _metrics_table(flow_monthly, gauge_id, run_keys)
    if not table.empty:
        st.dataframe(table, hide_index=True, width="stretch")

    # --- chart 2: groundwater
    st.divider()
    st.subheader("Groundwater — depth to water table")
    well_id = _persistent_select("Well", wells["id"].tolist(), "sel_well")
    well_pairs = gw_pairs[gw_pairs["id"] == well_id].sort_values("year")
    bias = well_pairs["sim_depth_m"] - well_pairs["obs_depth_m"]
    st.plotly_chart(plot_gw_well_timeseries(well_pairs, well_id), width="stretch", key="perf_gw_chart")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Mean observed", f"{well_pairs['obs_depth_m'].mean():.1f} m")
    m2.metric("Mean simulated", f"{well_pairs['sim_depth_m'].mean():.1f} m")
    m3.metric("Bias (sim − obs)", f"{bias.mean():+.1f} m")
    m4.metric("Well-years", len(well_pairs))
    st.caption(
        "Depth below ground surface (0 at the top). A well is a point while the model cell averages several km², "
        "and the model has one aquifer layer, so deep or confined wells (beyond 130 m) are left out."
    )

    # --- chart 3: salinity
    st.divider()
    st.subheader("Salinity")
    sal_labels = dict(zip(sal_meta["site"], sal_meta["station"]))
    s1, s2 = st.columns(2)
    site = _persistent_select("Station", sal_meta["site"].tolist(), "sel_salinity", format_func=lambda s: sal_labels.get(s, s), container=s1)
    constituent = s2.selectbox("Constituent", options=list(CONSTITUENT_LABELS), format_func=CONSTITUENT_LABELS.get)
    st.plotly_chart(plot_station_obs_vs_sim(sal_obs, sal_sim, site, constituent), width="stretch", key="perf_salinity_chart")
    n_obs = int(sal_meta[sal_meta["site"] == site].iloc[0][f"n_{constituent}"])
    st.caption(
        f"{sal_labels.get(site, site)}: {n_obs:,} real Water Quality Portal grab samples (hollow red) against the "
        "model's annual flux-weighted concentration (green)."
    )

    with st.expander("Salinity context — where the salt comes from, and the full site inventory"):
        contrib = read_salinity_source_contrib(basin_dir)
        if not contrib.empty:
            st.plotly_chart(plot_source_contribution(contrib.iloc[0].to_dict()), width="stretch", key="perf_salt_sources")
        sites = read_salinity_sites(basin_dir)
        if not sites.empty:
            a, b, c = st.columns(3)
            a.metric("Sampling sites", f"{len(sites):,}")
            b.metric("Median TDS", f"{sites['tds_mean'].median():,.0f} mg/L")
            c.metric("Sites > 6,000 mg/L", f"{int((sites['tds_mean'] > 6000).sum()):,}")
            st.plotly_chart(plot_tds_distribution(sites), width="stretch", key="perf_tds_hist")
            st.caption("Houston et al. (2019), USGS Pecos River Basin Salinity Assessment (DOI 10.5066/F7DB800T).")


# --------------------------------------------------------------------------
# view 2: ET
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Preparing the ET maps…")
def _et_animation(basin_dir, step: str, product: str):
    """One animated figure per (time step, product); cached so switching back is instant."""
    by_year = read_et_spatial_by_year(basin_dir)
    mean_label = "2010–2019 mean"
    if step == "Monthly":
        data = read_et_spatial_by_month(basin_dir)
        data = data.assign(_k=data["year"] * 100 + data["month"])
        keys = sorted(data["_k"].unique())
        labels = [f"{k // 100}-{k % 100:02d}" for k in keys]
        ticks = [str(k // 100) if k % 100 == 1 else "" for k in keys]
        unit = "mm/month"
        wide = lambda col: data.pivot_table(index=["lat", "lon"], columns="_k", values=col, aggfunc="mean")[keys]
    else:
        data = by_year.assign(_k=by_year["year"])
        years = sorted(data["_k"].unique())
        labels = [mean_label, *[str(y) for y in years]]
        ticks = labels
        unit = "mm/yr"

        def wide(col):
            w = data.pivot_table(index=["lat", "lon"], columns="_k", values=col, aggfunc="mean")[years]
            mean = w[[y for y in years if 2010 <= y <= 2019]].mean(axis=1)
            return pd.concat([mean.rename(mean_label), w.rename(columns=str)], axis=1)

    model_w, prod_w = wide("model_v52prod_mm"), wide(product)
    cells = model_w.index
    prod_w = prod_w.reindex(cells)
    label = "SSEBop" if product == "ssebop_et_mm" else "TerraClimate"
    return plot_et_animation(
        cells.get_level_values("lat").to_numpy(), cells.get_level_values("lon").to_numpy(), labels,
        [model_w.iloc[:, i].to_numpy() for i in range(len(labels))],
        [prod_w.iloc[:, i].to_numpy() for i in range(len(labels))],
        label, unit, slider_ticks=ticks,
    )


def render_et_view(bundle, context) -> None:
    if context.basin_id != "Pecos":
        st.info("ET comparison is only available for the Pecos basin right now.")
        return

    basin_dir = bundle.basin_dir
    by_year = read_et_spatial_by_year(basin_dir)
    by_month = read_et_spatial_by_month(basin_dir)

    if not by_year.empty:
        product = st.radio(
            "Compare against", options=["ssebop_et_mm", "terraclimate_et_mm"], horizontal=True,
            format_func=lambda c: "SSEBop (MODIS, energy balance)" if c == "ssebop_et_mm" else "TerraClimate",
        )
        step = "Annual"
        if not by_month.empty:
            step = st.radio("Time step", ["Annual", "Monthly"], horizontal=True, key="et_step")

        st.caption(
            "The model's own ET (HRU + groundwater ET, production run) against a remote-sensing product at "
            "0.1° grid cells. Use the slider or Play to step through 2010–2024 — the frames are already in your "
            "browser, so stepping is instant — and colors keep one scale across the whole period. "
            "In the difference map, green means the model evaporates more."
        )
        st.plotly_chart(
            _et_animation(basin_dir, step, product), width="stretch", key=f"et_anim_{step}_{product}",
            config={"displayModeBar": False},
        )

    regions = read_et_regions(basin_dir)
    monthly = read_et_region_monthly(basin_dir)
    annual = read_et_region_annual(basin_dir)
    if not regions.empty:
        st.divider()
        st.subheader("ET through time")
        region_labels = dict(zip(regions["region"], regions["label"]))
        region = _persistent_select("Region", regions["region"].tolist(), "sel_et_region", format_func=lambda r: region_labels.get(r, r))

        st.markdown("**Monthly, 2010–2025**")
        st.plotly_chart(plot_et_region_monthly(monthly[monthly["region"] == region]), width="stretch", key="et_monthly_chart")
        st.caption(
            "Both products are remote-sensing estimates, drawn as observations; the line is the production run's "
            "monthly ET (HRU + groundwater)."
        )
        st.markdown("**Annual, 2010–2025**")
        st.plotly_chart(plot_et_region_annual(annual[annual["region"] == region]), width="stretch", key="et_annual_chart")

    et_basin = read_et_basin_monthly(basin_dir)
    et_grid = read_et_grid(basin_dir)
    if not et_basin.empty:
        st.divider()
        st.subheader("Climate context")
        a, b, c = st.columns(3)
        ppt, aet = et_basin["ppt_mm"].mean() * 12, et_basin["aet_mm"].mean() * 12
        a.metric("Mean annual precipitation", f"{ppt:,.0f} mm/yr")
        b.metric("Mean annual actual ET", f"{aet:,.0f} mm/yr")
        c.metric("ET / precipitation", f"{aet / ppt * 100:.0f}%")
        st.plotly_chart(plot_et_water_balance(et_basin), width="stretch", key="et_water_balance_chart")
        st.caption(
            "TerraClimate (Abatzoglou et al. 2018), basin-averaged, 2000–2020. Nearly all precipitation leaves "
            "the basin as evapotranspiration — a key reason streamflow is so limited."
        )
    if not et_grid.empty:
        st.plotly_chart(plot_et_grid_distribution(et_grid), width="stretch", key="et_grid_hist")


# --------------------------------------------------------------------------
# view 3: hydrologic responses
# --------------------------------------------------------------------------
def render_hydrology_view(bundle, context) -> None:
    if context.basin_id != "Pecos":
        st.info("Hydrologic responses are only available for the Pecos basin right now.")
        return

    wb = read_water_balance_annual(bundle.basin_dir)
    if wb.empty:
        st.info("No water balance record found for this basin.")
        return

    st.caption("Where the model sends water each year, basin-wide, 2000–2025 — the model's own simulated balance.")
    a, b, c, d = st.columns(4)
    a.metric("Mean precipitation", f"{wb['prec'].mean():,.0f} mm/yr")
    b.metric("Groundwater → stream", f"{wb['gwq'].mean():.1f} mm/yr")
    c.metric("Stream → aquifer", f"{wb['swgw'].mean():.1f} mm/yr")
    d.metric("Net to the stream", f"{(wb['gwq'] - wb['swgw']).mean():+.1f} mm/yr")

    st.subheader("Annual water balance")
    st.plotly_chart(plot_annual_water_balance(wb), width="stretch", key="hyd_balance_chart")

    st.divider()
    st.subheader("Groundwater–surface water interaction")
    st.plotly_chart(plot_gw_sw_interaction(wb), width="stretch", key="hyd_gwsw_chart")
    st.caption(
        "The aquifer discharges to the streams every year and takes less back through seepage, so over the "
        "full record it is a steady net source of baseflow rather than a sink."
    )

    st.divider()
    st.subheader("Flow duration")
    st.plotly_chart(plot_fdc(bundle.streamflow_joined), width="stretch", key="hyd_fdc_chart")
