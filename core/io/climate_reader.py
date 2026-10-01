"""Reader for real basin-wide evapotranspiration / water-balance data.

Data source: TerraClimate monthly gridded climate data (Abatzoglou et
al. 2018), averaged over ~6,300 grid cells covering the Pecos basin,
2000-2020 -- actual ET, potential ET, and precipitation. Extracted
from the Reservoir Release Lab into a plain CSV -- see
resources/txpwc/basins/Pecos/et_basin_monthly.csv.

This is an independent remote-sensing/reanalysis product, not a
SWAT+gwflow model output -- useful context for the basin's water
balance, not an observed-vs-simulated comparison.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.io.filesystem import read_csv


@st.cache_data
def read_et_basin_monthly(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "et_basin_monthly.csv"
    if not path.exists():
        return pd.DataFrame(columns=["month", "aet_mm", "pet_mm", "ppt_mm"])

    df = read_csv(path)
    df["date"] = pd.to_datetime(df["month"], format="%Y-%m")
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data
def read_et_grid(basin_dir: Path) -> pd.DataFrame:
    """6,300 TerraClimate grid cells covering the basin, mean actual ET (mm/yr)."""
    path = basin_dir / "et_grid.csv"
    if not path.exists():
        return pd.DataFrame(columns=["lat", "lon", "aet_mm_yr"])
    return read_csv(path)


@st.cache_data
def read_et_spatial_comparison(basin_dir: Path) -> pd.DataFrame:
    """1,148 0.1-deg grid cells: the model's own ET (HRU + groundwater, run
    v33) against two remote-sensing products, SSEBop and TerraClimate, mean
    annual mm/yr, 2010-2019."""
    path = basin_dir / "et_spatial_comparison.csv"
    if not path.exists():
        return pd.DataFrame(columns=["lat", "lon", "model_et_mm", "ssebop_et_mm", "terraclimate_et_mm"])
    return read_csv(path)
