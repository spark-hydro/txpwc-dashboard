import streamlit as st
from components.cards import render_metric_cards
from components.sidebar import render_sidebar
from core.metrics.performance import compute_basic_summary
from core.plotting.duration_curves import plot_fdc
from core.plotting.groundwater import plot_groundwater_scatter, plot_well_timeseries
from core.plotting.hydrographs import plot_streamflow_hydrograph
from core.plotting.maps import plot_station_map
from core.services.performance_service import load_performance_bundle
from core.plotting.maps import (
    plot_station_map,
    plot_subbasins_map,
    add_station_geojson_points,
    plot_watershed_overview,
)
from core.plotting.reservoirs import plot_reservoir_timeseries
from core.io.reservoir_reader import read_reservoirs_meta, read_reservoirs_monthly
from core.io.wells_reader import read_wells_meta, read_wells_timeseries
from core.io.salinity_reader import read_salinity_sites
from core.io.climate_reader import read_et_basin_monthly, read_et_grid, read_et_spatial_comparison
from core.io.gw_calibration_reader import read_gw_calibration_wells, read_gw_calibration_pairs
from core.io.water_balance_reader import read_water_balance_annual
from core.io.streamflow_runs_reader import (
    read_streamflow_gauges_meta,
    read_streamflow_monthly_obs_sim,
    RUN_KEYS as FLOW_RUN_KEYS,
    RUN_LABELS as FLOW_RUN_LABELS,
)
from core.io.salinity_simulation_reader import (
    read_salinity_station_meta,
    read_salinity_station_observed,
    read_salinity_station_simulated,
    read_salinity_source_contrib,
    read_salinity_reach_export,
)
from core.plotting.salinity import plot_tds_distribution, plot_station_obs_vs_sim, plot_source_contribution
from core.plotting.climate import (
    plot_et_water_balance,
    plot_et_grid_distribution,
    plot_et_spatial_map,
    compute_et_spatial_stats,
)
from core.plotting.gw_calibration import plot_gw_obs_vs_sim_scatter, plot_gw_well_timeseries
from core.plotting.water_balance import plot_annual_water_balance
from core.plotting.streamflow_runs import compute_gauge_stats, plot_seasonal_shape, plot_multirun_timeseries
import plotly.graph_objects as go
from core.metrics.mobj_adapter import evaluate_metrics
from core.io.txpwc_reader import read_observed_station_timeseries
import pandas as pd
import base64
import streamlit.components.v1 as components


st.set_page_config(layout="wide")

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

context = render_sidebar()
bundle = load_performance_bundle(context)

if context.basin_id == "Pecos":
    wells_meta = read_wells_meta(bundle.basin_dir)
    wells_ts = read_wells_timeseries(bundle.basin_dir)
    res_meta = read_reservoirs_meta(bundle.basin_dir)
    res_ts = read_reservoirs_monthly(bundle.basin_dir)
    salinity_sites = read_salinity_sites(bundle.basin_dir)
    et_grid = read_et_grid(bundle.basin_dir)
    et_spatial = read_et_spatial_comparison(bundle.basin_dir)
    gw_cal_wells = read_gw_calibration_wells(bundle.basin_dir)
    gw_cal_pairs = read_gw_calibration_pairs(bundle.basin_dir)
    water_balance = read_water_balance_annual(bundle.basin_dir)
    flow_gauges_meta = read_streamflow_gauges_meta(bundle.basin_dir)
    flow_monthly = read_streamflow_monthly_obs_sim(bundle.basin_dir)
    sal_station_meta = read_salinity_station_meta(bundle.basin_dir)
    sal_obs = read_salinity_station_observed(bundle.basin_dir)
    sal_sim = read_salinity_station_simulated(bundle.basin_dir)
    sal_contrib = read_salinity_source_contrib(bundle.basin_dir)
    sal_reach_export = read_salinity_reach_export(bundle.basin_dir)
else:
    wells_meta = wells_ts = res_meta = res_ts = salinity_sites = et_grid = et_spatial = pd.DataFrame()
    flow_gauges_meta = flow_monthly = pd.DataFrame()
    gw_cal_wells = gw_cal_pairs = water_balance = pd.DataFrame()
    sal_station_meta = sal_obs = sal_sim = sal_contrib = sal_reach_export = pd.DataFrame()


