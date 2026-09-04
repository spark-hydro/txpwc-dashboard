"""Reader for real salinity/TDS observation sites.

Data source: 4,283 real water-quality sampling sites inside the Pecos
watershed (USGS, NMED, TCEQ), compiled in the Houston et al. (2019) USGS
Pecos River Basin Salinity Assessment (DOI 10.5066/F7DB800T), extracted
from the Reservoir Release Lab into a plain CSV -- see
resources/txpwc/basins/Pecos/salinity_sites.csv.

This is historical grab-sample data (TDS, specific conductance, and for
a subset, stable-isotope tracers). SWAT+gwflow does not yet include a
salinity/solute-transport module, so there is no simulated series to
compare against -- this is an observed-data inventory, not a
observed-vs-simulated skill assessment.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.io.filesystem import read_csv

_COLUMNS = [
    "id", "desc", "source", "lat", "lon", "type_cd",
    "n_samples", "n_tds", "n_cond", "n_ion_samples", "n_iso_samples",
    "tds_min", "tds_max", "tds_mean", "date_oldest", "date_newest",
]


@st.cache_data
def read_salinity_sites(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "salinity_sites.csv"
    if not path.exists():
        return pd.DataFrame(columns=_COLUMNS)
    return read_csv(path)
