import pandas as pd

def get_station_daily_from_existing_workflow(station_id, stations_meta, token):
    """
    Usa tu flujo que ya funciona (download_noaa_yearly o similar)
    para una sola estación, usando su mindate y maxdate.
    """
    row = stations_meta.loc[stations_meta["id"] == station_id].iloc[0]

    min_year = max(1980, pd.to_datetime(row["mindate"]).year)
    max_year = min(2024, pd.to_datetime(row["maxdate"]).year)

    # Aquí llamas a TU función que ya funciona
    from scripts.download_noaa_yearly import download_noaa_yearly
    df = download_noaa_yearly(station_id, min_year, max_year)

    return df