def _subbasin_streamflow_df(subbasin_id):
    """Merged observed+simulated streamflow for one subbasin.

    Shared by the map's click panel and the Streamflow tab, so both show
    the exact same series built the exact same way.
    """
    station_matches = pd.DataFrame()
    if not bundle.stations.empty:
        station_matches = bundle.stations[
            bundle.stations["subbasin"].astype(str) == str(subbasin_id)
        ].copy()
    matched_station = station_matches.iloc[0] if not station_matches.empty else None

    sub_df = pd.DataFrame()
    if not bundle.channel_daily.empty:
        sub_df = bundle.channel_daily[bundle.channel_daily["gis_id"] == int(subbasin_id)].copy()

    sim_plot_df = pd.DataFrame(columns=["date", "simulated"])
    if not sub_df.empty:
        sim_plot_df = sub_df[["date", "flo_out"]].rename(columns={"flo_out": "simulated"})

    obs_plot_df = pd.DataFrame(columns=["date", "observed"])
    if matched_station is not None:
        site_no = str(matched_station["site_no"]).strip().split(".")[0].zfill(8)
        obs_plot_df = read_observed_station_timeseries(
            basin_dir=bundle.basin_dir,
            filename=bundle.observed_data_filename,
            site_no=site_no,
            variable="flow",
        )

    if not obs_plot_df.empty:
        plot_df = obs_plot_df.merge(sim_plot_df, on="date", how="inner")
    else:
        plot_df = sim_plot_df.copy()

    if not plot_df.empty:
        plot_df = plot_df.sort_values("date").reset_index(drop=True)

    return plot_df, station_matches


def _subbasin_streamflow_fig(plot_df, subbasin_id, compact=False):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=plot_df["date"], y=plot_df["simulated"], mode="lines", name="Simulated")
    )
    if "observed" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df["date"], y=plot_df["observed"],
                mode="markers", name="Observed",
                marker=dict(symbol="circle", size=7, color="rgba(0,0,0,0)", line=dict(color="red", width=1.5), opacity=0.5),
            )
        )
    fig.update_layout(
        title="" if compact else f"Streamflow — Subbasin {subbasin_id}",
        xaxis_title="" if compact else "Date",
        yaxis_title="" if compact else "Streamflow Discharge (cm³/s)",
        height=200 if compact else None,
        showlegend=not compact,
        margin=dict(l=10, r=10, t=10 if compact else 40, b=10),
        hovermode="x unified",
    )
    return fig


st.title("Model Performance")
st.caption("Initial end-to-end vertical slice: context selection → data load → metrics → plots.")
st.subheader("Watershed Map")

if bundle.subbasins_geojson is not None:
    features = bundle.subbasins_geojson.get("features", [])

    numeric_candidates = []
    if features:
        sample_props = features[0].get("properties", {})
        for key, value in sample_props.items():
            if isinstance(value, (int, float)):
                numeric_candidates.append(key)

    default_var = "Elev" if "Elev" in numeric_candidates else (
        numeric_candidates[0] if numeric_candidates else None
    )

    col_var, col_layers = st.columns([1, 2])
    with col_var:
        selected_var = None
        if numeric_candidates:
            selected_var = st.selectbox(
                "Color subbasins by",
                options=numeric_candidates,
                index=numeric_candidates.index(default_var) if default_var in numeric_candidates else 0,
                key="shared_map_color_var",
            )

    layer_options = []
    if bundle.stations is not None and not bundle.stations.empty:
        layer_options.append("Stations")
    if not wells_meta.empty:
        layer_options.append("Groundwater wells")
    if not res_meta.empty:
        layer_options.append("Reservoirs")
    if not salinity_sites.empty:
        layer_options.append("Salinity sites")
    if not et_grid.empty:
        layer_options.append("ET grid")
    if not gw_cal_wells.empty:
        layer_options.append("GW accuracy")
    if not sal_reach_export.empty:
        layer_options.append("Salt export (simulated)")

    with col_layers:
        show_layers = st.multiselect(
            "Show on map",
            options=layer_options,
            default=["Stations"] if "Stations" in layer_options else [],
            help="Pick which real datasets to overlay. Once shown, click a "
                 "name in the map legend to hide/show that layer instantly.",
        )

    fig, layer_order, salinity_plotted = plot_watershed_overview(
        bundle.subbasins_geojson,
        color_field=selected_var,
        stations_geojson=bundle.stations_geojson if "Stations" in show_layers else None,
        wells_meta=wells_meta if "Groundwater wells" in show_layers else None,
        reservoirs_meta=res_meta if "Reservoirs" in show_layers else None,
        salinity_sites=salinity_sites if "Salinity sites" in show_layers else None,
        et_grid=et_grid if "ET grid" in show_layers else None,
        gw_calibration_wells=gw_cal_wells if "GW accuracy" in show_layers else None,
        salt_reach_export=sal_reach_export if "Salt export (simulated)" in show_layers else None,
    )

    map_event = st.plotly_chart(
        fig,
        width="stretch",
        on_select="rerun",
        selection_mode="points",
        config={"scrollZoom": True},
        key="watershed_map",
    )

    clicked_points = map_event.selection["points"] if map_event and map_event.selection else []

    if clicked_points:
        clicked = clicked_points[0]
        curve_number = clicked.get("curve_number")
        point_index = clicked.get("point_index")
        layer = layer_order[curve_number] if curve_number is not None and curve_number < len(layer_order) else None

        if layer == "subbasins" and point_index is not None and 0 <= point_index < len(features):
            props = features[point_index].get("properties", {})
            subbasin_id = props.get("Subbasin")
            st.session_state["selected_subbasin"] = subbasin_id
            st.caption(f"Selected subbasin {subbasin_id} — see the Streamflow and Sediment Yield tabs below.")

        elif layer == "wells" and point_index is not None and 0 <= point_index < len(wells_meta):
            well_row = wells_meta.iloc[point_index]
            st.session_state["selected_well"] = well_row["id"]
            st.caption(f"Selected {well_row['label']} — see the Groundwater tab below.")

        elif layer == "reservoirs" and point_index is not None and 0 <= point_index < len(res_meta):
            dam_row = res_meta.iloc[point_index]
            st.session_state["selected_dam"] = dam_row["dam_key"]
            st.caption(f"Selected {dam_row['name']} — see the Reservoirs tab below.")

        elif layer == "salinity" and point_index is not None and 0 <= point_index < len(salinity_plotted):
            site = salinity_plotted.iloc[point_index]
            st.caption(f"{site['desc']}: mean TDS {site['tds_mean']:,.0f} mg/L — see the Salinity tab below.")

        elif layer == "et_grid" and point_index is not None and 0 <= point_index < len(et_grid):
            cell = et_grid.iloc[point_index]
            st.caption(f"Grid cell {cell['lat']:.3f}, {cell['lon']:.3f}: {cell['aet_mm_yr']:,.0f} mm/yr actual ET — see the Climate (ET) tab below.")

        elif layer == "gw_calibration" and point_index is not None and 0 <= point_index < len(gw_cal_wells):
            well_row = gw_cal_wells.iloc[point_index]
            st.session_state["selected_gw_cal_well"] = well_row["id"]
            st.caption(f"Selected well {well_row['id']} — see the Groundwater tab below.")

        elif layer == "salt_export" and point_index is not None and 0 <= point_index < len(sal_reach_export):
            reach_row = sal_reach_export.iloc[point_index]
            st.caption(f"Reach {int(reach_row['u'])}: simulated TDS export {reach_row['tds']:,.0f} kg/yr (26-yr mean).")


tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    ["Streamflow", "Flow Duration", "Groundwater", "Reservoirs", "Sediment Yield", "Salinity", "Climate (ET)", "Water Balance"]
)

with tab1:
    st.subheader("Subbasin-scale simulated streamflow")
    selected_subbasin = st.session_state.get("selected_subbasin")
    if selected_subbasin is not None:
        st.caption(f"Active subbasin: {selected_subbasin}")    

    plot_df = pd.DataFrame()
    if selected_subbasin is not None:
        plot_df, station_matches = _subbasin_streamflow_df(selected_subbasin)

        if not station_matches.empty:
            st.write("Matched station(s) for this subbasin:")
            st.dataframe(
                station_matches[["station_id", "name", "site_no", "gis_id", "subbasin"]],
                width="stretch",
            )
        else:
            st.info("No observation station matched to this subbasin.")

    if not plot_df.empty:
        st.plotly_chart(
            _subbasin_streamflow_fig(plot_df, selected_subbasin),
            width="stretch",
            config={"scrollZoom": True},
            key="tab_streamflow_chart",
        )

    if "observed" in plot_df.columns:
        station_metrics = evaluate_metrics(
            obs=plot_df["observed"].to_numpy(dtype=float),
            sim=plot_df["simulated"].to_numpy(dtype=float),
        )

        st.write("### Metrics")
        render_metric_cards(station_metrics)
    else:
        st.info("Metrics not available because no observed streamflow is matched to this subbasin.")

    st.divider()
    st.subheader("Real USGS gauges against the model's best full-period runs")
    st.caption(
        "Monthly flow at 10 real USGS gauges across the basin — main-stem, "
        "reservoir-outlet, and tributary — against the three model runs that "
        "cover the complete 2000–2025 period. Of the many shorter screening runs "
        "tried during development, these are the ones run over the full record. "
        "The comparison itself covers 2002–2007, the common window with cached "
        "observations across every run."
    )

    if not flow_gauges_meta.empty:
        flow_gauge_options = flow_gauges_meta["id"].tolist()
        flow_gauge_labels = dict(zip(flow_gauges_meta["id"], flow_gauges_meta["label"]))
        selected_flow_gauge = st.selectbox(
            "Gauge",
            options=flow_gauge_options,
            format_func=lambda g: flow_gauge_labels.get(g, g),
        )
        selected_flow_runs = st.multiselect(
            "Runs",
            options=FLOW_RUN_KEYS,
            default=FLOW_RUN_KEYS,
            format_func=lambda r: FLOW_RUN_LABELS.get(r, r),
        )

        log_scale = st.checkbox("Log scale (recommended — flow spans orders of magnitude)", value=True)

        if selected_flow_runs:
            st.plotly_chart(
                plot_multirun_timeseries(flow_monthly, selected_flow_gauge, selected_flow_runs, log_scale=log_scale),
                width="stretch",
                key="tab_flow_multirun_chart",
            )

            for run_key in selected_flow_runs:
                run_stats = compute_gauge_stats(flow_monthly, selected_flow_gauge, run_key)
                st.caption(f"**{FLOW_RUN_LABELS.get(run_key, run_key)}**")
                if run_stats is None:
                    st.info("Fewer than 12 overlapping months at this gauge for this run.")
                    continue
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                c1.metric("NSE", f"{run_stats['nse']:.2f}")
                c2.metric("KGE", f"{run_stats['kge']:.2f}")
                c3.metric("PBIAS", f"{run_stats['pbias']:.1f}%")
                c4.metric("R²", f"{run_stats['r2']:.2f}")
                c5.metric("RMSE", f"{run_stats['rmse']:.2f} m³/s")
                c6.metric("n (months)", run_stats["n"])
        else:
            st.info("Pick at least one run to compare.")
    else:
        st.info("No gauge comparison data found for this basin.")

    if selected_subbasin is None:
        st.info("Click a subbasin on the map to view simulated streamflow.")


