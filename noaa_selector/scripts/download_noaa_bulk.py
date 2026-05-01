import pandas as pd
from scripts.download_noaa_daily import download_noaa_daily

def download_bulk(stations_df, start_date, end_date, token):
    results = {}

    for _, row in stations_df.iterrows():
        sid = row["id"]
        name = row["name"]

        df = download_noaa_daily(sid, start_date, end_date, token)
        results[sid] = df

    return results
