from __future__ import annotations

from pathlib import Path
import pandas as pd
import json
import streamlit as st


from core.io.filesystem import read_csv


def get_basin_dir(resources_dir: Path, basin_id: str) -> Path:
    return resources_dir / "txpwc" / "basins" / basin_id


@st.cache_data
def read_streamflow_observed(basin_dir: Path) -> pd.DataFrame:
    df = read_csv(basin_dir / "streamflow_observed.csv", parse_dates=["date"])
    df = df.rename(columns={"flow": "flow_obs"})
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data
def read_streamflow_simulated(basin_dir: Path, scenario_id: str) -> pd.DataFrame:
    df = read_csv(basin_dir / f"streamflow_simulated_{scenario_id}.csv", parse_dates=["date"])
    df = df.rename(columns={"flow": "flow_sim"})
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data
def read_groundwater(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "groundwater.csv"
    if not path.exists():
        return pd.DataFrame(columns=["date", "site_id", "observed", "simulated"])
    df = read_csv(path, parse_dates=["date"])
    return df.sort_values(["site_id", "date"]).reset_index(drop=True)

@st.cache_data
def read_stations(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "stations.csv"
    if not path.exists():
        return pd.DataFrame(columns=["station_id", "name", "variable", "lat", "lon", "subbasin", "site_no"])

    df = read_csv(path, dtype={"site_no": str})
    df.columns = df.columns.str.strip()

    if "site_no" in df.columns:
        df["site_no"] = df["site_no"].astype(str).str.strip().str.split(".").str[0].str.zfill(8)

    return df


def join_streamflow(observed: pd.DataFrame, simulated: pd.DataFrame) -> pd.DataFrame:
    merged = observed.merge(simulated, on="date", how="outer")
    return merged.sort_values("date").reset_index(drop=True)

@st.cache_data
def read_subbasins_geojson(basin_dir: Path) -> dict | None:
    geojson_path = basin_dir / "spatial" / "subbasins.geojson"

    if not geojson_path.exists():
        return None

    with geojson_path.open("r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def read_stations_geojson(basin_dir: Path) -> dict | None:
    geojson_path = basin_dir / "spatial" / "stations.geojson"

    if not geojson_path.exists():
        return None

    with geojson_path.open("r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def read_station_timeseries(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "station_timeseries.csv"

    if not path.exists():
        return pd.DataFrame(
            columns=["date", "station_id", "variable", "observed", "simulated"]
        )

    df = read_csv(path, parse_dates=["date"])
    return df.sort_values(["station_id", "variable", "date"]).reset_index(drop=True)

@st.cache_data
def read_observed_station_timeseries(
    basin_dir: Path,
    filename: str,
    site_no: str,
    variable: str,
) -> pd.DataFrame:
    path = basin_dir / filename

    if not path.exists():
        return pd.DataFrame(columns=["date", "observed"])

    column_map = {
        "flow": "Q_cms",
        "gauge_height": "gauge_height_m",
        "water_temp": "watertemp_c",
        "specific_conductivity": "SPC",
        "salinity": "sal_psu",
        "baseflow": "Qbase",
    }

    value_col = column_map.get(variable)
    if value_col is None:
        return pd.DataFrame(columns=["date", "observed"])

    usecols = ["site_no", "Date", value_col]

    df = pd.read_csv(
        path,
        usecols=usecols,
        parse_dates=["Date"],
        dtype={"site_no": str},
        low_memory=False,
    )

    print("Requested site_no:", repr(site_no))
    print("Sample site_no values:", df["site_no"].astype(str).dropna().unique()[:10])

    df = df[df["site_no"].astype(str) == str(site_no)].copy()
    df = df.rename(columns={"Date": "date", value_col: "observed"})
    df = df[["date", "observed"]]
    df = df.sort_values("date").reset_index(drop=True)

    return df


def read_channel_sdmorph_day(
    model_dir: Path,
    variables: list[str] | None = None,
) -> pd.DataFrame:
    if variables is None:
        variables = ["flo_out", "sed_out"]

    txt_path = model_dir / "channel_sdmorph_day.txt"

    if not txt_path.exists():
        return pd.DataFrame(columns=["date", "gis_id"] + variables)

    usecols = ["yr", "mon", "day", "gis_id"] + variables

    df = pd.read_csv(
        txt_path,
        sep=r"\s+",
        skiprows=[0, 2],
        usecols=usecols,
        low_memory=False,
    )

    df["date"] = pd.to_datetime(
        dict(year=df["yr"], month=df["mon"], day=df["day"]),
        errors="coerce",
    )

    df = df.dropna(subset=["date"]).copy()

    return df[["date", "gis_id"] + variables].sort_values(["gis_id", "date"]).reset_index(drop=True)


def read_time_sim_file(model_dir: Path) -> pd.DataFrame:
    path = model_dir / "time.sim"
    return pd.read_csv(path, sep=r"\s+", skiprows=1)


def read_print_prt_file(model_dir: Path) -> pd.DataFrame:
    path = model_dir / "print.prt"
    return pd.read_csv(path, sep=r"\s+", skiprows=1)


def build_swat_daily_dates(model_dir: Path) -> pd.DatetimeIndex:
    df_time = read_time_sim_file(model_dir)
    df_prt = read_print_prt_file(model_dir)

    skipyear = int(df_prt.loc[0, "nyskip"])
    yrc_start = int(df_time.loc[0, "yrc_start"])
    yrc_end = int(df_time.loc[0, "yrc_end"])
    day_start = int(df_time.loc[0, "day_start"])
    day_end = int(df_time.loc[0, "day_end"])

    start_date = pd.Timestamp(yrc_start, 1, 1) + pd.Timedelta(days=day_start - 1)
    end_date = pd.Timestamp(yrc_end, 1, 1) + pd.Timedelta(days=day_end - 1)

    full_dates = pd.date_range(start=start_date, end=end_date, freq="D")

    if skipyear > 0:
        warmup_start = pd.Timestamp(yrc_start + skipyear, 1, 1) + pd.Timedelta(days=day_start - 1)
        full_dates = full_dates[full_dates >= warmup_start]

    return full_dates

@st.cache_data
def read_channel_daily_parquet(basin_dir: Path) -> pd.DataFrame:
    path = basin_dir / "channel_daily.parquet"

    if not path.exists():
        return pd.DataFrame(columns=["date", "gis_id", "flo_out", "sed_out"])

    df = pd.read_parquet(path)

    return df