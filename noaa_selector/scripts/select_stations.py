import geopandas as gpd
import pandas as pd
import requests

def select_stations(
    basin,
    buffer_km,
    year_min,
    cal_start,
    cal_end,
    min_years,
    min_cover_frac,
    min_dist_km,
    token
):
    # ============================
    # 1. Unificar cuenca
    # ============================
    basin_union = basin.union_all()
    basin_single = gpd.GeoDataFrame(geometry=[basin_union], crs=4326)

    # ============================
    # 2. Buffer
    # ============================
    if buffer_km > 0:
        basin_utm = basin_single.to_crs(32613)
        basin_buffer = basin_utm.buffer(buffer_km * 1000)
        basin_buffer = gpd.GeoDataFrame(geometry=basin_buffer, crs=32613).to_crs(4326)
    else:
        basin_buffer = basin_single.copy()

    # ============================
    # 3. Descargar estaciones NOAA
    # ============================
    west, south, east, north = basin_buffer.total_bounds
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"

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
            print("NOAA devolvió algo que no es JSON")
            print(r.text[:500])
            break

        data = json_data.get("results", [])
        if not data:
            break

        all_results.extend(data)
        offset += 1000

    stations = pd.DataFrame(all_results)

    if stations.empty:
        return gpd.GeoDataFrame(), basin_buffer

    # ============================
    # 4. Manejo robusto de mindate / maxdate
    # ============================

    def fix_date_column(df, names, new_name):
        """Encuentra la columna correcta y la convierte a datetime."""
        for col in names:
            if col in df.columns:
                df[new_name] = pd.to_datetime(df[col], errors="coerce")
                return
        df[new_name] = pd.NaT

    fix_date_column(stations, ["mindate", "minDate", "min_date"], "mindate")
    fix_date_column(stations, ["maxdate", "maxDate", "max_date"], "maxdate")

    # span_years
    stations["span_years"] = (stations["maxdate"] - stations["mindate"]).dt.days / 365.25

    # ============================
    # 5. Convertir a GeoDataFrame
    # ============================
    g_st = gpd.GeoDataFrame(
        stations,
        geometry=gpd.points_from_xy(stations.longitude, stations.latitude),
        crs=4326
    )

    # ============================
    # 6. Filtro espacial
    # ============================
    stations_inside = gpd.sjoin(g_st, basin_buffer, predicate="within").drop_duplicates(subset="id")

    # ============================
    # 7. Filtros por fechas
    # ============================
    stations_inside = stations_inside[stations_inside["maxdate"].dt.year >= year_min]

    cal_start_dt = pd.to_datetime(cal_start)
    cal_end_dt   = pd.to_datetime(cal_end)
    cal_years    = cal_end_dt.year - cal_start_dt.year + 1

    def years_in_cal(row):
        if pd.isna(row["mindate"]) or pd.isna(row["maxdate"]):
            return 0
        return max(0, min(row["maxdate"].year, cal_end_dt.year) -
                      max(row["mindate"].year, cal_start_dt.year) + 1)

    stations_inside["years_in_cal"] = stations_inside.apply(years_in_cal, axis=1)
    stations_inside["cover_frac"] = stations_inside["years_in_cal"] / cal_years

    # Filtro de recencia
    stations_inside = stations_inside[stations_inside["maxdate"].dt.year >= 2010]

    # ============================
    # 8. Filtros finales
    # ============================
    stations_filtered = stations_inside[
        (stations_inside["span_years"] >= min_years) &
        (stations_inside["cover_frac"] >= min_cover_frac)
    ].copy()

    if stations_filtered.empty:
        return gpd.GeoDataFrame(), basin_buffer

    # ============================
    # 9. Score
    # ============================
    max_span = stations_filtered["span_years"].max()
    min_year = stations_filtered["maxdate"].dt.year.min()
    max_year = stations_filtered["maxdate"].dt.year.max()

    stations_filtered["recency_norm"] = (
        stations_filtered["maxdate"].dt.year - min_year
    ) / (max_year - min_year if max_year > min_year else 1)

    stations_filtered["score"] = (
        0.4 * (stations_filtered["span_years"] / max_span) +
        0.4 * stations_filtered["cover_frac"] +
        0.2 * stations_filtered["recency_norm"]
    )

    stations_filtered = stations_filtered.sort_values("score", ascending=False)

    # ============================
    # 10. Thinning por distancia
    # ============================
    st_utm = stations_filtered.to_crs(32613)
    selected_idx = []
    used = set()
    min_dist_m = min_dist_km * 1000

    for i, row in st_utm.iterrows():
        if i in used:
            continue
        selected_idx.append(i)
        dists = st_utm.geometry.distance(row.geometry)
        used.update(dists[dists < min_dist_m].index)

    stations_thinned = stations_filtered.loc[selected_idx].copy()

    # ============================
    # 11. Bandas de elevación
    # ============================
    stations_thinned["elevation"] = pd.to_numeric(stations_thinned["elevation"], errors="coerce")
    st_elev = stations_thinned.dropna(subset=["elevation"]).copy()

    if not st_elev.empty:
        q = st_elev["elevation"].quantile([0.25, 0.5, 0.75])
        q1, q2, q3 = q[0.25], q[0.5], q[0.75]

        def elev_band(z):
            if pd.isna(z):
                return "NA"
            if z <= q1: return "baja"
            if z <= q2: return "media-baja"
            if z <= q3: return "media-alta"
            return "alta"

        stations_thinned["elev_band"] = stations_thinned["elevation"].apply(elev_band)
    else:
        stations_thinned["elev_band"] = "NA"

    return stations_thinned, basin_buffer