with tab2:
    st.plotly_chart(plot_fdc(bundle.streamflow_joined), width="stretch", key="tab_fdc_chart")


with tab3:
    st.subheader("Observed against simulated depth to water table")
    st.caption(
        "Every well-year at 51 real USGS/TWDB observation wells: depth to water "
        "table as reported at the well, against the model's own simulated depth "
        "in that well's grid cell. Points on the dashed 1:1 line would be a "
        "perfect match."
    )

    if context.basin_id == "Pecos" and not gw_cal_pairs.empty:
        bias = gw_cal_pairs["sim_depth_m"] - gw_cal_pairs["obs_depth_m"]
        rmse = (bias ** 2).mean() ** 0.5
        within5 = (bias.abs() < 5).mean() * 100

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Wells", gw_cal_pairs["id"].nunique())
        col2.metric("Well-years", len(gw_cal_pairs))
        col3.metric("Bias (sim − obs)", f"{bias.mean():+.1f} m")
        col4.metric("Within 5 m", f"{within5:.0f}%")

        st.plotly_chart(plot_gw_obs_vs_sim_scatter(gw_cal_pairs), width="stretch", key="tab_gwcal_scatter")
        st.caption(
            "Nearly all points sit below the 1:1 line (simulated depth smaller than "
            "observed): the model's water table sits higher/shallower than the real "
            "wells. Turn on **GW accuracy** in the Watershed Map above to see it by "
            "location, or pick a well below for its own record through time."
        )

        gwcal_options = sorted(gw_cal_wells["id"].tolist())
        current_gwcal = st.session_state.get("selected_gw_cal_well", gwcal_options[0])
        if current_gwcal not in gwcal_options:
            current_gwcal = gwcal_options[0]

        selected_gwcal = st.selectbox("Well", options=gwcal_options, index=gwcal_options.index(current_gwcal))
        st.session_state["selected_gw_cal_well"] = selected_gwcal

        well_pairs = gw_cal_pairs[gw_cal_pairs["id"] == selected_gwcal].sort_values("year")
        st.plotly_chart(
            plot_gw_well_timeseries(well_pairs, selected_gwcal),
            width="stretch",
            key="tab_gwcal_well_chart",
        )
        st.caption(
            "Caveats: a well is a point and the model cell averages several km²; the "
            "model has one soil/aquifer layer, so deep or confined wells cannot match. "
            "Well-years beyond 130 m depth to water (either observed or simulated) "
            "are excluded as not comparable at this resolution."
        )
    else:
        st.info("No observed-vs-simulated well data found for this basin.")

    st.divider()
    st.subheader("Other real groundwater monitoring wells")
    st.caption(
        "60 more real USGS NWIS / TWDB observation wells over the Pecos gwflow grid — "
        "observed head only, no simulated comparison yet. "
        "Turn on **Groundwater wells** in the Watershed Map above and click one, "
        "or just pick one from the list below."
    )

    if context.basin_id == "Pecos":
        if wells_meta.empty:
            st.info("No well catalog found for this basin.")
        else:
            well_options = wells_meta["id"].tolist()
            well_labels = dict(zip(wells_meta["id"], wells_meta["label"]))
            current_well = st.session_state.get("selected_well", well_options[0])
            if current_well not in well_options:
                current_well = well_options[0]

            selected_well = st.selectbox(
                "Well",
                options=well_options,
                index=well_options.index(current_well),
                format_func=lambda wid: well_labels.get(wid, wid),
            )
            st.session_state["selected_well"] = selected_well

            well_row = wells_meta[wells_meta["id"] == selected_well].iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Source", well_row["source"])
            col2.metric("Readings", int(well_row["n_obs"]))
            col3.metric("Mean head", f"{well_row['mean_head_m']:.1f} m" if pd.notna(well_row["mean_head_m"]) else "NA")
            col4.metric("Well depth", f"{well_row['well_depth_ft']:.0f} ft" if pd.notna(well_row.get("well_depth_ft")) else "NA")

            well_series = wells_ts[wells_ts["well_id"] == selected_well]
            if well_series.empty:
                st.info("No time series available for this well.")
            else:
                st.plotly_chart(
                    plot_well_timeseries(well_series, well_labels.get(selected_well, selected_well)),
                    width="stretch",
                    key="tab_well_chart",
                )
                st.caption(
                    "Source: USGS NWIS / TWDB Groundwater Database, extracted from the "
                    "Reservoir Release Lab's own calibration well catalog."
                )
    else:
        st.info("Real well data is only available for the Pecos basin right now.")


