import requests
import pandas as pd

# ⭐ TOKEN HARDCODEADO (igual que en tu script original)
TOKEN = "CHSymOnkMgrHkRUcybaxSZEAVEFQUgmq"

def download_noaa_yearly(station_id, start_year, end_year):
    """
    Descarga datos NOAA GHCND año por año (PRCP, TMAX, TMIN).
    Usa el token HARDCODEADO para asegurar que NOAA responda igual que en tu script original.
    """

    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
    headers = {"token": TOKEN}

    frames = []

    for year in range(start_year, end_year + 1):

        params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "startdate": f"{year}-01-01",
            "enddate": f"{year}-12-31",
            "limit": 1000,
            "units": "metric"
        }

        offset = 1

        while True:
            params["offset"] = offset
            r = requests.get(url, params=params, headers=headers)

            # NOAA sometimes returns HTML → skip safely
            try:
                data = r.json()
            except:
                break

            if "results" not in data:
                break

            frames.append(pd.DataFrame(data["results"]))

            if len(data["results"]) < 1000:
                break

            offset += 1000

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    # Pivot to wide format
    df = df.pivot_table(
        index="date",
        columns="datatype",
        values="value",
        aggfunc="first"
    ).reset_index()

    df.rename(columns={"date": "DATE"}, inplace=True)

    # Ensure columns exist
    for col in ["PRCP", "TMAX", "TMIN"]:
        if col not in df.columns:
            df[col] = None

    return df[["DATE", "PRCP", "TMAX", "TMIN"]]
