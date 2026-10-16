"""Readers for the gridded groundwater / salinity maps (2010-2024).

All three files come from the production run's monthly-output rerun (see
resources/txpwc/basins/Pecos):

- groundwater_by_month.csv.gz   0.1-deg cells x month: recharge (mm), depth to the water table (m)
                                and the net groundwater-river exchange (m3/s, positive = the aquifer
                                feeds the river, negative = the river loses water to the aquifer;
                                empty where the cell has no stream contact).
- river_salinity_by_month.csv.gz  one row per river reach and month: total dissolved salts (mg/L, the sum
                                of the eight modelled ions), empty when the reach is dry; with the
                                reach midpoint.
- soil_salt_by_year.csv         mass of salt held in the soil (kg/ha), 0.1-deg cells x year.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.io.filesystem import read_csv


@st.cache_data
def read_groundwater_by_month(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "groundwater_by_month.csv.gz"
    if not path.exists():
        return pd.DataFrame(columns=["year", "month", "lat", "lon", "recharge_mm", "wt_depth_m", "stream_exchange_m3s"])
    return read_csv(path)


@st.cache_data
def read_river_salinity_by_month(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "river_salinity_by_month.csv.gz"
    if not path.exists():
        return pd.DataFrame(columns=["year", "month", "gis_id", "tds_mgL", "lat", "lon"])
    return read_csv(path)


@st.cache_data
def read_soil_salt_by_year(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "soil_salt_by_year.csv"
    if not path.exists():
        return pd.DataFrame(columns=["year", "lat", "lon", "soil_salt_kgha"])
    return read_csv(path)
