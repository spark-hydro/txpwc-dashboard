"""Reader for the SWAT+gwflow model's own annual basin water balance.

Data source: the model's basin-scale annual water-balance ledger (2000-
2025) -- precipitation, soil water, surface runoff, lateral flow,
groundwater discharge to stream, stream seepage to the aquifer, recharge
to the gwflow water table, and a relative groundwater storage trend.
Extracted from the project's own water-balance ledger into a plain CSV --
see resources/txpwc/basins/Pecos/water_balance_annual.csv.

This is the model's simulated water balance, not an observed record --
useful context for where the model sends water each year, not an
observed-vs-simulated comparison.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.io.filesystem import read_csv


@st.cache_data
def read_water_balance_annual(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "water_balance_annual.csv"
    if not path.exists():
        return pd.DataFrame(columns=["yr", "prec", "sw", "surq", "latq", "gwq", "swgw", "perco", "gw"])
    return read_csv(path)
