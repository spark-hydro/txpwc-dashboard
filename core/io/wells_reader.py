"""Readers for real groundwater monitoring-well records.

Data source: 60 real USGS NWIS / TWDB observation wells over the Pecos
gwflow grid, extracted from the Reservoir Release Lab into plain CSVs --
see resources/txpwc/basins/Pecos/groundwater_wells_meta.csv and
resources/txpwc/basins/Pecos/groundwater_wells_timeseries.csv. This is
real head data (m AMSL), independent of the small demo groundwater.csv
used elsewhere on Model Performance.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.io.filesystem import read_csv


@st.cache_data
def read_wells_meta(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "groundwater_wells_meta.csv"
    if not path.exists():
        return pd.DataFrame(columns=["id", "label", "source", "lat", "lon", "n_obs", "mean_head_m"])
    return read_csv(path, dtype={"id": str})


@st.cache_data
def read_wells_timeseries(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "groundwater_wells_timeseries.csv"
    if not path.exists():
        return pd.DataFrame(columns=["well_id", "date", "head_m", "n_readings"])

    df = read_csv(path, dtype={"well_id": str})
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m")
    return df.sort_values(["well_id", "date"]).reset_index(drop=True)