with tab4:
    st.subheader("Real reservoir release &amp; storage (2000–2020)")
    st.caption(
        "The Pecos's 5 major dams — Santa Rosa, Sumner, Brantley, Avalon, Red Bluff — "
        "real monthly release and storage, blended GDROM + USGS gage records. "
        "Turn on **Reservoirs** in the Watershed Map above and click one, or just "
        "pick one from the list below. "
        "See the [Reservoir Release Lab](/Scenarios) to explore release policy interactively."
    )

    if context.basin_id == "Pecos":
        if res_meta.empty:
            st.info("No reservoir catalog found for this basin.")
        else:
            dam_options = res_meta["dam_key"].tolist()
            dam_labels = dict(zip(res_meta["dam_key"], res_meta["name"]))
            current_dam = st.session_state.get("selected_dam", dam_options[0])
            if current_dam not in dam_options:
                current_dam = dam_options[0]

            selected_dam = st.selectbox(
                "Dam",
                options=dam_options,
                index=dam_options.index(current_dam),
                format_func=lambda k: dam_labels.get(k, k),
            )
            st.session_state["selected_dam"] = selected_dam

            dam_series = res_ts[res_ts["dam_key"] == selected_dam]
            if dam_series.empty:
                st.info("No time series available for this dam.")
            else:
                st.plotly_chart(
                    plot_reservoir_timeseries(dam_series, dam_labels.get(selected_dam, selected_dam)),
                    width="stretch",
                    key="tab_reservoir_chart",
                )
                st.caption(
                    "Source: Pecos_USA SWAT+gwflow reservoir model, blended GDROM "
                    "(NM Interstate Stream Commission) + USGS gage records, "
                    "2000–2020 monthly."
                )

            st.divider()
            st.subheader("Observed seasonal pattern vs. the model's best runs")
            st.caption(
                "Mean monthly flow at each dam's outlet gauge, observed against one "
                "selected model run — shows whether the model gets the timing of "
                "releases right, not just the volume. Normalize to compare shape "
                "alone, independent of how much water the run passes overall."
            )

            res_meta_gages = res_meta["flow_gage"].astype(str).str.zfill(8)
            res_gauge_ids = [g for g in res_meta_gages if not flow_gauges_meta.empty and g in set(flow_gauges_meta["id"])]
            if res_gauge_ids:
                res_gauge_labels = dict(zip(res_meta_gages, res_meta["name"]))

                selected_res_gauge = st.selectbox(
                    "Dam outlet gauge",
                    options=res_gauge_ids,
                    format_func=lambda g: res_gauge_labels.get(g, g),
                )
                selected_res_run = st.selectbox(
                    "Run",
                    options=FLOW_RUN_KEYS,
                    format_func=lambda r: FLOW_RUN_LABELS.get(r, r),
                )
                normalize_shape = st.checkbox("Normalize (divide each curve by its own mean)", value=False)

                shape_stats = compute_gauge_stats(flow_monthly, selected_res_gauge, selected_res_run)
                if shape_stats is None:
                    st.info("Fewer than 12 overlapping months at this gauge for this run.")
                else:
                    st.plotly_chart(
                        plot_seasonal_shape(shape_stats, selected_res_run, normalize=normalize_shape),
                        width="stretch",
                        key="tab_res_shape_chart",
                    )
                    c1, c2, c3, c4, c5, c6 = st.columns(6)
                    c1.metric("NSE", f"{shape_stats['nse']:.2f}")
                    c2.metric("KGE", f"{shape_stats['kge']:.2f}")
                    c3.metric("PBIAS", f"{shape_stats['pbias']:.1f}%")
                    c4.metric("R²", f"{shape_stats['r2']:.2f}")
                    c5.metric("RMSE", f"{shape_stats['rmse']:.2f} m³/s")
                    c6.metric("n (months)", shape_stats["n"])
                    st.caption(
                        "This is flow at the dam's USGS outlet gauge (2002–2007) — a "
                        "different record from the release/storage series above."
                    )
            else:
                st.info("No gauge comparison data available for these dams.")
    else:
        st.info("Real reservoir data is only available for the Pecos basin right now.")


