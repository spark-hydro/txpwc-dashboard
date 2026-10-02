"""Readers for the model's own simulated salinity, against real observations.

Data sources, all extracted from the project's salinity calibration ledger
into plain CSVs (resources/txpwc/basins/Pecos/salinity_*.csv):

- 6 USGS gauges with both real Water Quality Portal grab samples
  (chloride/sulfate/TDS, mg/L, full period of record) and the model's own
  annual flux-weighted concentration (v52_prod, 2000-2025) -- the first
  real observed-vs-simulated salinity comparison available for this basin.
- The basin-scale annual chloride load by source (groundwater export vs.
  the two mapped point sources, Malaga Bend brine and produced water).
- Simulated salt export (chloride/sulfate/TDS, 26-yr mean) at 2,400
  routed channel reaches.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.io.filesystem import read_csv


@st.cache_data
def read_salinity_station_meta(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "salinity_station_meta.csv"
    if not path.exists():
        return pd.DataFrame(columns=["station", "site", "lat", "lon", "n_cl", "n_so4", "n_tds"])
    return read_csv(path, dtype={"site": str})


@st.cache_data
def read_salinity_station_observed(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "salinity_station_observed.csv"
    if not path.exists():
        return pd.DataFrame(columns=["station", "site", "constituent", "date", "value_mgL"])
    df = read_csv(path, dtype={"site": str})
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def read_salinity_station_simulated(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "salinity_station_simulated.csv"
    if not path.exists():
        return pd.DataFrame(columns=["station", "site", "constituent", "year", "value_mgL"])
    return read_csv(path, dtype={"site": str})


@st.cache_data
def read_salinity_source_contrib(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "salinity_source_contrib.csv"
    if not path.exists():
        return pd.DataFrame(columns=["groundwater_t_yr", "malaga_t_yr", "prodwater_t_yr"])
    return read_csv(path)


@st.cache_data
def read_salinity_reach_export(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "salinity_reach_export.csv"
    if not path.exists():
        return pd.DataFrame(columns=["u", "lat", "lon", "cl", "so4", "tds"])
    return read_csv(path)
