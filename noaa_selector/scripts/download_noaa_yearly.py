import time

import requests
import pandas as pd


def download_noaa_yearly(station_id: str, start_year: int, end_year: int,
                          token: str = "") -> pd.DataFrame:
    _token = token.strip() if token and token.strip() else "CHSymOnkMgrHkRUcybaxSZEAVEFQUgmq"

    url     = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
    headers = {"token": _token}
    frames  = []

    for year in range(start_year, end_year + 1):
        params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "startdate": f"{year}-01-01",
            "enddate":   f"{year}-12-31",
            "limit":     1000,
            "units":     "metric",
            "offset":    1,
        }

        while True:
            try:
                r = requests.get(url, params=params, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()
            except requests.HTTPError as e:
                raise RuntimeError(
                    f"HTTP {r.status_code} for {station_id} {year}: {r.text[:200]}"
                ) from e
            except Exception as e:
                raise RuntimeError(f"Request failed for {station_id} {year}: {e}") from e

            if "results" not in data:
                break

            frames.append(pd.DataFrame(data["results"]))

            if len(data["results"]) < 1000:
                break

            params["offset"] += 1000
            time.sleep(0.2)

        time.sleep(0.2)  # stay under NOAA rate limit across years

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df = df.pivot_table(
        index="date", columns="datatype",
        values="value", aggfunc="first"
    ).reset_index()
    df.rename(columns={"date": "DATE"}, inplace=True)

    for col in ["PRCP", "TMAX", "TMIN"]:
        if col not in df.columns:
            df[col] = None

    return df[["DATE", "PRCP", "TMAX", "TMIN"]]