with tab5:
    st.subheader("Subbasin-scale simulated sediment")

    selected_subbasin = st.session_state.get("selected_subbasin")

    if selected_subbasin is None:
        st.info("Click a subbasin on the map to view sediment.")
    else:
        st.caption(f"Active subbasin: {selected_subbasin}")

        station_matches = pd.DataFrame()

        if not bundle.stations.empty:
            station_matches = bundle.stations[
                bundle.stations["subbasin"].astype(str) == str(selected_subbasin)
            ].copy()

        matched_station = None
        if not station_matches.empty:
            matched_station = station_matches.iloc[0]

        # Simulated sediment
        sub_df = pd.DataFrame()
        if not bundle.channel_daily.empty:
            sub_df = bundle.channel_daily[
                bundle.channel_daily["gis_id"] == int(selected_subbasin)
            ].copy()

        sim_plot_df = pd.DataFrame(columns=["date", "simulated"])

        if not sub_df.empty:
            sim_plot_df = sub_df[["date", "sed_out"]].copy()
            sim_plot_df = sim_plot_df.rename(columns={"sed_out": "simulated"})

        # Observed sediment
        obs_plot_df = pd.DataFrame(columns=["date", "observed"])

        if matched_station is not None:
            site_no = str(matched_station["site_no"]).strip()
            site_no = site_no.split(".")[0].zfill(8)

            obs_plot_df = read_observed_station_timeseries(
                basin_dir=bundle.basin_dir,
                filename=bundle.observed_data_filename,
                site_no=site_no,
                variable="sediment",
            )

        # Merge
        if not obs_plot_df.empty:
            plot_df = obs_plot_df.merge(sim_plot_df, on="date", how="inner")
        else:
            plot_df = sim_plot_df.copy()

        if not plot_df.empty:
            plot_df = plot_df.sort_values("date").reset_index(drop=True)

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=plot_df["date"],
                    y=plot_df["simulated"],
                    mode="lines",
                    name="Simulated",
                    line=dict(color="brown", width=2),
                )
            )


            if "observed" in plot_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=plot_df["date"],
                        y=plot_df["observed"],
                        mode="markers",
                        name="Observed",
                        marker=dict(
                            symbol="circle",
                            size=7,
                            color="rgba(0,0,0,0)",
                            line=dict(color="red", width=1.5),
                        ),
                    )
                )



            fig.update_layout(
                title=f"Sediment - Subbasin {selected_subbasin}",
                xaxis_title="Date",
                yaxis_title="Sediment (Tons/day)",
                hovermode="x unified",
            )

            st.plotly_chart(
                fig,
                width="stretch",
                config={"scrollZoom": True},
                key="tab_sediment_chart",
            )

            if "observed" in plot_df.columns:
                station_metrics = evaluate_metrics(
                    obs=plot_df["observed"].to_numpy(dtype=float),
                    sim=plot_df["simulated"].to_numpy(dtype=float),
                )

                st.write("### Metrics")
                render_metric_cards(station_metrics)
            else:
                st.info("Metrics not available (no observed sediment data).")

