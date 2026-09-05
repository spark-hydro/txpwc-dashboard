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
from core.io.climate_reader import read_et_basin_monthly, read_et_grid
from core.plotting.salinity import plot_tds_distribution
from core.plotting.climate import plot_et_water_balance, plot_et_grid_distribution
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
else:
    wells_meta = wells_ts = res_meta = res_ts = salinity_sites = et_grid = pd.DataFrame()


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


def _compact_fig(fig):
    """Shrink an existing figure for the map's small click panel."""
    fig.update_layout(
        title="",
        height=200,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
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
    )

    map_event = st.plotly_chart(
        fig,
        use_container_width=True,
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

            with st.container(border=True):
                st.markdown(f"**Subbasin {subbasin_id} — simulated streamflow**")
                sf_plot_df, _ = _subbasin_streamflow_df(subbasin_id)
                if sf_plot_df.empty:
                    st.caption("No simulated series available for this subbasin.")
                else:
                    st.plotly_chart(
                        _subbasin_streamflow_fig(sf_plot_df, subbasin_id, compact=True),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="map_panel_subbasin_compact",
                    )
                    with st.expander("See full-size chart & details"):
                        st.plotly_chart(
                            _subbasin_streamflow_fig(sf_plot_df, subbasin_id, compact=False),
                            use_container_width=True,
                            key="map_panel_subbasin_full",
                        )
                        st.caption("Also on the Streamflow tab below, with sediment/metrics context.")

        elif layer == "wells" and point_index is not None and 0 <= point_index < len(wells_meta):
            well_row = wells_meta.iloc[point_index]
            st.session_state["selected_well"] = well_row["id"]

            with st.container(border=True):
                st.markdown(f"**{well_row['label']} — water table depth**")
                well_series = wells_ts[wells_ts["well_id"] == well_row["id"]]
                if well_series.empty:
                    st.caption("No time series available for this well.")
                else:
                    st.plotly_chart(
                        _compact_fig(plot_well_timeseries(well_series, well_row["label"])),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="map_panel_well_compact",
                    )
                    with st.expander("See full-size chart & details"):
                        st.plotly_chart(
                            plot_well_timeseries(well_series, well_row["label"]),
                            use_container_width=True,
                            key="map_panel_well_full",
                        )
                        col_w1, col_w2, col_w3 = st.columns(3)
                        col_w1.metric("Source", well_row["source"])
                        col_w2.metric("Readings", int(well_row["n_obs"]))
                        col_w3.metric("Mean head", f"{well_row['mean_head_m']:.1f} m" if pd.notna(well_row["mean_head_m"]) else "NA")

        elif layer == "reservoirs" and point_index is not None and 0 <= point_index < len(res_meta):
            dam_row = res_meta.iloc[point_index]
            st.session_state["selected_dam"] = dam_row["dam_key"]

            with st.container(border=True):
                st.markdown(f"**{dam_row['name']} — release & storage**")
                dam_series = res_ts[res_ts["dam_key"] == dam_row["dam_key"]]
                if dam_series.empty:
                    st.caption("No time series available for this dam.")
                else:
                    st.plotly_chart(
                        _compact_fig(plot_reservoir_timeseries(dam_series, dam_row["name"])),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key="map_panel_dam_compact",
                    )
                    with st.expander("See full-size chart & details"):
                        st.plotly_chart(
                            plot_reservoir_timeseries(dam_series, dam_row["name"]),
                            use_container_width=True,
                            key="map_panel_dam_full",
                        )

        elif layer == "salinity" and point_index is not None and 0 <= point_index < len(salinity_plotted):
            site = salinity_plotted.iloc[point_index]
            with st.container(border=True):
                st.markdown(f"**{site['desc']}**")
                st.caption(
                    "No continuous time series exists per site (grab samples only) -- "
                    "shown here is where this site's mean TDS falls in the basin-wide distribution."
                )
                st.plotly_chart(
                    plot_tds_distribution(salinity_sites, highlight_tds=site["tds_mean"], compact=True),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key="map_panel_salinity_compact",
                )
                with st.expander("See full-size chart & details"):
                    st.plotly_chart(
                        plot_tds_distribution(salinity_sites, highlight_tds=site["tds_mean"]),
                        use_container_width=True,
                        key="map_panel_salinity_full",
                    )
                    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                    col_s1.metric("Mean TDS", f"{site['tds_mean']:,.0f} mg/L")
                    col_s2.metric("Range", f"{site['tds_min']:,.0f}–{site['tds_max']:,.0f}")
                    col_s3.metric("TDS samples", int(site["n_tds"]))
                    col_s4.metric("Source", site["source"])
                    st.caption(
                        f"Isotope samples: {int(site['n_iso_samples'])} · "
                        f"Sampled {site['date_oldest']} to {site['date_newest']}"
                    )

        elif layer == "et_grid" and point_index is not None and 0 <= point_index < len(et_grid):
            cell = et_grid.iloc[point_index]
            with st.container(border=True):
                st.markdown(f"**Grid cell — {cell['lat']:.3f}, {cell['lon']:.3f}**")
                st.caption(
                    "Each cell is a 2000–2020 annual normal (TerraClimate), not a time "
                    "series -- shown here is where this cell falls basin-wide."
                )
                st.plotly_chart(
                    plot_et_grid_distribution(et_grid, highlight_aet=cell["aet_mm_yr"], compact=True),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key="map_panel_et_compact",
                )
                with st.expander("See full-size chart & details"):
                    st.plotly_chart(
                        plot_et_grid_distribution(et_grid, highlight_aet=cell["aet_mm_yr"]),
                        use_container_width=True,
                        key="map_panel_et_full",
                    )
                    st.metric("Actual ET at this cell", f"{cell['aet_mm_yr']:,.0f} mm/yr")


tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["Streamflow", "Flow Duration", "Groundwater", "Reservoirs", "Sediment Yield", "Salinity", "Climate (ET)"]
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
                use_container_width=True,
            )
        else:
            st.info("No observation station matched to this subbasin.")

    if not plot_df.empty:
        st.plotly_chart(
            _subbasin_streamflow_fig(plot_df, selected_subbasin),
            use_container_width=True,
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

    if selected_subbasin is None:
        st.info("Click a subbasin on the map to view simulated streamflow.")


with tab2:
    st.plotly_chart(plot_fdc(bundle.streamflow_joined), use_container_width=True, key="tab_fdc_chart")


with tab3:
    st.subheader("Real groundwater monitoring wells")
    st.caption(
        "60 real USGS NWIS / TWDB observation wells over the Pecos gwflow grid — "
        "independent of the small demo dataset used elsewhere on this page. "
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
                    use_container_width=True,
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
                    use_container_width=True,
                    key="tab_reservoir_chart",
                )
                st.caption(
                    "Source: Pecos_USA SWAT+gwflow reservoir model, blended GDROM "
                    "(NM Interstate Stream Commission) + USGS gage records, "
                    "2000–2020 monthly."
                )
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
                use_container_width=True,
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
        "River Basin Salinity Assessment. SWAT+gwflow does not yet include a "
        "salinity-transport module, so this is an **observed-data inventory**, "
        "not an observed-vs-simulated comparison — that will follow once the "
        "module is added and calibrated (see the [Hydrology](/Hydrology) roadmap). "
        "For a conceptual, interactive treatment of salinity transport in the "
        "meantime, see the [Salinity Lab](/Water_Quality). Turn on **Salinity "
        "sites** in the Watershed Map above to see them plotted."
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

            st.plotly_chart(plot_tds_distribution(salinity_sites), use_container_width=True, key="tab_salinity_hist")

            st.caption(
                "Source: Houston, J.R. et al. (2019), USGS Pecos River Basin Salinity "
                "Assessment (DOI: 10.5066/F7DB800T). Values are historical grab-sample "
                "TDS/specific-conductance readings, not a continuous or model-simulated series."
            )
    else:
        st.info("Real salinity site data is only available for the Pecos basin right now.")


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

            st.plotly_chart(plot_et_water_balance(et_df), use_container_width=True, key="tab_et_chart")

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
            st.plotly_chart(plot_et_grid_distribution(et_grid), use_container_width=True, key="tab_et_grid_hist")
    else:
        st.info("Real basin climate data is only available for the Pecos basin right now.")



st.subheader("Summary table")
summary_df = compute_basic_summary(bundle.streamflow_joined)
st.dataframe(summary_df, use_container_width=True)
