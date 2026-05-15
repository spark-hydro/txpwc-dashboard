import pandas as pd
from .download_noaa_yearly import download_noaa_yearly


def download_noaa_daily(station_id: str, start_date, end_date,
                         token: str = "") -> pd.DataFrame:
    """
    Download daily NOAA GHCND data for a single station between two dates.

    Parameters
    ----------
    station_id : str   e.g. "GHCND:USW00023050"
    start_date : str | date | datetime
    end_date   : str | date | datetime
    token      : str   NOAA CDO API token — passed through to download_noaa_yearly
    """
    start_year = pd.to_datetime(start_date).year
    end_year   = pd.to_datetime(end_date).year

    df = download_noaa_yearly(station_id, start_year, end_year, token=token)

    if df.empty:
        return df

    df["DATE"] = pd.to_datetime(df["DATE"])
    mask = (
        (df["DATE"] >= pd.to_datetime(start_date)) &
        (df["DATE"] <= pd.to_datetime(end_date))
    )
    return df.loc[mask].reset_index(drop=True)