with tab6:
    st.subheader("Real salinity / TDS observation sites")
    st.caption(
        "4,283 real water-quality sampling sites inside the Pecos watershed "
        "(USGS, NMED, TCEQ), compiled in the Houston et al. (2019) USGS Pecos "
        "River Basin Salinity Assessment. Most of this is an **observed-data "
        "inventory** — the model's salinity routing only has simulated output "
        "at a handful of gauges so far (below). For a conceptual, interactive "
        "treatment of salinity transport in the meantime, see the "
        "[Salinity Lab](/Water_Quality). Turn on **Salinity sites** in the "
        "Watershed Map above to see them plotted."
    )

    if context.basin_id == "Pecos":
        if salinity_sites.empty:
            st.info("No salinity site catalog found for this basin.")
        else:
            n_sites = len(salinity_sites)
            n_tds = int(salinity_sites["tds_mean"].notna().sum())
            n_iso = int((salinity_sites["n_iso_samples"] > 0).sum())
            n_saline = int((salinity_sites["tds_mean"] > 6000).sum())
            median_tds = salinity_sites["tds_mean"].median()
            max_tds = salinity_sites["tds_mean"].max()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Sampling sites", f"{n_sites:,}")
            col2.metric("With direct TDS", f"{n_tds:,}")
            col3.metric("With isotope tracers", f"{n_iso:,}")
            col4.metric("Sites > 6,000 mg/L", f"{n_saline:,}")

            col_a, col_b = st.columns(2)
            col_a.metric("Median TDS (all sites w/ reading)", f"{median_tds:,.0f} mg/L")
            col_b.metric("Highest single reading", f"{max_tds:,.0f} mg/L")

            st.plotly_chart(plot_tds_distribution(salinity_sites), width="stretch", key="tab_salinity_hist")

            st.caption(
                "Source: Houston, J.R. et al. (2019), USGS Pecos River Basin Salinity "
                "Assessment (DOI: 10.5066/F7DB800T). Values are historical grab-sample "
                "TDS/specific-conductance readings, not a continuous or model-simulated series."
            )
    else:
        st.info("Real salinity site data is only available for the Pecos basin right now.")

    st.divider()
    st.subheader("Real salinity observed against simulated")
    st.caption(
        "Real Water Quality Portal grab samples against the model's own annual "
        "flux-weighted concentration, at the 6 USGS gauges where the model's "
        "channel salt routing has simulated output. Pick a gauge and a "
        "constituent; hover a point for its date/value."
    )

    if context.basin_id == "Pecos" and not sal_station_meta.empty:
        sal_station_options = sal_station_meta["site"].tolist()
        sal_station_labels = dict(zip(sal_station_meta["site"], sal_station_meta["station"]))

        col_sal1, col_sal2 = st.columns(2)
        with col_sal1:
            selected_sal_site = st.selectbox(
                "Station",
                options=sal_station_options,
                format_func=lambda s: sal_station_labels.get(s, s),
            )
        with col_sal2:
            selected_constituent = st.selectbox(
                "Constituent",
                options=["cl", "so4", "tds"],
                format_func=lambda c: {"cl": "Chloride", "so4": "Sulfate", "tds": "TDS"}[c],
            )

        st.plotly_chart(
            plot_station_obs_vs_sim(sal_obs, sal_sim, selected_sal_site, selected_constituent),
            width="stretch",
            key="tab_salinity_obs_sim_chart",
        )

        overlap_years = sal_sim[(sal_sim["site"] == selected_sal_site) & (sal_sim["constituent"] == selected_constituent)]["year"].nunique()
        station_row = sal_station_meta[sal_station_meta["site"] == selected_sal_site].iloc[0]
        n_obs = int(station_row[f"n_{selected_constituent}"])
        st.caption(
            f"{sal_station_labels.get(selected_sal_site, selected_sal_site)}: {n_obs:,} observed samples "
            f"(site {selected_sal_site}), full period of record. Simulated: {overlap_years} years "
            "(v52_prod, annual flux-weighted)."
        )

    st.divider()
    st.subheader("Where the salt comes from")
    st.caption(
        "Mean annual chloride load, simulated: groundwater export to streams "
        "against the basin's two mapped point sources. Chloride and sulfate "
        "follow the same pathway in this model (same initial-condition bands)."
    )

    if context.basin_id == "Pecos" and not sal_contrib.empty:
        contrib_row = sal_contrib.iloc[0].to_dict()
        st.plotly_chart(plot_source_contribution(contrib_row), width="stretch", key="tab_salinity_contrib_chart")
        gw_share = contrib_row["groundwater_t_yr"] / sum(contrib_row.values()) * 100
        st.caption(
            f"Groundwater accounts for ~{gw_share:.0f}% of mapped chloride export in this "
            "model — roughly 7× the two point sources combined."
        )


