"""Readers for real reservoir (dam) release/storage records.

Data source: monthly records for the five Pecos reservoirs, 2000-2025 -- see
resources/txpwc/basins/Pecos/reservoirs_meta.csv and reservoirs_monthly.csv.

reservoirs_monthly.csv columns:
  release_Mm3       monthly release volume. 2000-2020 is the model calibration package's blend of
                    GDROM and USGS gauge records (unchanged); 2021-2025 is the USGS gauge below the dam.
  release_source    which of those two it is, month by month.
  release_obs_Mm3   observed release throughout 2000-2025: the USGS gauge just below each dam
                    (the river release; at Avalon the canal diversion is not included).
  storage_af        monthly mean storage. Reclamation (RISE) for Avalon, Brantley, Sumner and Santa Rosa
                    (to 2020-05); TWDB for Red Bluff; Santa Rosa from 2020-06 is derived from the USGS
                    lake level through the post-2017 elevation-storage relation (storage_source says which).
  release_reclamation_total_Mm3
                    Reclamation's total release (river plus canals) for the New Mexico dams.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.io.filesystem import read_csv


@st.cache_data
def read_reservoirs_meta(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "reservoirs_meta.csv"
    if not path.exists():
        return pd.DataFrame(columns=["dam_key", "name", "state", "lat", "lon", "elev_m", "flow_gage", "storage_gage"])
    return read_csv(path)


@st.cache_data
def read_reservoirs_monthly(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "reservoirs_monthly.csv"
    if not path.exists():
        return pd.DataFrame(columns=["dam_key", "month", "release_Mm3", "storage_af"])

    df = read_csv(path)
    df["date"] = pd.to_datetime(df["month"], format="%Y-%m")
    return df.sort_values(["dam_key", "date"]).reset_index(drop=True)
