from __future__ import annotations

import streamlit as st

from config.settings import RESOURCES_DIR
from core.io.txpwc_reader import (
    get_basin_dir,
    read_streamflow_observed,
    read_streamflow_simulated,
    read_groundwater,
    read_stations,
    join_streamflow,
    read_stations_geojson,
    read_channel_daily_parquet
)

from core.io.txpwc_reader import read_subbasins_geojson
from core.metrics.performance import compute_streamflow_metrics
from core.models.schema import AppContext, PerformanceBundle
from core.io.txpwc_reader import read_station_timeseries
from core.services.catalog import get_basin_config


@st.cache_data
def load_performance_bundle(context: AppContext) -> PerformanceBundle:
    basin_dir = get_basin_dir(RESOURCES_DIR, context.basin_id)
    basin_config = get_basin_config(context.basin_id)
    observed_data_filename = basin_config.get("observed_data")
    observed = read_streamflow_observed(basin_dir)
    simulated = read_streamflow_simulated(basin_dir, context.scenario_id)
    joined = join_streamflow(observed, simulated)
    groundwater = read_groundwater(basin_dir)
    stations = read_stations(basin_dir)
    metrics = compute_streamflow_metrics(joined)
    station_timeseries=read_station_timeseries(basin_dir)
    stations_geojson = read_stations_geojson(basin_dir)
    channel_daily = read_channel_daily_parquet(basin_dir)
    

    return PerformanceBundle(
        context=context,
        basin_dir=basin_dir,
        observed_streamflow=observed,
        simulated_streamflow=simulated,
        streamflow_joined=joined,
        groundwater=groundwater,
        stations=stations,
        metrics=metrics,
        subbasins_geojson=read_subbasins_geojson(basin_dir),
        station_timeseries=station_timeseries,
        stations_geojson=stations_geojson,
        observed_data_filename=observed_data_filename,
        channel_daily=channel_daily,
    )