with tab7:
    st.subheader("Basin water balance — precipitation &amp; evapotranspiration")
    st.caption(
        "Real gridded climate data (TerraClimate, Abatzoglou et al. 2018), averaged "
        "over ~6,300 grid cells covering the Pecos basin, monthly, 2000–2020. This is "
        "an independent remote-sensing/reanalysis product — not a SWAT+gwflow model "
        "output — included here as basin-wide climate context alongside the "
        "streamflow and groundwater records above."
    )

    if context.basin_id == "Pecos":
        et_df = read_et_basin_monthly(bundle.basin_dir)

        if et_df.empty:
            st.info("No basin climate record found for this basin.")
        else:
            mean_ppt = et_df["ppt_mm"].mean() * 12
            mean_aet = et_df["aet_mm"].mean() * 12
            pct_closed = mean_aet / mean_ppt * 100 if mean_ppt else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Mean annual precipitation", f"{mean_ppt:,.0f} mm/yr")
            col2.metric("Mean annual actual ET", f"{mean_aet:,.0f} mm/yr")
            col3.metric("ET / precipitation", f"{pct_closed:.0f}%")

            st.plotly_chart(plot_et_water_balance(et_df), width="stretch", key="tab_et_chart")

            st.caption(
                f"Source: TerraClimate monthly climate data (Abatzoglou et al. 2018), "
                f"averaged over {6300:,} grid cells. Nearly all incoming precipitation "
                "leaves the basin as evapotranspiration — a key reason streamflow is so "
                "limited relative to basin area, and a factor in the Pecos's high "
                "residual salinity (see [Hydrology](/Hydrology))."
            )

        if not et_grid.empty:
            st.subheader("Spatial pattern")
            st.caption(
                "Same TerraClimate data, but per grid cell (2000–2020 annual normal) "
                "instead of basin-averaged. Turn on **ET grid** in the Watershed Map "
                "above to see it mapped, and click a cell for its exact value."
            )
            st.plotly_chart(plot_et_grid_distribution(et_grid), width="stretch", key="tab_et_grid_hist")

        if not et_spatial.empty:
            st.divider()
            st.subheader("Model vs. remote-sensing ET, 2010–2019")
            st.caption(
                "The model's own ET (HRU + groundwater ET, run v33) against a real "
                "remote-sensing product, at 1,148 0.1° grid cells. Green means the "
                "model evaporates more than the product, brown means less."
            )
            product_choice = st.radio(
                "Compare against",
                options=["ssebop_et_mm", "terraclimate_et_mm"],
                format_func=lambda c: "SSEBop (MODIS, energy balance)" if c == "ssebop_et_mm" else "TerraClimate",
                horizontal=True,
            )
            product_label = "SSEBop" if product_choice == "ssebop_et_mm" else "TerraClimate"

            et_spatial_diff = et_spatial.assign(diff_mm=et_spatial["model_et_mm"] - et_spatial[product_choice])
            shared_cmax = max(et_spatial["model_et_mm"].max(), et_spatial[product_choice].max())

            col_m, col_p, col_d = st.columns(3)
            with col_m:
                st.plotly_chart(
                    plot_et_spatial_map(et_spatial, "model_et_mm", "Model ET", shared_cmax=shared_cmax),
                    width="stretch", key="tab_et_spatial_model",
                )
            with col_p:
                st.plotly_chart(
                    plot_et_spatial_map(et_spatial, product_choice, f"{product_label} ET", shared_cmax=shared_cmax),
                    width="stretch", key="tab_et_spatial_product",
                )
            with col_d:
                st.plotly_chart(
                    plot_et_spatial_map(et_spatial_diff, "diff_mm", "Model − product", diverging=True),
                    width="stretch", key="tab_et_spatial_diff",
                )

            spatial_stats = compute_et_spatial_stats(et_spatial["model_et_mm"], et_spatial[product_choice])
            if spatial_stats:
                c3, c4, c5 = st.columns(3)
                c3.metric("PBIAS", f"{spatial_stats['pbias']:.1f}%")
                c4.metric("R²", f"{spatial_stats['r2']:.2f}")
                c5.metric("RMSE", f"{spatial_stats['rmse']:.1f} mm")
                st.caption(f"n = {spatial_stats['n']:,} grid cells. Spatial pairs, not a time series.")
    else:
        st.info("Real basin climate data is only available for the Pecos basin right now.")


with tab8:
    st.subheader("Annual water balance (SWAT+gwflow model, 2000–2025)")
    st.caption(
        "Where the model sends water each year, at the whole-basin scale: "
        "precipitation in, soil water, the surface/lateral/groundwater flow that "
        "reaches the stream network, the exchange between the stream and the "
        "aquifer, and a relative groundwater storage trend. This is the model's "
        "own simulated balance, not an observed record."
    )

    if context.basin_id == "Pecos" and not water_balance.empty:
        st.plotly_chart(plot_annual_water_balance(water_balance), width="stretch", key="tab_wb_chart")
        st.caption(
            "Groundwater discharge to the stream (dark blue, panel 3) is larger and "
            "steadier than recharge or seepage in the opposite direction in almost "
            "every year: the aquifer is a consistent net source of baseflow to the "
            "channel network over the full 26-year record, not a sink."
        )
    else:
        st.info("No water balance record found for this basin.")


st.subheader("Summary table")
summary_df = compute_basic_summary(bundle.streamflow_joined)
st.dataframe(summary_df, width="stretch")
