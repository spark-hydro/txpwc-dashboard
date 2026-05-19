import streamlit as st
from components.cards import render_metric_cards
from components.sidebar import render_sidebar
from core.metrics.performance import compute_basic_summary
from core.plotting.duration_curves import plot_fdc
from core.plotting.groundwater import plot_groundwater_scatter
from core.plotting.hydrographs import plot_streamflow_hydrograph
from core.plotting.maps import plot_station_map
from core.services.performance_service import load_performance_bundle
from core.plotting.maps import plot_station_map, plot_subbasins_map, add_station_geojson_points
from streamlit_plotly_events import plotly_events
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

    selected_var = None
    if numeric_candidates:
        selected_var = st.selectbox(
            "Color subbasins by",
            options=numeric_candidates,
            index=numeric_candidates.index(default_var) if default_var in numeric_candidates else 0,
            key="shared_map_color_var",
        )

    fig = plot_subbasins_map(bundle.subbasins_geojson, color_field=selected_var)

    if bundle.stations is not None and not bundle.stations.empty:
        fig = add_station_geojson_points(fig, bundle.stations_geojson)


    selected_points = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=600,
        override_width="100%",
    )

    # st.plotly_chart(
    #     fig,
    #     use_container_width=True,
    #     config={"scrollZoom": True},
    # )
    # selected_points = []


    if selected_points:
        clicked = selected_points[0]

        if clicked.get("curveNumber") == 0 and bundle.subbasins_geojson is not None:
            features = bundle.subbasins_geojson.get("features", [])
            point_index = clicked.get("pointIndex")

            if point_index is not None and 0 <= point_index < len(features):
                props = features[point_index].get("properties", {})
                subbasin_id = props.get("Subbasin")

                st.session_state["selected_subbasin"] = subbasin_id
                st.success(f"Selected subbasin from map: {subbasin_id}")


tab1, tab2, tab3, tab4 = st.tabs(
    ["Streamflow", "Groundwater", "Sediment Yield", "Salinity"]
)

with tab1:
    st.subheader("Subbasin-scale simulated streamflow")
    selected_subbasin = st.session_state.get("selected_subbasin")
    if selected_subbasin is not None:
        st.caption(f"Active subbasin: {selected_subbasin}")    

    station_matches = pd.DataFrame()
    if selected_subbasin is not None and not bundle.stations.empty:
        station_matches = bundle.stations[
            bundle.stations["subbasin"].astype(str) == str(selected_subbasin)
        ].copy()

        if not station_matches.empty:
            st.write("Matched station(s) for this subbasin:")
            st.dataframe(
                station_matches[["station_id", "name", "site_no", "gis_id", "subbasin"]],
                use_container_width=True,
            )
        else:
            st.info("No observation station matched to this subbasin.")

    matched_station = None
    if not station_matches.empty:
        matched_station = station_matches.iloc[0]

    # Create the simulated subbasin series first, regardless of whether a station exists.
    sub_df = pd.DataFrame()

    if selected_subbasin is not None and not bundle.channel_daily.empty:
        sub_df = bundle.channel_daily[
            bundle.channel_daily["gis_id"] == int(selected_subbasin)
        ].copy()

    # Turn that simulated subbasin table into a plotting table for streamflow.
    sim_plot_df = pd.DataFrame(columns=["date", "simulated"])

    if not sub_df.empty:
        sim_plot_df = sub_df[["date", "flo_out"]].copy()
        sim_plot_df = sim_plot_df.rename(columns={"flo_out": "simulated"})

    # Load the observed series only when a matched station exists.
    obs_plot_df = pd.DataFrame(columns=["date", "observed"])

    if matched_station is not None:
        site_no = str(matched_station["site_no"]).strip()
        site_no = site_no.split(".")[0].zfill(8)

        obs_plot_df = read_observed_station_timeseries(
            basin_dir=bundle.basin_dir,
            filename=bundle.observed_data_filename,
            site_no=site_no,
            variable="flow",
        )

    # Create one unified plot_df for the Streamflow tab.
    plot_df = pd.DataFrame()
    if not obs_plot_df.empty:
        plot_df = obs_plot_df.merge(sim_plot_df, on="date", how="inner")
    else:
        plot_df = sim_plot_df.copy()

    if not plot_df.empty:
        plot_df = plot_df.sort_values("date").reset_index(drop=True)

    # Plot plot_df in one figure, with observed shown only when available.
    if not plot_df.empty:
        fig_sub = go.Figure()

        fig_sub.add_trace(
            go.Scatter(
                x=plot_df["date"],
                y=plot_df["simulated"],
                mode="lines",
                name="Simulated",
                # line=dict(width=2),
            )
        )

        if "observed" in plot_df.columns:
            fig_sub.add_trace(
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
                    opacity=0.5,
                    ),
                )
            )

        fig_sub.update_layout(
            title=f"Streamflow - Subbasin {selected_subbasin}",
            xaxis_title="Date",
            yaxis_title="Streamflow Discharge (cm³/s)",
            hovermode="x unified"
        )

        st.plotly_chart(fig_sub, use_container_width=True, config={"scrollZoom": True})

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
    st.plotly_chart(plot_fdc(bundle.streamflow_joined), use_container_width=True)


with tab3:
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

with tab4:
    st.info("Salinity analysis will be added here.")



st.subheader("Summary table")
summary_df = compute_basic_summary(bundle.streamflow_joined)
st.dataframe(summary_df, use_container_width=True)
