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

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from core.io.filesystem import read_csv

RUN_KEYS = ["v52prod", "v33", "v30ext"]
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


@st.cache_data
def read_model_subbasins(basin_dir: Path) -> dict | None:
    """The production model's own 309 subbasins (the delineation SWAT+ ran on),
    each tagged with the channel at its outlet."""
    path = basin_dir / "spatial" / "subbasins_model.geojson"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data
def read_subbasin_outlet_flow(basin_dir: Path) -> pd.DataFrame:
    """Simulated monthly flow (m3/s) at each subbasin's outlet channel, 2002-2007,
    for the three full-period runs. There are no observations at subbasin
    outlets -- only at the gauges -- so these are model-only series."""
    path = basin_dir / "subbasin_outlet_flow_monthly.csv"
    if not path.exists():
        return pd.DataFrame(columns=["subbasin", "month"])
    return read_csv(path)


@st.cache_data
def read_streamflow_stations_all(basin_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The 10 curated gauges plus the other USGS stations on the river network.

    The extra stations come from the daily USGS record (monthly means, 2000-2025)
    and are matched to the model channel nearest each station, so the same
    observed-versus-simulated comparison works for them. Canals and springs are
    left out (the model has no such reach), as are stations farther than 1.5 km
    from any modelled channel. Returns (stations, monthly) in the same layout as
    read_streamflow_gauges_meta / read_streamflow_monthly_obs_sim.
    """
    gauges = read_streamflow_gauges_meta(basin_dir).copy()
    monthly = read_streamflow_monthly_obs_sim(basin_dir).copy()
    gauges["group"] = gauges["group"].fillna("main")
    meta_path = basin_dir / "streamflow_stations_meta.csv"
    mon_path = basin_dir / "streamflow_stations_monthly.csv"
    if not (meta_path.exists() and mon_path.exists()):
        return gauges, monthly
    extra = read_csv(meta_path, dtype={"site_no": str})
    extra_monthly = read_csv(mon_path, dtype={"site_no": str})
    extra_gauges = pd.DataFrame({
        "id": extra["site_no"],
        "label": extra["name"].str.title().str.replace(r"\bNr\b", "near", regex=True).str.replace(r"\bRv\b", "River", regex=True).str.replace(r"\bNm\b", "NM", regex=True).str.replace(r"\bTx\b", "TX", regex=True),
        "ch": extra["channel_gis_id"].astype(str),
        "group": "extra",
        "lat": extra["lat"], "lon": extra["lon"],
        "snap_m": extra["snap_m"], "drain_km2": extra["drain_km2"],
    })
    gauges = pd.concat([gauges, extra_gauges], ignore_index=True)
    monthly = pd.concat([monthly, extra_monthly.rename(columns={"site_no": "gauge_id"})], ignore_index=True)
    return gauges, monthly
