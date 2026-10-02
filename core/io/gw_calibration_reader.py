"""Readers for observed-vs-simulated depth-to-water-table at real wells.

Data source: 70 real USGS/TWDB observation wells, each with observed depth
to water table (derived from reported head and an estimated cell land-
surface elevation) and the SWAT+gwflow model's own simulated depth
(wt_depth) in the same cell, for the model's extended run. Extracted from
the project's calibration ledger into plain CSVs -- see
resources/txpwc/basins/Pecos/gw_calibration_wells.csv and
resources/txpwc/basins/Pecos/gw_calibration_pairs.csv.

Well-years with an observed or simulated depth beyond 130 m were dropped:
those are deep/confined wells the model's single soil layer cannot
represent, and they dominate the plot's scale without being comparable.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.io.filesystem import read_csv


@st.cache_data
def read_gw_calibration_wells(basin_dir: Path) -> pd.DataFrame:
    """One row per well: location and its mean observed/simulated depth and bias."""
    path = basin_dir / "gw_calibration_wells.csv"
    if not path.exists():
        return pd.DataFrame(columns=["id", "lat", "lon", "n_years", "mean_obs_m", "mean_sim_m", "mean_bias_m"])
    return read_csv(path, dtype={"id": str})


@st.cache_data
def read_gw_calibration_pairs(basin_dir: Path) -> pd.DataFrame:
    """One row per well-year: observed and simulated depth to water table (m bgs)."""
    path = basin_dir / "gw_calibration_pairs.csv"
    if not path.exists():
        return pd.DataFrame(columns=["id", "lat", "lon", "cell", "year", "obs_depth_m", "sim_depth_m"])
    return read_csv(path, dtype={"id": str})
