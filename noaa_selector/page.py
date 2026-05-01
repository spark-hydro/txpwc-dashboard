import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import tempfile
import plotly.express as px
import os


from .scripts.download_noaa import download_noaa_stations
from .scripts.filter_and_score import filter_and_score
from .scripts.select_stations import select_stations
from .scripts.analyze_subbasins import analyze_subbasins
from .scripts.download_noaa_daily import download_noaa_daily
from .scripts.download_noaa_yearly import download_noaa_yearly
from .scripts.make_map import make_map
from .scripts.noaa_single import get_station_daily_from_existing_workflow


def run_app():

    # ============================
    # Language Selector
    # ============================

    language = st.sidebar.selectbox("Language / Idioma", ["English", "Español"])

    def T(en, es):
        return en if language == "English" else es

    # ============================
    # Title
    # ============================

    st.title(T(
        "🌧️ NOAA Climate Station Selector for SWAT",
        "🌧️ Selector de Estaciones Climáticas NOAA para SWAT"
    ))

    st.markdown(T(
    """
    Upload a watershed shapefile, choose your parameters, and automatically:

    1. Download NOAA GHCND stations  
    2. Filter + score + thin by distance  
    3. Analyze subbasin coverage  
    4. Generate an interactive Folium map  
    """,
    """
    Carga un shapefile de cuenca, elige tus parámetros y automáticamente:

    1. Descarga estaciones NOAA GHCND  
    2. Filtra + puntúa + reduce por distancia  
    3. Analiza cobertura por subcuenca  
    4. Genera un mapa interactivo con Folium  
    """
    ))

    # ============================
    # Step 1 — Upload Shapefile
    # ============================

    st.header(T("1. Upload your watershed shapefile", "1. Cargar shapefile de la cuenca"))

    uploaded_files = st.file_uploader(
        T("Upload shapefile components", "Subir componentes del shapefile"),
        type=["shp", "shx", "dbf", "prj"],
        accept_multiple_files=True
    )

    # ⭐ SOLO ejecutar Step 1 cuando el usuario sube archivos
    if uploaded_files:

        # ⭐ Si ya había un shapefile cargado → limpiar session_state
        if uploaded_files and "basin" not in st.session_state:

            # (opcional) si quieres limpiar cosas viejas de otra corrida:
            for key in [
                "basin", "stations_thinned", "nearest_df",
                "sub_counts", "basin_buffer", "final_map"
            ]:
                st.session_state.pop(key, None)
            if "basin" in st.session_state:
                st.warning(T(
                    "Replacing previous shapefile. Clearing previous results.",
                    "Reemplazando shapefile previo. Limpiando resultados anteriores."
                ))
                for key in [
                    "basin", "stations_thinned", "nearest_df",
                    "sub_counts", "basin_buffer", "final_map"
                ]:
                    st.session_state.pop(key, None)

        # ⭐ Validar shapefile completo
        required_ext = {".shp", ".shx", ".dbf", ".prj"}
        uploaded_ext = {os.path.splitext(f.name)[1].lower() for f in uploaded_files}

        missing = required_ext - uploaded_ext
        if missing:
            st.error(f"Missing shapefile components: {missing}. Please upload .shp, .shx, .dbf, .prj.")
            st.stop()

        # ⭐ Guardar archivos en carpeta temporal
        temp_dir = tempfile.mkdtemp()
        for f in uploaded_files:
            with open(os.path.join(temp_dir, f.name), "wb") as out:
                out.write(f.read())

        # ⭐ Cargar shapefile
        shp_path = [os.path.join(temp_dir, f.name) for f in uploaded_files if f.name.endswith(".shp")][0]
        basin = gpd.read_file(shp_path)

        # ⭐ Detectar CRS
        if basin.crs is None:
            st.warning("Shapefile has no CRS. Assigning Miller Cylindrical (ESRI:54003).")
            basin = basin.set_crs("ESRI:54003")

        # ⭐ Reproyectar a WGS84
        basin = basin.to_crs(4326)

        # ⭐ Guardar en session_state
        st.session_state["basin"] = basin

        st.success(T("Shapefile loaded successfully!", "¡Shapefile cargado exitosamente!"))

    # ============================
    # Step 2 — Parameters
    # ============================

    st.header(T("2. Select parameters", "2. Seleccionar parámetros"))

    col1, col2, col3 = st.columns(3)

    with col1:
        buffer_km = st.number_input(T("Buffer (km)", "Buffer (km)"), 0, 50, 15)
        min_year = st.number_input(T("Minimum year", "Año mínimo"), 1900, 2025, 2000)

    with col2:
        cal_start = st.text_input(T("Calibration start", "Inicio de calibración"), "2010-01-01")
        cal_end = st.text_input(T("Calibration end", "Fin de calibración"), "2020-12-31")

    with col3:
        min_years = st.number_input(T("Minimum years of data", "Años mínimos de datos"), 1, 50, 5)
        min_cover = st.slider(T("Coverage fraction", "Fracción de cobertura"), 0.0, 1.0, 0.5)
        min_dist_km = st.number_input(T("Minimum spacing (km)", "Distancia mínima (km)"), 1, 100, 25)

    # ⭐ TOKEN NOAA PARA STEP 3
    token = st.text_input(
        T("Enter your NOAA API token", "Ingresa tu token NOAA API"),
        type="password",
        key="token_step3"
    )

    run_button = st.button(T("Run NOAA Station Selection", "Ejecutar selección de estaciones NOAA"))


    # ============================
    # Step 3.0 — Button (Compute Only)
    # ============================

    if run_button and "basin" in st.session_state:

        basin = st.session_state["basin"]

        with st.spinner("Selecting NOAA stations…"):
            stations_thinned, basin_buffer = select_stations(
                basin,
                buffer_km,
                min_year,
                cal_start,
                cal_end,
                min_years,
                min_cover,
                min_dist_km,
                token
            )

        # ⭐ LIMPIAR columnas heredadas de sjoin previos
        stations_thinned = stations_thinned.drop(
            columns=[c for c in stations_thinned.columns if c in ["index_right", "index_left"]],
            errors="ignore"
        )

        basin = basin.drop(
            columns=[c for c in basin.columns if c in ["index_right", "index_left"]],
            errors="ignore"
        )

        with st.spinner("Analyzing subbasins…"):
            nearest_df, sub_counts = analyze_subbasins(stations_thinned, basin)

        # Guardar resultados
        st.session_state["stations_thinned"] = stations_thinned
        st.session_state["nearest_df"] = nearest_df
        st.session_state["sub_counts"] = sub_counts
        st.session_state["basin_buffer"] = basin_buffer

        # ⭐ Inicializar bulk_data para evitar errores posteriores
        if "bulk_data" not in st.session_state:
            st.session_state["bulk_data"] = {}

        # DEBUG
        st.write("DEBUG stations_thinned:", len(stations_thinned))
        st.write("DEBUG nearest_df:", len(nearest_df))
        st.write("DEBUG sub_counts:", len(sub_counts))


    # ============================
    # Step 3 — Results (Always Visible)
    # ============================

    if (
        "stations_thinned" in st.session_state and
        "nearest_df" in st.session_state and
        "sub_counts" in st.session_state and
        "basin_buffer" in st.session_state
    ):

        basin = st.session_state["basin"]
        stations_thinned = st.session_state["stations_thinned"]
        nearest_df = st.session_state["nearest_df"]
        sub_counts = st.session_state["sub_counts"]
        basin_buffer = st.session_state["basin_buffer"]

        st.header("3. Results and map")

        # --- Coverage summary ---
        st.subheader("Subbasin coverage summary")

        total_subs = len(nearest_df)
        gt40 = (nearest_df["dist_km"] > 40).sum()
        gt60 = (nearest_df["dist_km"] > 60).sum()
        gt80 = (nearest_df["dist_km"] > 80).sum()
        gt100 = (nearest_df["dist_km"] > 100).sum()

        st.write(f"Total subbasins: {total_subs}")
        st.write(f"> 40 km: {gt40}")
        st.write(f"> 60 km: {gt60}")
        st.write(f"> 80 km: {gt80}")
        st.write(f"> 100 km: {gt100}")

        # --- Final Folium Map ---
        st.subheader("Final station map")

        stations = stations_thinned.copy()
        basin_subs = basin.copy()
        basin_union = basin_subs.union_all()
        basin_single = gpd.GeoDataFrame(geometry=[basin_union], crs=4326)

        def color_from_band(band):
            return {
                "baja": "blue",
                "media-baja": "green",
                "media-alta": "orange",
                "alta": "red"
            }.get(band, "gray")

        centroid = basin_single.geometry.unary_union.centroid

        m_final = folium.Map(
            location=[centroid.y, centroid.x],
            zoom_start=7,
            tiles="CartoDB positron"
        )

        folium.GeoJson(basin_single.to_json(), name="Basin").add_to(m_final)
        folium.GeoJson(basin_subs.to_json(), name="Subbasins").add_to(m_final)
        folium.GeoJson(basin_buffer.to_json(), name="Buffer").add_to(m_final)

        cluster = MarkerCluster(name="Stations").add_to(m_final)

        for _, row in stations.iterrows():
            folium.Marker(
                location=[row.geometry.y, row.geometry.x],
                popup=row["name"],
                icon=folium.Icon(color=color_from_band(row["elev_band"]))
            ).add_to(cluster)

        folium.LayerControl().add_to(m_final)
        st_folium(m_final, width=900, height=600)

    # ============================
    # Step 5 — Climate Analysis Dashboard
    # ============================

    st.header("5. Climate Analysis Dashboard")

    stations = st.session_state["stations_thinned"]

    # Select station
    station_choice = st.selectbox(
        "Select a station for analysis",
        stations["name"] + " — " + stations["id"]
    )

    sid = station_choice.split(" — ")[-1]

    # Load station data from your NOAA folder
    def load_station_data(station_id):
        fname = station_id.replace(":", "_") + ".csv"
        path = os.path.join("noaa_raw", fname)
        df = pd.read_csv(path)
        df["DATE"] = pd.to_datetime(df["DATE"])
        return df

    df = load_station_data(sid)

    # Derived columns (in memory only)
    df2 = df.copy()
    df2["year"] = df2["DATE"].dt.year
    df2["month"] = df2["DATE"].dt.month
    df2["doy"] = df2["DATE"].dt.dayofyear
    df2["decade"] = (df2["year"] // 10) * 10

    tab1, tab2, tab3, tab4 = st.tabs([
        "Station Overview",
        "Time Series & Gaps",
        "Calibration Period",
        "Climate Trends"
    ])

    # ---------------------------
    # TAB 1 — STATION OVERVIEW
    # ---------------------------
    with tab1:
        row = stations[stations["id"] == sid].iloc[0]

        st.subheader("Metadata")
        st.write(f"**Name:** {row['name']}")
        st.write(f"**ID:** {sid}")
        st.write(f"**Elevation:** {row['elevation']} m")
        st.write(f"**Elevation band:** {row['elev_band']}")
        st.write(f"**Data range:** {row['mindate']} → {row['maxdate']}")
        st.write(f"**Coverage fraction:** {row['cover_frac']:.2f}")
        st.write(f"**Score:** {row['score']:.3f}")

        st.subheader("Basic Statistics")
        st.write(df.describe())

    # ---------------------------
    # TAB 2 — TIME SERIES & GAPS
    # ---------------------------
    with tab2:
        st.subheader("Daily Precipitation")
        fig_prcp = px.line(df2, x="DATE", y="PRCP", title="Daily PRCP")
        st.plotly_chart(fig_prcp, use_container_width=True)

        st.subheader("Daily Temperature")
        df_temp = df2.melt(id_vars=["DATE"], value_vars=["TMAX", "TMIN"],
                           var_name="variable", value_name="temperature")
        fig_temp = px.line(df_temp, x="DATE", y="temperature",
                           color="variable", title="TMAX/TMIN")
        st.plotly_chart(fig_temp, use_container_width=True)

        st.subheader("Missing Data Heatmap")
        missing = df2.copy()
        missing["missing"] = df2["PRCP"].isna()
        heat = missing.pivot_table(index="year", columns="month",
                                   values="missing", aggfunc="mean")
        fig_heat = px.imshow(heat, aspect="auto",
                             labels=dict(color="% Missing"),
                             title="Missing Data by Year/Month")
        st.plotly_chart(fig_heat, use_container_width=True)

    # ---------------------------
    # TAB 3 — CALIBRATION PERIOD
    # ---------------------------
    with tab3:
        st.subheader("Select Calibration Period")

        min_y = int(df2["year"].min())
        max_y = int(df2["year"].max())

        cal_start, cal_end = st.slider(
            "Calibration years",
            min_y, max_y, (min_y, max_y)
        )

        cal_df = df2[(df2["year"] >= cal_start) & (df2["year"] <= cal_end)]

        st.write(f"Records in calibration window: {len(cal_df)}")

        missing_pct = cal_df["PRCP"].isna().mean() * 100
        st.write(f"**Missing PRCP:** {missing_pct:.2f}%")

        st.subheader("Annual PRCP in Calibration Window")
        annual = cal_df.groupby("year")["PRCP"].sum().reset_index()
        fig_ann = px.bar(annual, x="year", y="PRCP")
        st.plotly_chart(fig_ann, use_container_width=True)

    # ---------------------------
    # TAB 4 — CLIMATE TRENDS
    # ---------------------------

    with tab4:
        st.subheader("Decadal Precipitation")
        dec_prcp = df2.groupby("decade")["PRCP"].sum().reset_index()
        fig_dec = px.bar(dec_prcp, x="decade", y="PRCP")
        st.plotly_chart(fig_dec, use_container_width=True)

        st.subheader("Temperature Trends")
        dec_temp = df2.groupby("decade")[["TMAX", "TMIN"]].mean().reset_index()
        fig_temp_dec = px.line(dec_temp, x="decade", y=["TMAX", "TMIN"])
        st.plotly_chart(fig_temp_dec, use_container_width=True)



    # ============================
    # Step 6 — Advanced Climate Diagnostics
    # ============================

    import os
    import numpy as np
    import pandas as pd
    from scipy.stats import linregress
    import plotly.express as px
    import plotly.graph_objects as go

    st.header("6. Advanced Climate Diagnostics")

    NOAA_FOLDER = "noaa_raw"

    # ----------------------------------------
    # Helper: Load ALL stations
    # ----------------------------------------
    @st.cache_data
    def load_all_stations():
        files = [f for f in os.listdir(NOAA_FOLDER) if f.endswith(".csv")]
        data = {}

        for f in files:
            sid = f.replace(".csv", "").replace("_", ":")
            df = pd.read_csv(os.path.join(NOAA_FOLDER, f))
            df["DATE"] = pd.to_datetime(df["DATE"])
            df["year"] = df["DATE"].dt.year
            data[sid] = df

        return data

    all_data = load_all_stations()

    # ----------------------------------------
    # Helper: Compute climate metrics per station
    # ----------------------------------------
    def compute_station_metrics(df):
        df2 = df.copy()
        df2["year"] = df2["DATE"].dt.year

        # Mean annual PRCP
        annual = df2.groupby("year")["PRCP"].sum()
        mean_prcp = annual.mean()

        # Missingness
        missing_pct = df2["PRCP"].isna().mean() * 100

        # PRCP trend (mm/decade)
        if len(annual) > 1:
            slope, _, _, _, _ = linregress(annual.index, annual.values)
            prcp_trend = slope * 10
        else:
            prcp_trend = np.nan

        # Temperature trends
        annual_tmax = df2.groupby("year")["TMAX"].mean()
        annual_tmin = df2.groupby("year")["TMIN"].mean()

        def trend(series):
            if len(series) > 1:
                slope, _, _, _, _ = linregress(series.index, series.values)
                return slope * 10
            return np.nan

        tmax_trend = trend(annual_tmax)
        tmin_trend = trend(annual_tmin)

        return mean_prcp, prcp_trend, missing_pct, tmax_trend, tmin_trend

    # ----------------------------------------
    # Build metrics table
    # ----------------------------------------
    metrics = []
    stations_gdf = st.session_state["stations_thinned"]

    for sid, df in all_data.items():
        row = stations_gdf[stations_gdf["id"] == sid]
        if len(row) == 0:
            continue

        mean_prcp, prcp_trend, missing_pct, tmax_trend, tmin_trend = compute_station_metrics(df)

        metrics.append({
            "id": sid,
            "name": row.iloc[0]["name"],
            "lat": row.iloc[0].geometry.y,
            "lon": row.iloc[0].geometry.x,
            "mean_prcp": mean_prcp,
            "prcp_trend": prcp_trend,
            "missing_pct": missing_pct,
            "tmax_trend": tmax_trend,
            "tmin_trend": tmin_trend,
            "elev_band": row.iloc[0].get("elev_band", None)
        })

    metrics_df = pd.DataFrame(metrics)

    # ----------------------------------------
    # Tabs
    # ----------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "Spatial Climate Maps",
        "Multi‑Station Comparison",
        "Mann–Kendall Trends",
        "Global Calibration Optimizer"
    ])

    # ============================================================
    # TAB 1 — SPATIAL CLIMATE MAPS
    # ============================================================
    with tab1:
        st.subheader("Mean Annual Precipitation (mm)")

        fig = px.scatter_geo(
            metrics_df,
            lat="lat",
            lon="lon",
            color="mean_prcp",
            size="mean_prcp",
            hover_name="name",
            projection="natural earth",
            title="Mean Annual PRCP"
        )
        st.plotly_chart(fig, use_container_width=True)

        # ---------------- PRCP TREND ----------------
        st.subheader("PRCP Trend (mm/decade)")

        metrics_df["prcp_trend_abs"] = (
            metrics_df["prcp_trend"]
            .fillna(0)
            .abs()
            .clip(lower=5)
        )

        fig2 = px.scatter_geo(
            metrics_df,
            lat="lat",
            lon="lon",
            color="prcp_trend",
            size="prcp_trend_abs",
            hover_name="name",
            projection="natural earth",
            color_continuous_scale="RdBu_r",
            title="PRCP Trend (mm/decade)"
        )
        st.plotly_chart(fig2, use_container_width=True)

        # ---------------- MISSINGNESS ----------------
        st.subheader("Missingness (%)")

        # Fixed size, color only
        metrics_df["missing_size"] = 12

        fig3 = px.scatter_geo(
            metrics_df,
            lat="lat",
            lon="lon",
            color="missing_pct",
            size="missing_size",
            hover_name="name",
            projection="natural earth",
            color_continuous_scale="YlOrRd",
            title="Missing Data (%)"
        )
        st.plotly_chart(fig3, use_container_width=True)

        # ---------------- TEMPERATURE TRENDS ----------------
        st.subheader("TMAX Trend (°C/decade)")

        metrics_df["tmax_trend_abs"] = (
            metrics_df["tmax_trend"]
            .fillna(0)
            .abs()
            .clip(lower=5)
        )

        fig_tmax = px.scatter_geo(
            metrics_df,
            lat="lat",
            lon="lon",
            color="tmax_trend",
            size="tmax_trend_abs",
            hover_name="name",
            projection="natural earth",
            color_continuous_scale="RdBu_r",
            title="TMAX Trend (°C/decade)"
        )
        st.plotly_chart(fig_tmax, use_container_width=True)

        st.subheader("TMIN Trend (°C/decade)")

        metrics_df["tmin_trend_abs"] = (
            metrics_df["tmin_trend"]
            .fillna(0)
            .abs()
            .clip(lower=5)
        )

        fig_tmin = px.scatter_geo(
            metrics_df,
            lat="lat",
            lon="lon",
            color="tmin_trend",
            size="tmin_trend_abs",
            hover_name="name",
            projection="natural earth",
            color_continuous_scale="RdBu_r",
            title="TMIN Trend (°C/decade)"
        )
        st.plotly_chart(fig_tmin, use_container_width=True)

    # ============================================================
    # TAB 2 — MULTI‑STATION COMPARISON
    # ============================================================
    with tab2:
        st.subheader("Annual PRCP Comparison")

        combined = []
        for sid, df in all_data.items():
            df2 = df.copy()
            df2["year"] = df2["DATE"].dt.year
            annual = df2.groupby("year")["PRCP"].sum().reset_index()
            annual["station"] = sid
            combined.append(annual)

        if combined:
            combined_df = pd.concat(combined)

            fig = px.line(
                combined_df,
                x="year",
                y="PRCP",
                color="station",
                title="Annual PRCP Comparison"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No station data available for comparison.")

    # ============================================================
    # TAB 3 — MANN–KENDALL TREND TEST (GRAPH + TABLE)
    # ============================================================
    with tab3:
        st.subheader("Mann–Kendall Trend Test (Annual PRCP)")

        try:
            import pymannkendall as mk
        except ImportError:
            st.error("pymannkendall is not installed. Run: pip install pymannkendall")
            st.stop()

        mk_results = []
        for sid, df in all_data.items():
            df2 = df.copy()
            df2["year"] = df2["DATE"].dt.year
            annual = df2.groupby("year")["PRCP"].sum()

            if len(annual) > 5:
                res = mk.original_test(annual.values)
                mk_results.append({
                    "station": sid,
                    "trend": res.trend,
                    "p_value": res.p,
                    "slope": res.slope
                })

        if mk_results:
            mk_df = pd.DataFrame(mk_results)
            st.write("Mann–Kendall Results (Table):")
            st.dataframe(mk_df)

            # Graph: Sen's slope per station
            st.write("Mann–Kendall Sen's Slope (Graph):")

            mk_df["sign"] = np.where(mk_df["slope"] >= 0, "Increasing", "Decreasing")
            mk_df["significant"] = mk_df["p_value"] < 0.05

            fig_mk = px.bar(
                mk_df,
                x="station",
                y="slope",
                color="sign",
                color_discrete_map={"Increasing": "blue", "Decreasing": "red"},
                title="Sen's Slope by Station (Annual PRCP)"
            )

            # Highlight significant trends with thicker outline
            fig_mk.update_traces(
                marker_line_width=np.where(mk_df["significant"], 2.5, 0.5),
                marker_line_color="black"
            )

            st.plotly_chart(fig_mk, use_container_width=True)
        else:
            st.info("Not enough data to compute Mann–Kendall trends.")

    # ============================================================
    # TAB 4 — GLOBAL CALIBRATION OPTIMIZER
    # ============================================================
    with tab4:
        st.subheader("Global Calibration Period Recommendation (All Stations)")

        if not all_data:
            st.info("No station data available for calibration optimization.")
        else:
            # User‑defined window length range
            col1, col2 = st.columns(2)
            with col1:
                min_len = st.number_input("Minimum window length (years)", min_value=3, max_value=50, value=5, step=1)
            with col2:
                max_len = st.number_input("Maximum window length (years)", min_value=min_len, max_value=60, value=20, step=1)

            # Collect global year range
            all_years = []
            for df in all_data.values():
                yrs = df["year"].unique()
                all_years.extend(list(yrs))
            all_years = sorted(list(set(all_years)))

            best_score = -999
            best_window = None
            window_scores = []

            # Evaluate all candidate windows
            for start in all_years:
                for end in all_years:
                    length = end - start + 1
                    if length < min_len or length > max_len:
                        continue
                    if end <= start:
                        continue

                    station_scores = []

                    for sid, df in all_data.items():
                        sub = df[(df["year"] >= start) & (df["year"] <= end)]
                        if sub.empty:
                            continue

                        # Missingness
                        missing = sub["PRCP"].isna().mean()

                        # Annual variance
                        annual = sub.groupby("year")["PRCP"].sum()
                        if len(annual) < 2:
                            continue
                        var = annual.var()

                        # Simple score: high when low missingness and stable variance
                        # (you can refine this later)
                        score = (1 - missing) * (1 / (1 + var))
                        station_scores.append(score)

                    if not station_scores:
                        continue

                    window_score = np.mean(station_scores)
                    window_scores.append({
                        "start": start,
                        "end": end,
                        "length": length,
                        "score": window_score
                    })

                    if window_score > best_score:
                        best_score = window_score
                        best_window = (start, end)

            if best_window is None:
                st.warning("No valid calibration window found with the current settings.")
            else:
                st.success(f"Recommended global calibration period: {best_window[0]}–{best_window[1]} (score = {best_score:.3f})")

                # Plot score vs window center year
                scores_df = pd.DataFrame(window_scores)
                scores_df["center_year"] = (scores_df["start"] + scores_df["end"]) / 2

                fig_cal = px.scatter(
                    scores_df,
                    x="center_year",
                    y="score",
                    size="length",
                    title="Calibration Window Score vs Center Year",
                    labels={"center_year": "Window Center Year", "score": "Score"}
                )
                st.plotly_chart(fig_cal, use_container_width=True)

                st.caption("Higher scores indicate windows with lower missingness and more stable variance across stations.")




    # ============================================================
    # Step 6B — Climate Structure Verification
    # Calibration (2010–2019) vs Validation (2020–2024)
    # ============================================================

    import numpy as np
    import plotly.express as px

    st.header("6B. Climate Structure Verification (Calibration vs Validation)")

    # ------------------------------------------------------------
    # Load all NOAA daily data from existing local folder
    # ------------------------------------------------------------
    @st.cache_data
    def load_all_noaa_daily(folder="noaa_raw"):
        dfs = []
        for f in os.listdir(folder):
            if f.endswith(".csv"):
                df = pd.read_csv(os.path.join(folder, f))
                df["DATE"] = pd.to_datetime(df["DATE"])
                df["year"] = df["DATE"].dt.year
                dfs.append(df)
        return pd.concat(dfs, ignore_index=True)

    df_all = load_all_noaa_daily()

    # ------------------------------------------------------------
    # Annual regional precipitation (mean across stations → annual sum)
    # ------------------------------------------------------------
    annual_prcp = (
        df_all
        .groupby(["year", "DATE"])["PRCP"]
        .mean()          # spatial mean per day
        .groupby("year")
        .sum()           # annual total
        .reset_index()
    )

    # ------------------------------------------------------------
    # FIGURE 1 — Annual Precipitation (wet vs dry years)
    # ------------------------------------------------------------
    st.subheader("Annual Regional Precipitation")

    fig_prcp = px.bar(
        annual_prcp,
        x="year",
        y="PRCP",
        title="Annual Regional Precipitation – Pecos Watershed",
        labels={"PRCP": "Annual precipitation", "year": "Year"}
    )

    # Highlight calibration and validation periods
    fig_prcp.add_vrect(
        x0=2010, x1=2019,
        fillcolor="green", opacity=0.15, layer="below"
    )
    fig_prcp.add_vrect(
        x0=2020, x1=2024,
        fillcolor="red", opacity=0.15, layer="below"
    )

    fig_prcp.add_annotation(
        x=2014.5,
        y=annual_prcp["PRCP"].max() * 0.95,
        text="Calibration (2010–2019)",
        showarrow=False
    )
    fig_prcp.add_annotation(
        x=2022,
        y=annual_prcp["PRCP"].max() * 0.95,
        text="Validation (2020–2024)",
        showarrow=False
    )

    st.plotly_chart(fig_prcp, use_container_width=True)

    # ------------------------------------------------------------
    # FIGURE 2 — Standardized precipitation anomalies (objective)
    # ------------------------------------------------------------
    mean_prcp = annual_prcp["PRCP"].mean()
    std_prcp  = annual_prcp["PRCP"].std()

    annual_prcp["prcp_anomaly"] = (
        (annual_prcp["PRCP"] - mean_prcp) / std_prcp
    )

    st.subheader("Standardized Annual Precipitation Anomalies")

    fig_anom = px.bar(
        annual_prcp,
        x="year",
        y="prcp_anomaly",
        color="prcp_anomaly",
        color_continuous_scale="RdBu",
        title="Standardized Annual Precipitation Anomalies (z-score)",
        labels={"prcp_anomaly": "Standardized anomaly"}
    )

    fig_anom.add_hline(y=0, line_dash="dash")

    fig_anom.add_vrect(
        x0=2010, x1=2019,
        fillcolor="green", opacity=0.12, layer="below"
    )
    fig_anom.add_vrect(
        x0=2020, x1=2024,
        fillcolor="red", opacity=0.12, layer="below"
    )

    st.plotly_chart(fig_anom, use_container_width=True)

    st.caption(
        "Negative anomalies indicate dry years, while positive anomalies indicate wet years. "
        "The calibration period includes both wet and dry conditions, whereas the validation "
        "period is dominated by persistent negative anomalies."
    )

    # ------------------------------------------------------------
    # FIGURE 3 — Mean annual temperature (non-stationarity)
    # ------------------------------------------------------------
    df_all["TMEAN"] = (df_all["TMAX"] + df_all["TMIN"]) / 2

    annual_temp = (
        df_all
        .groupby("year")["TMEAN"]
        .mean()
        .reset_index()
    )

    st.subheader("Mean Annual Temperature")

    fig_temp = px.line(
        annual_temp,
        x="year",
        y="TMEAN",
        title="Mean Annual Temperature – Pecos Watershed",
        labels={"TMEAN": "Mean temperature"}
    )

    fig_temp.add_vrect(
        x0=2010, x1=2019,
        fillcolor="green", opacity=0.15, layer="below"
    )
    fig_temp.add_vrect(
        x0=2020, x1=2024,
        fillcolor="red", opacity=0.15, layer="below"
    )

    st.plotly_chart(fig_temp, use_container_width=True)

    st.caption(
        "The validation period is characterized by higher mean temperatures, "
        "confirming that model validation is performed under a warmer and more drought-dominated regime."
    )

