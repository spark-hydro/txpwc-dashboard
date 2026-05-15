import geopandas as gpd
import pandas as pd
import requests

def download_noaa_stations(basin, buffer_km):

    basin_union = basin.union_all()
    basin_single = gpd.GeoDataFrame(geometry=[basin_union], crs=4326)

    if buffer_km > 0:
        basin_utm = basin_single.to_crs(32613)
        basin_buffer = basin_utm.buffer(buffer_km * 1000)
        basin_buffer = gpd.GeoDataFrame(geometry=basin_buffer, crs=32613).to_crs(4326)
    else:
        basin_buffer = basin_single

    west, south, east, north = basin_buffer.total_bounds

    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
    token = "CHSymOnkMgrHkRUcybaxSZEAVEFQUgmq"

    params = {
        "datasetid": "GHCND",
        "extent": f"{south},{west},{north},{east}",
        "limit": 1000
    }

    all_results = []
    offset = 1

    while True:
        params["offset"] = offset
        r = requests.get(url, params=params, headers={"token": token})

        try:
            json_data = r.json()
        except:
            break

        data = json_data.get("results", [])
        if not data:
            break

        all_results.extend(data)
        offset += 1000

    return pd.DataFrame(all_results)
