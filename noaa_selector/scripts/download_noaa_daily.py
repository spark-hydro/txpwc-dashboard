import pandas as pd
from .download_noaa_yearly import download_noaa_yearly

def download_noaa_daily(station_id, start_date, end_date):
    """
    Wrapper que usa download_noaa_yearly con token HARDCODEADO.
    """

    start_year = pd.to_datetime(start_date).year
    end_year = pd.to_datetime(end_date).year

    df = download_noaa_yearly(station_id, start_year, end_year)

    if df.empty:
        return df

    df["DATE"] = pd.to_datetime(df["DATE"])

    mask = (df["DATE"] >= pd.to_datetime(start_date)) & (df["DATE"] <= pd.to_datetime(end_date))
    return df.loc[mask]
