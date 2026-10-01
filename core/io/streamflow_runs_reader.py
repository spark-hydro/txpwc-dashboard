"""Readers for real USGS gauge records against the model's own best runs.

Data source: 10 real USGS streamflow gauges across the basin (both main-
stem/reservoir-outlet gauges and tributary gauges), observed monthly flow
against the three SWAT+gwflow runs that cover the model's full 2000-2025
period (of the many shorter screening runs tried during development,
these are the only ones run the complete record). Extracted from the
project's calibration ledger into plain CSVs -- see
resources/txpwc/basins/Pecos/streamflow_gauges_meta.csv and
resources/txpwc/basins/Pecos/streamflow_monthly_obs_sim.csv.

The monthly comparison itself only covers 2002-2007 (72 months): that is
the window with observed records cached for every run in the ledger,
including the short screening runs this project compared the long runs
against, so it stays the common window here too.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.io.filesystem import read_csv

RUN_KEYS = ["v30ext", "v33", "v52prod"]
RUN_LABELS = {
    "v30ext": "Base run (2000–2025)",
    "v33": "Improved channel geometry (2000–2025)",
    "v52prod": "Production run (2000–2025)",
}


@st.cache_data
def read_streamflow_gauges_meta(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "streamflow_gauges_meta.csv"
    if not path.exists():
        return pd.DataFrame(columns=["id", "label", "ch", "group", "lat", "lon"])
    return read_csv(path, dtype={"id": str, "ch": str})


@st.cache_data
def read_streamflow_monthly_obs_sim(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "streamflow_monthly_obs_sim.csv"
    if not path.exists():
        return pd.DataFrame(columns=["gauge_id", "month"])
    return read_csv(path, dtype={"gauge_id": str})
