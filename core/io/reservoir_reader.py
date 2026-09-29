"""Readers for real reservoir (dam) release/storage records.

Data source: the Pecos_USA SWAT+gwflow reservoir model's own calibration
package (real 2000-2020 monthly release and storage, blended GDROM +
USGS gage records per the project's README_calibration.md), extracted
from the Reservoir Release Lab into plain CSVs -- see
resources/txpwc/basins/Pecos/reservoirs_meta.csv and
resources/txpwc/basins/Pecos/reservoirs_monthly.csv.
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
