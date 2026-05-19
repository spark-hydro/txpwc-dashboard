"""
NOAA Climate Station Selector for SWAT+ — Pecos River Edition
==============================================================
Fully offline / pre-loaded version.

Required data files in noaa_selector/data/:
    stations_catalog.csv     — full catalog of NOAA GHCND stations
    pecos_basin.geojson      — Pecos River watershed
    pecos_buffer.geojson     — 30 km buffer

Required daily data in noaa_raw/ (current working dir):
    GHCND_*.csv              — daily PRCP/TMAX/TMIN files
"""

import os
import datetime
from pathlib import Path

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import MarkerCluster
from scipy.stats import linregress
from streamlit_folium import st_folium

try:
    from .scripts.export_swatplus import export_swatplus
    HAS_EXPORTER = True
except ImportError:
    HAS_EXPORTER = False

try:
    from components.sidebar import render_sidebar
    HAS_SIDEBAR = True
except ImportError:
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent.parent))
        from components.sidebar import render_sidebar  # type: ignore[import]
        HAS_SIDEBAR = True
    except ImportError:
        HAS_SIDEBAR = False


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

PACKAGE_DIR    = Path(__file__).parent
DATA_DIR       = PACKAGE_DIR / "data"
CATALOG_PATH   = DATA_DIR / "stations_catalog.csv"
BASIN_PATH     = DATA_DIR / "pecos_basin.geojson"
NOAA_RAW_DIR   = "noaa_raw"

BASIN_NAME     = "Pecos River"
BASIN_AREA_KM2 = 121_404


# ══════════════════════════════════════════════════════════════════════════════
# CACHED LOADERS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_catalog() -> pd.DataFrame:
    df = pd.read_csv(CATALOG_PATH)
    df["mindate"]    = pd.to_datetime(df["mindate"], errors="coerce")
    df["maxdate"]    = pd.to_datetime(df["maxdate"], errors="coerce")
    df["span_years"] = (df["maxdate"] - df["mindate"]).dt.days / 365.25

    q1, q2, q3 = df["elevation"].quantile([0.25, 0.5, 0.75])

    def _band(z):
        if pd.isna(z):
            return "NA"
        if z <= q1:
            return "low"
        if z <= q2:
            return "mid-low"
        if z <= q3:
            return "mid-high"
        return "high"

    df["elev_band"] = df["elevation"].apply(_band)
    return df


@st.cache_data
def load_basin():
    return gpd.read_file(BASIN_PATH)



@st.cache_data
def list_downloaded_stations(folder: str) -> set:
    if not os.path.isdir(folder):
        return set()
    return {
        f.replace(".csv", "").replace("_", ":")
        for f in os.listdir(folder)
        if f.endswith(".csv")
    }


@st.cache_data
def load_station_daily(station_id: str, folder: str) -> pd.DataFrame:
    fname = station_id.replace(":", "_") + ".csv"
    path  = os.path.join(folder, fname)
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["DATE"] = pd.to_datetime(df["DATE"])
    return df


@st.cache_data
def load_all_downloaded(folder: str) -> pd.DataFrame:
    dfs = []
    if not os.path.isdir(folder):
        return pd.DataFrame()
    for f in os.listdir(folder):
        if not f.endswith(".csv"):
            continue
        sid = f.replace(".csv", "").replace("_", ":")
        df  = pd.read_csv(os.path.join(folder, f))
        df["DATE"]       = pd.to_datetime(df["DATE"])
        df["year"]       = df["DATE"].dt.year
        df["station_id"] = sid
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILTERING LOGIC
# ══════════════════════════════════════════════════════════════════════════════

def apply_filters(catalog: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Multi-stage filtering, scoring, and spatial thinning.

    Order of operations (matches the original select_stations workflow):
      1) Recency filter      — station must still be active by min_active_year
      2) Span filter         — minimum total record length
      3) NOAA coverage       — minimum daily-data completeness reported by NOAA
      4) Calibration overlap — cover_frac >= min_cover_frac of the cal. window
      5) Elevation filters   — by absolute range and by quartile band
      6) Score               — 0.4*span + 0.4*cover_frac + 0.2*recency  (0–1 scale)
      7) Spatial thinning    — keep the highest-scored station, then drop any
                                neighbours within min_dist_km
    """
    df = catalog.copy()

    # ── 1. Recency: station active until at least this year ───────────────
    if filters.get("min_active_year"):
        df = df[df["maxdate"].dt.year >= filters["min_active_year"]]

    # ── 2. Span: minimum record length in years ───────────────────────────
    if filters.get("min_span_years"):
        df = df[df["span_years"] >= filters["min_span_years"]]

    # ── 3. NOAA reported data completeness ────────────────────────────────
    if filters.get("min_datacoverage"):
        df = df[df["datacoverage"] >= filters["min_datacoverage"]]

    # ── 4. Coverage of user's calibration window ──────────────────────────
    cal_start = filters.get("cal_start")
    cal_end   = filters.get("cal_end")
    if cal_start and cal_end:
        cal_start_ts = pd.Timestamp(cal_start)
        cal_end_ts   = pd.Timestamp(cal_end)
        cal_years    = cal_end_ts.year - cal_start_ts.year + 1

        def _years_in_cal(row):
            if pd.isna(row["mindate"]) or pd.isna(row["maxdate"]):
                return 0
            return max(0,
                       min(row["maxdate"].year, cal_end_ts.year) -
                       max(row["mindate"].year, cal_start_ts.year) + 1)

        df["years_in_cal"] = df.apply(_years_in_cal, axis=1)
        df["cover_frac"]   = df["years_in_cal"] / cal_years

        if filters.get("min_cover_frac"):
            df = df[df["cover_frac"] >= filters["min_cover_frac"]]
    else:
        df["cover_frac"] = np.nan

    # ── 5. Elevation filters ──────────────────────────────────────────────
    if filters.get("elev_min") is not None:
        df = df[df["elevation"] >= filters["elev_min"]]
    if filters.get("elev_max") is not None:
        df = df[df["elevation"] <= filters["elev_max"]]
    bands = filters.get("elev_bands")
    if bands:
        df = df[df["elev_band"].isin(bands)]

    if df.empty:
        df["score"] = np.nan
        return df.reset_index(drop=True)

    # ── 6. SCORE — 0.4*span + 0.4*cover + 0.2*recency ─────────────────────
    # All three components are normalized to [0, 1] using the FILTERED subset
    # so the score reflects relative quality within the user's selection.
    max_span = df["span_years"].max()
    span_norm = df["span_years"] / max_span if max_span > 0 else 0

    cover_norm = df["cover_frac"].fillna(0).clip(0, 1)

    min_yr = df["maxdate"].dt.year.min()
    max_yr = df["maxdate"].dt.year.max()
    if max_yr > min_yr:
        recency_norm = (df["maxdate"].dt.year - min_yr) / (max_yr - min_yr)
    else:
        recency_norm = pd.Series(1.0, index=df.index)

    df["span_norm"]    = span_norm
    df["cover_norm"]   = cover_norm
    df["recency_norm"] = recency_norm
    df["score"] = (
        0.4 * span_norm +
        0.4 * cover_norm +
        0.2 * recency_norm
    )

    df = df.sort_values("score", ascending=False)

    # ── 7. Spatial thinning by score ──────────────────────────────────────
    # Iterate top-down by score, drop neighbours within min_dist_km.
    min_dist_km = filters.get("min_dist_km", 0)
    if min_dist_km > 0:
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df.longitude, df.latitude),
            crs=4326
        ).to_crs(32613)

        keep = []
        used = set()
        threshold_m = min_dist_km * 1000
        for i, row in gdf.iterrows():
            if i in used:
                continue
            keep.append(i)
            dists = gdf.geometry.distance(row.geometry)
            used.update(dists[dists < threshold_m].index)
        df = df.loc[keep]

    return df.reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

def run_app():

    language = st.sidebar.selectbox("Language / Idioma", ["English", "Español"])

    def T(en, es):
        return en if language == "English" else es

    st.title(T(
        f"🌧️ NOAA Climate Stations — {BASIN_NAME} for SWAT+",
        f"🌧️ Estaciones Climáticas NOAA — {BASIN_NAME} para SWAT+"
    ))

    if not CATALOG_PATH.exists():
        st.error(T(
            f"Catalog not found at {CATALOG_PATH}. Run build_pecos_catalog.py first.",
            f"Catálogo no encontrado en {CATALOG_PATH}. Ejecuta build_pecos_catalog.py primero."
        ))
        st.stop()

    catalog        = load_catalog()
    basin          = load_basin()
    downloaded_ids = list_downloaded_stations(NOAA_RAW_DIR)

    step = st.sidebar.radio(
        T("Sections", "Secciones"),
        [
            T("🏠 Overview",             "🏠 Resumen"),
            T("🎛️ Filters & Selection", "🎛️ Filtros y Selección"),
            T("📊 Climate Analysis",    "📊 Análisis Climático"),
            T("🔬 Cal vs Val",           "🔬 Calibración vs Validación"),
            T("📦 Export SWAT+",         "📦 Exportar SWAT+"),
        ]
    )

    if "filters" not in st.session_state:
        st.session_state["filters"] = {
            "min_active_year":   2010,
            "min_span_years":    10,
            "min_datacoverage":  0.7,
            "cal_start":         datetime.date(2010, 1, 1),
            "cal_end":           datetime.date(2019, 12, 31),
            "min_cover_frac":    0.7,
            "elev_min":          int(catalog["elevation"].min()),
            "elev_max":          int(catalog["elevation"].max()),
            "elev_bands":        ["low", "mid-low", "mid-high", "high"],
            "min_dist_km":       15,
        }

    if HAS_SIDEBAR:
        render_sidebar()  # type: ignore[name-defined]


    # ══════════════════════════════════════════════════════════════════════════
    # OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    if step == T("🏠 Overview", "🏠 Resumen"):

        st.header(T(f"Welcome — {BASIN_NAME} Watershed",
                    f"Bienvenido — Cuenca del {BASIN_NAME}"))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(T("Watershed area", "Área de cuenca"), f"{BASIN_AREA_KM2:,} km²")
        col2.metric(T("Subbasins", "Subcuencas"), len(basin))
        col3.metric(T("Stations in catalog", "Estaciones en catálogo"), len(catalog))
        col4.metric(T("Already downloaded", "Ya descargadas"), len(downloaded_ids))

        st.markdown(T(
            f"""
            This app explores **{len(catalog)} NOAA GHCND climate stations** available
            in and around the **{BASIN_NAME}** watershed ({BASIN_AREA_KM2:,} km²,
            {len(basin)} subbasins). All stations are pre-loaded — no token or downloads needed.

            **What you can do:**
            1. 🎛️ Adjust filters and see in real time how the number of usable stations changes
            2. 📊 Analyze precipitation and temperature patterns across the watershed
            3. 🔬 Verify your calibration and validation periods are climatically representative
            4. 📦 Export ready-to-use SWAT+ climate files
            """,
            f"""
            Esta app explora **{len(catalog)} estaciones climáticas NOAA GHCND** disponibles
            en y alrededor de la cuenca del **{BASIN_NAME}** ({BASIN_AREA_KM2:,} km²,
            {len(basin)} subcuencas). Todas pre-cargadas — sin token ni descargas.

            **Qué puedes hacer:**
            1. 🎛️ Ajusta filtros y ve en tiempo real cómo cambia el número de estaciones útiles
            2. 📊 Analiza patrones de precipitación y temperatura en la cuenca
            3. 🔬 Verifica que tus periodos de calibración y validación sean representativos
            4. 📦 Exporta archivos climáticos listos para SWAT+
            """
        ))

        st.subheader(T("📈 Catalog at a glance", "📈 Catálogo de un vistazo"))

        col1, col2, col3 = st.columns(3)
        active_2020 = (catalog["maxdate"].dt.year >= 2020).sum()
        col1.metric(T("Active in 2020+", "Activas en 2020+"),
                    active_2020,
                    delta=f"{active_2020/len(catalog)*100:.0f}% {T('of catalog','del catálogo')}")
        long_record = (catalog["span_years"] >= 30).sum()
        col2.metric(T("≥ 30 years of record", "≥ 30 años de registro"),
                    long_record,
                    delta=T("historical value", "valor histórico"))
        density = BASIN_AREA_KM2 / len(catalog)
        col3.metric(T("Catalog density", "Densidad de catálogo"),
                    f"1 / {density:.0f} km²",
                    delta=T("WMO plains: 575 km²/sta", "OMM planicies: 575 km²/sta"))

        st.subheader(T("🗺️ All stations", "🗺️ Todas las estaciones"))
        st.caption(T(
            "Gray polygons show the 460 Pecos subbasins. The dashed blue line marks the "
            "watershed boundary. Click any marker for details. "
            "Use the next section to filter by quality.",
            "Los polígonos grises muestran las 460 subcuencas del Pecos. La línea azul "
            "punteada marca el límite de la cuenca. Haz clic en un marcador para más detalles. "
            "Usa la siguiente sección para filtrar por calidad."
        ))

        centroid_ov = basin.geometry.unary_union.centroid
        m_ov = folium.Map(
            location=[centroid_ov.y, centroid_ov.x],
            zoom_start=7,
            tiles="CartoDB positron",
        )

        # Subbasins
        folium.GeoJson(
            basin.to_json(),
            name=T("Subbasins (460)", "Subcuencas (460)"),
            style_function=lambda _: {
                "fillColor": "#cccccc", "fillOpacity": 0.15,
                "color": "#666666", "weight": 0.5,
            },
        ).add_to(m_ov)

        # Watershed outline (dashed)
        try:
            basin_outline_ov = gpd.GeoDataFrame(
                geometry=[basin.geometry.unary_union], crs=basin.crs
            )
            folium.GeoJson(
                basin_outline_ov.to_json(),
                name=T("Watershed boundary", "Límite de cuenca"),
                style_function=lambda _: {
                    "fillOpacity": 0, "color": "#003399", "weight": 2.5,
                    "dashArray": "8 5",
                },
            ).add_to(m_ov)
        except Exception:
            pass

        # Stations colored by elevation band (clustered)
        band_colors = {
            "low": "blue", "mid-low": "green",
            "mid-high": "orange", "high": "red", "NA": "gray",
        }
        cluster_ov = MarkerCluster(
            name=T(f"Stations ({len(catalog)})",
                   f"Estaciones ({len(catalog)})")
        ).add_to(m_ov)

        for row in catalog.itertuples():
            band = getattr(row, "elev_band", "NA")
            color = band_colors.get(band, "gray")
            popup_html = (
                f"<b>{row.name}</b><br>"
                f"<i>{getattr(row, 'id', '')}</i><br>"
                f"Elevation: {getattr(row, 'elevation', 0):.0f} m ({band})<br>"
                f"Record: {getattr(row, 'span_years', 0):.1f} yr<br>"
                f"NOAA coverage: {getattr(row, 'datacoverage', 0):.0%}"
            )
            folium.CircleMarker(
                location=[row.latitude, row.longitude],
                radius=4,
                color=color, fill=True, fill_opacity=0.7, weight=1,
                popup=folium.Popup(popup_html, max_width=250),
            ).add_to(cluster_ov)

        folium.LayerControl().add_to(m_ov)
        st_folium(m_ov, width=None, height=600,
                  returned_objects=[], use_container_width=True)

        st.subheader(T("📊 Catalog distributions", "📊 Distribuciones del catálogo"))
        col1, col2 = st.columns(2)
        with col1:
            fig_e = px.histogram(catalog, x="elevation", nbins=40, color="elev_band",
                                  color_discrete_map={
                                      "low": "#1f77b4", "mid-low": "#2ca02c",
                                      "mid-high": "#ff7f0e", "high": "#d62728",
                                  },
                                  title=T("Elevation (m)", "Elevación (m)"))
            st.plotly_chart(fig_e, use_container_width=True)
        with col2:
            fig_s = px.histogram(catalog, x="span_years", nbins=40,
                                  title=T("Record length (years)", "Longitud (años)"))
            st.plotly_chart(fig_s, use_container_width=True)

        st.subheader(T("📈 Stations active each year", "📈 Estaciones activas por año"))
        st.caption(T(
            "Network growth over time. The recent peak shows when most modern stations were installed.",
            "Crecimiento de la red. El pico reciente muestra cuándo se instalaron la mayoría."
        ))
        years = list(range(1900, 2026))
        active_counts = [
            ((catalog["mindate"] <= pd.Timestamp(f"{y}-06-01")) &
             (catalog["maxdate"] >= pd.Timestamp(f"{y}-06-01"))).sum()
            for y in years
        ]
        fig_act = px.area(x=years, y=active_counts,
                           labels={"x": T("Year", "Año"),
                                   "y": T("Stations active", "Estaciones activas")})
        st.plotly_chart(fig_act, use_container_width=True)

        st.info(T(
            f"➡️ Go to **🎛️ Filters & Selection** to narrow down these {len(catalog)} stations.",
            f"➡️ Ve a **🎛️ Filtros y Selección** para reducir estas {len(catalog)} estaciones."
        ))

        st.markdown(T(
            """
            ---
            🛠️ **Need this for your own watershed?**
            The standalone version of this tool works for **any basin worldwide**:

            🚀 [**Open the app**](https://noaa-station-selector.streamlit.app/) — upload your shapefile and export SWAT+ files in minutes
            &nbsp;&nbsp;&nbsp;&nbsp;📦 [Source code & docs](https://github.com/JosephAuresy/noaa-swat-station-selector)
            """,
            """
            ---
            🛠️ **¿Necesitas esto para tu propia cuenca?**
            La versión standalone de esta herramienta funciona para **cualquier cuenca del mundo**:

            🚀 [**Abrir la app**](https://noaa-station-selector.streamlit.app/) — sube tu shapefile y exporta archivos SWAT+ en minutos
            &nbsp;&nbsp;&nbsp;&nbsp;📦 [Código fuente y documentación](https://github.com/JosephAuresy/noaa-swat-station-selector)
            """
        ))

    # ══════════════════════════════════════════════════════════════════════════
    # FILTERS & SELECTION
    # ══════════════════════════════════════════════════════════════════════════
    elif step == T("🎛️ Filters & Selection", "🎛️ Filtros y Selección"):

        st.header(T("Interactive Station Selection",
                    "Selección Interactiva de Estaciones"))

        with st.expander(T("ℹ️ How does this work?", "ℹ️ ¿Cómo funciona?"), expanded=True):
            st.markdown(T(
                f"""
                You have **{len(catalog)} stations** available. Each filter on the left
                narrows the selection. The counters and map update **in real time** —
                try moving the sliders and watch the selection change.

                The goal is to find the **smallest, highest-quality subset** that:
                - Covers your watershed spatially
                - Has reliable data during your calibration period
                - Spans enough years to capture climate variability
                """,
                f"""
                Tienes **{len(catalog)} estaciones** disponibles. Cada filtro a la izquierda
                reduce la selección. Los contadores y el mapa se actualizan **en tiempo real**.

                El objetivo: encontrar el **subconjunto más pequeño y de mayor calidad** que:
                - Cubra tu cuenca espacialmente
                - Tenga datos confiables en tu periodo de calibración
                - Abarque suficientes años para capturar la variabilidad climática
                """
            ))

        st.sidebar.divider()
        st.sidebar.subheader(T("🎛️ Filters", "🎛️ Filtros"))
        f = st.session_state["filters"]

        f["min_active_year"] = st.sidebar.slider(
            T("Active until at least", "Activa al menos hasta"),
            1900, 2026, f["min_active_year"], 1,
            help=T("Station still recording in this year or later",
                   "La estación debe seguir activa en este año o después")
        )
        f["min_span_years"] = st.sidebar.slider(
            T("Min record length (years)", "Longitud mínima (años)"),
            0, 100, int(f["min_span_years"]),
            help=T(
                "Minimum total years of data the station must have. Longer records "
                "capture more climate variability and improve SWAT calibration.",
                "Años mínimos de datos que debe tener la estación. Registros más largos "
                "capturan más variabilidad climática y mejoran la calibración SWAT."
            )
        )
        f["min_datacoverage"] = st.sidebar.slider(
            T("Min NOAA coverage", "Cobertura NOAA mínima"),
            0.0, 1.0, float(f["min_datacoverage"]), 0.05,
            help=T(
                "NOAA's own estimate of daily data completeness (0 = no data, 1 = fully complete). "
                "Values below 0.7 usually indicate too many missing days for reliable analysis.",
                "Estimación de NOAA de la completitud de datos diarios (0 = sin datos, 1 = completo). "
                "Valores bajo 0.7 suelen indicar demasiados días faltantes para un análisis confiable."
            )
        )

        st.sidebar.markdown(T("**Calibration window**", "**Ventana de calibración**"))
        f["cal_start"] = st.sidebar.date_input(
            T("Calibration start", "Inicio calibración"),
            value=f["cal_start"],
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            help=T(
                "Start of your SWAT+ calibration period. Stations are scored on how much "
                "of this window they cover.",
                "Inicio de tu periodo de calibración SWAT+. Las estaciones se puntúan según "
                "qué tanto cubren esta ventana."
            )
        )
        f["cal_end"] = st.sidebar.date_input(
            T("Calibration end", "Fin calibración"),
            value=f["cal_end"],
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date(2100, 12, 31),
            help=T(
                "End of your SWAT+ calibration period.",
                "Fin de tu periodo de calibración SWAT+."
            )
        )
        f["min_cover_frac"] = st.sidebar.slider(
            T("Min coverage of cal. period", "Cobertura mín. del periodo cal."),
            0.0, 1.0, float(f["min_cover_frac"]), 0.05,
            help=T(
                "Fraction of calibration years the station must cover (e.g. 0.7 = at least 70% "
                "of the calibration window). Stations that went offline mid-period score lower.",
                "Fracción de los años de calibración que debe cubrir la estación (p.ej. 0.7 = al menos "
                "70% de la ventana). Estaciones que se apagaron a mitad del periodo puntúan más bajo."
            )
        )

        st.sidebar.markdown(T("**Elevation bands**", "**Bandas de elevación**"))
        f["elev_bands"] = st.sidebar.multiselect(
            T("Include bands", "Incluir bandas"),
            ["low", "mid-low", "mid-high", "high"],
            default=f["elev_bands"],
            help=T(
                "Elevation quartile bands computed from the full catalog. "
                "low = bottom 25%, mid-low = 25–50%, mid-high = 50–75%, high = top 25%. "
                "Keep all bands to ensure elevation diversity across the watershed.",
                "Bandas de cuartil de elevación calculadas sobre todo el catálogo. "
                "low = cuartil inferior, mid-low = 25–50%, mid-high = 50–75%, high = cuartil superior. "
                "Mantén todas las bandas para asegurar diversidad altitudinal en la cuenca."
            )
        )

        f["min_dist_km"] = st.sidebar.slider(
            T("Min spacing between stations (km)",
              "Distancia mínima entre estaciones (km)"),
            0, 100, int(f["min_dist_km"]),
            help=T("Spatial thinning to avoid redundancy",
                   "Reducción espacial para evitar redundancia")
        )

        filtered = apply_filters(catalog, f)
        st.session_state["filtered_stations"] = filtered

        # ── Executive summary ──
        st.subheader(T("📋 Executive Summary", "📋 Resumen Ejecutivo"))
        n_total     = len(catalog)
        n_sel       = len(filtered)
        density_sel = BASIN_AREA_KM2 / n_sel if n_sel else float("inf")
        n_with_data = filtered["id"].isin(downloaded_ids).sum() if not filtered.empty else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(T("Stations selected", "Estaciones seleccionadas"),
                    f"{n_sel}",
                    delta=f"-{n_total-n_sel} {T('filtered out','filtradas')}",
                    delta_color="off")
        col2.metric(T("% of catalog", "% del catálogo"),
                    f"{n_sel/n_total*100:.1f}%")
        col3.metric(T("Density (km²/station)", "Densidad (km²/estación)"),
                    f"{density_sel:.0f}" if n_sel else "—",
                    delta=T("WMO target: ≤ 575", "Meta OMM: ≤ 575"),
                    delta_color="normal" if density_sel <= 575 else "inverse")
        col4.metric(T("With local data", "Con datos locales"),
                    f"{n_with_data} / {n_sel}",
                    delta=T("ready for export", "listas para exportar"))

        if n_sel == 0:
            st.error(T("❌ No stations match filters. Relax criteria.",
                       "❌ Ninguna estación cumple. Relaja criterios."))
        elif n_sel < 4:
            st.warning(T(
                f"⚠️ Only {n_sel} stations — below SWAT practical minimum of 4.",
                f"⚠️ Solo {n_sel} estaciones — bajo mínimo SWAT de 4."
            ))
        elif density_sel > 575:
            st.info(T(
                f"ℹ️ {n_sel} stations is acceptable, but density (1/{density_sel:.0f} km²) "
                "is below WMO standard. Lower spacing to add more.",
                f"ℹ️ {n_sel} estaciones es aceptable, pero la densidad (1/{density_sel:.0f} km²) "
                "está bajo el estándar OMM. Reduce el espaciado para añadir más."
            ))
        else:
            st.success(T(
                f"✅ {n_sel} stations — meets SWAT and WMO standards.",
                f"✅ {n_sel} estaciones — cumple SWAT y OMM."
            ))

        # ── Live map ──
        st.subheader(T("🗺️ Selection map (live)", "🗺️ Mapa de selección (en vivo)"))

        with st.expander(T("ℹ️ How to read the map", "ℹ️ Cómo leer el mapa")):
            st.markdown(T(
                """
                - **Gray polygons**: the 460 subbasins of the Pecos watershed
                - **Blue dashed line**: watershed boundary
                - **🔴 Red markers**: stations selected by current filters
                - **⚪ Gray dots**: catalog stations that were filtered out
                - Click any selected station to see its score and quality stats
                """,
                """
                - **Polígonos grises**: las 460 subcuencas del Pecos
                - **Línea azul punteada**: límite de la cuenca hidrográfica
                - **🔴 Marcadores rojos**: estaciones seleccionadas por los filtros actuales
                - **⚪ Puntos grises**: estaciones del catálogo filtradas
                - Haz clic en una estación seleccionada para ver su score y calidad
                """
            ))

        # Build Folium map with subbasins + buffer + stations
        centroid = basin.geometry.unary_union.centroid
        m_sel = folium.Map(
            location=[centroid.y, centroid.x],
            zoom_start=7,
            tiles="CartoDB positron",
        )

        # Subbasins layer (gray polygons)
        folium.GeoJson(
            basin.to_json(),
            name=T("Subbasins (460)", "Subcuencas (460)"),
            style_function=lambda _: {
                "fillColor": "#cccccc", "fillOpacity": 0.15,
                "color": "#666666", "weight": 0.5,
            },
        ).add_to(m_sel)

        # Watershed outline (dashed)
        try:
            basin_outline = gpd.GeoDataFrame(
                geometry=[basin.geometry.unary_union], crs=basin.crs
            )
            folium.GeoJson(
                basin_outline.to_json(),
                name=T("Watershed boundary", "Límite de cuenca"),
                style_function=lambda _: {
                    "fillOpacity": 0, "color": "#003399", "weight": 2.5,
                    "dashArray": "8 5",
                },
            ).add_to(m_sel)
        except Exception:
            pass

        # Filtered-out stations as small gray circles
        excluded = catalog[~catalog["id"].isin(filtered["id"])]
        excluded_layer = folium.FeatureGroup(
            name=T(f"Filtered out ({len(excluded)})",
                   f"Filtradas ({len(excluded)})")
        )
        for row in excluded.itertuples():
            folium.CircleMarker(
                location=[row.latitude, row.longitude],
                radius=2, color="#999999",
                fill=True, fill_opacity=0.4, weight=0,
            ).add_to(excluded_layer)
        excluded_layer.add_to(m_sel)

        # Selected stations as red markers with score in popup
        cluster = MarkerCluster(
            name=T(f"Selected stations ({len(filtered)})",
                   f"Estaciones seleccionadas ({len(filtered)})")
        ).add_to(m_sel)

        for row in filtered.itertuples():
            score_val = getattr(row, "score", float("nan"))
            cov_val   = getattr(row, "cover_frac", float("nan"))
            span_val  = getattr(row, "span_years", float("nan"))
            popup_html = (
                f"<b>{row.name}</b><br>"
                f"<i>{getattr(row, 'id', '')}</i><br>"
                f"Elevation: {getattr(row, 'elevation', 0):.0f} m "
                f"({getattr(row, 'elev_band', 'NA')})<br>"
                f"Record: {span_val:.1f} yr<br>"
                f"Cal coverage: {cov_val:.0%}<br>"
                f"<b>Score: {score_val:.3f}</b>"
            )
            folium.Marker(
                location=[row.latitude, row.longitude],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color="red", icon="cloud", prefix="fa"),
            ).add_to(cluster)

        folium.LayerControl().add_to(m_sel)
        st_folium(m_sel, width=None, height=600,
                  returned_objects=[], use_container_width=True)

        if not filtered.empty:

            # ── Score explanation ─────────────────────────────────────────
            st.subheader(T("🎯 Quality score", "🎯 Puntaje de calidad"))

            with st.expander(T("ℹ️ How is the score calculated?",
                               "ℹ️ ¿Cómo se calcula el puntaje?"), expanded=False):
                st.markdown(T(
                    """
                    Each surviving station receives a composite **quality score** from 0 to 1
                    that combines three normalized factors:

                    | Component | Weight | What it rewards |
                    |---|---|---|
                    | **Record span** | 40% | Stations with longer histories — better for climate trends |
                    | **Calibration coverage** | 40% | Stations that cover most of your chosen calibration window |
                    | **Recency** | 20% | Stations that are still active recently — relevant for current land use |

                    **Formula:**
                    `score = 0.4 × span_norm + 0.4 × cover_frac + 0.2 × recency_norm`

                    The score is used to drive **spatial thinning**: when two stations are within
                    the minimum spacing distance, the one with the higher score is kept.
                    This is why thinning is **not random** — it preserves the best stations.
                    """,
                    """
                    Cada estación que sobrevive recibe un **puntaje de calidad** compuesto entre 0 y 1
                    que combina tres factores normalizados:

                    | Componente | Peso | Qué premia |
                    |---|---|---|
                    | **Longitud de registro** | 40% | Estaciones con historias largas — mejor para tendencias |
                    | **Cobertura de calibración** | 40% | Estaciones que cubren la mayor parte de tu ventana |
                    | **Recencia** | 20% | Estaciones aún activas recientemente — relevante para uso de suelo actual |

                    **Fórmula:**
                    `score = 0.4 × span_norm + 0.4 × cover_frac + 0.2 × recency_norm`

                    El puntaje se usa para el **thinning espacial**: cuando dos estaciones están
                    dentro de la distancia mínima, se mantiene la de mayor puntaje. Por eso
                    el thinning **no es aleatorio** — preserva las mejores estaciones.
                    """
                ))

            # Score metrics
            if "score" in filtered.columns:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric(T("Mean score", "Score promedio"),
                            f"{filtered['score'].mean():.3f}")
                col2.metric(T("Best score", "Mejor score"),
                            f"{filtered['score'].max():.3f}")
                col3.metric(T("Worst score", "Peor score"),
                            f"{filtered['score'].min():.3f}")
                # Top station name
                top = filtered.loc[filtered["score"].idxmax()]
                col4.metric(T("Top station", "Mejor estación"),
                            top["name"][:25] + ("…" if len(top["name"]) > 25 else ""))

                fig_score = px.histogram(
                    filtered, x="score", nbins=25,
                    color_discrete_sequence=["#d62728"],
                    title=T("Distribution of station scores",
                            "Distribución de puntajes de estaciones"),
                )
                fig_score.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_score, use_container_width=True)

            # ── Selection quality breakdown ───────────────────────────────
            st.subheader(T("📊 Selection quality", "📊 Calidad de la selección"))
            col1, col2, col3 = st.columns(3)
            with col1:
                bands_count = filtered["elev_band"].value_counts().reindex(
                    ["low", "mid-low", "mid-high", "high"], fill_value=0
                )
                fig_b = px.bar(x=bands_count.index, y=bands_count.values,
                                color=bands_count.index,
                                color_discrete_map={
                                    "low": "#1f77b4", "mid-low": "#2ca02c",
                                    "mid-high": "#ff7f0e", "high": "#d62728",
                                },
                                labels={"x": "", "y": T("Stations","Estaciones")})
                fig_b.update_layout(showlegend=False, height=300,
                                     title=T("Elevation distribution","Distribución elevación"))
                st.plotly_chart(fig_b, use_container_width=True)
            with col2:
                fig_sp = px.histogram(filtered, x="span_years", nbins=20,
                                       title=T("Record length (years)","Longitud (años)"))
                fig_sp.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_sp, use_container_width=True)
            with col3:
                fig_dc = px.histogram(filtered, x="datacoverage", nbins=20,
                                       title=T("NOAA daily coverage","Cobertura diaria NOAA"))
                fig_dc.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_dc, use_container_width=True)

        with st.expander(T("📋 Detailed selection table",
                           "📋 Tabla detallada de selección")):
            cols_show = [c for c in ["name", "id", "elevation", "elev_band",
                                      "span_years", "datacoverage",
                                      "cover_frac", "score",
                                      "mindate", "maxdate"]
                          if c in filtered.columns]
            disp = filtered[cols_show].copy()
            if "id" in disp.columns:
                disp[T("Has local data", "Datos locales")] = \
                    disp["id"].isin(downloaded_ids).map({True: "✅", False: "❌"})
            # Sort by score descending so best stations show first
            if "score" in disp.columns:
                disp = disp.sort_values("score", ascending=False)
            st.dataframe(disp, use_container_width=True)
            st.download_button(
                T("⬇️ Download selection (CSV)", "⬇️ Descargar selección (CSV)"),
                data=filtered.to_csv(index=False).encode(),
                file_name="pecos_selection.csv",
                mime="text/csv",
            )

    # ══════════════════════════════════════════════════════════════════════════
    # CLIMATE ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    elif step == T("📊 Climate Analysis", "📊 Análisis Climático"):

        st.header(T("Climate Analysis Dashboard",
                    "Dashboard de Análisis Climático"))

        if "filtered_stations" not in st.session_state:
            st.session_state["filtered_stations"] = apply_filters(
                catalog, st.session_state["filters"]
            )
        filtered = st.session_state["filtered_stations"]

        if not downloaded_ids:
            st.error(T(
                f"No data in `{NOAA_RAW_DIR}/`. Climate analysis needs daily files.",
                f"Sin datos en `{NOAA_RAW_DIR}/`. El análisis necesita archivos diarios."
            ))
            st.stop()

        analyzable = filtered[filtered["id"].isin(downloaded_ids)] if not filtered.empty \
                     else catalog[catalog["id"].isin(downloaded_ids)]

        st.info(T(
            f"Analyzing **{len(analyzable)} stations** matching current filters AND with local data.",
            f"Analizando **{len(analyzable)} estaciones** que cumplen filtros Y tienen datos locales."
        ))

        if analyzable.empty:
            st.warning(T("No stations match. Relax filters.",
                         "Ninguna estación coincide. Relaja filtros."))
            st.stop()

        df_all = load_all_downloaded(NOAA_RAW_DIR)
        df_all = df_all[df_all["station_id"].isin(analyzable["id"])]
        if df_all.empty:
            st.warning(T("No data after filtering.", "Sin datos tras filtrar."))
            st.stop()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            T("🌡️ Walter-Lieth",     "🌡️ Walter-Lieth"),
            T("📅 Calendar Heatmap", "📅 Mapa Calendario"),
            T("🌵 SPI Drought Index","🌵 Índice de Sequía SPI"),
            T("📈 Trends",            "📈 Tendencias"),
            T("🔍 Single Station",    "🔍 Estación Individual"),
        ])

        # ── Walter-Lieth ──
        with tab1:
            st.subheader(T("Walter-Lieth Climatogram (regional mean)",
                           "Climatograma Walter-Lieth (media regional)"))
            with st.expander(T("ℹ️ What is this?", "ℹ️ ¿Qué es esto?")):
                st.markdown(T(
                    """
                    The classic climate characterization tool. Overlays monthly precipitation
                    (blue) and temperature (red) with the **precipitation axis at 2× the
                    temperature axis**.

                    - **Red line above blue** = dry/arid season
                    - **Blue line above red** = humid season
                    """,
                    """
                    Herramienta clásica de caracterización. Superpone precipitación mensual
                    (azul) y temperatura (roja), con el **eje de precipitación a 2× el eje de
                    temperatura**.

                    - **Línea roja sobre azul** = estación seca/árida
                    - **Línea azul sobre roja** = estación húmeda
                    """
                ))

            df_wl = df_all.copy()
            df_wl["month"] = df_wl["DATE"].dt.month
            df_wl["TMEAN"] = (df_wl["TMAX"] + df_wl["TMIN"]) / 2

            monthly = df_wl.groupby("month").agg(
                PRCP=("PRCP", "mean"),
                TMEAN=("TMEAN", "mean"),
            ).reset_index()
            days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            monthly["PRCP"] = monthly["PRCP"] * pd.Series(days)

            fig_wl = go.Figure()
            fig_wl.add_trace(go.Bar(
                x=monthly["month"], y=monthly["PRCP"],
                name=T("Precipitation (mm)", "Precipitación (mm)"),
                marker_color="rgba(31,119,180,0.6)", yaxis="y",
            ))
            fig_wl.add_trace(go.Scatter(
                x=monthly["month"], y=monthly["TMEAN"],
                name=T("Mean T (°C)", "T media (°C)"),
                line=dict(color="crimson", width=3), yaxis="y2",
            ))
            month_names = (["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                            if language == "English"
                            else ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"])
            fig_wl.update_layout(
                title=T(f"Walter-Lieth — {BASIN_NAME} ({len(analyzable)} stations)",
                        f"Walter-Lieth — {BASIN_NAME} ({len(analyzable)} estaciones)"),
                xaxis=dict(tickmode="array", tickvals=list(range(1,13)), ticktext=month_names),
                yaxis=dict(title=T("Precipitation (mm)","Precipitación (mm)"),
                           side="left", color="#1f77b4"),
                yaxis2=dict(title=T("Temperature (°C)","Temperatura (°C)"),
                            side="right", overlaying="y", color="crimson"),
                hovermode="x unified",
            )
            st.plotly_chart(fig_wl, use_container_width=True)

            wet_months = (monthly["PRCP"] / 2 > monthly["TMEAN"]).sum()
            arid = wet_months < 3
            st.markdown(T(
                f"**Interpretation:** {wet_months}/12 humid months. "
                + ("This is an **arid to semi-arid climate** — typical for Pecos."
                   if arid else
                   "This indicates a **sub-humid to humid climate**."),
                f"**Interpretación:** {wet_months}/12 meses húmedos. "
                + ("Clima **árido a semiárido** — típico del Pecos."
                   if arid else
                   "Clima **sub-húmedo a húmedo**.")
            ))

        # ── Calendar Heatmap ──
        with tab2:
            st.subheader(T("Calendar Heatmap — Daily Precipitation",
                           "Mapa Calendario — Precipitación Diaria"))
            with st.expander(T("ℹ️ How to read this", "ℹ️ Cómo leer esto")):
                st.markdown(T(
                    """
                    Each cell = one day. Y-axis = years, X-axis = day of year.
                    Darker blue = wetter. This reveals:
                    - **Seasonal patterns** (wet seasons each year)
                    - **Extreme events** (dark isolated dots)
                    - **Drought years** (pale rows)
                    - **Changes over time** (compare top vs bottom)
                    """,
                    """
                    Cada celda = un día. Eje Y = años, eje X = día del año.
                    Azul más oscuro = más húmedo. Revela:
                    - **Patrones estacionales** (temporadas húmedas)
                    - **Eventos extremos** (puntos oscuros aislados)
                    - **Años de sequía** (filas pálidas)
                    - **Cambios en el tiempo** (compara arriba vs abajo)
                    """
                ))

            df_cal = df_all.groupby("DATE")["PRCP"].mean().reset_index()
            df_cal["year"] = df_cal["DATE"].dt.year
            df_cal["doy"]  = df_cal["DATE"].dt.dayofyear

            recent_cutoff = df_cal["year"].max() - 30
            df_cal_recent = df_cal[df_cal["year"] >= recent_cutoff]

            pivot = df_cal_recent.pivot_table(
                index="year", columns="doy", values="PRCP", aggfunc="mean"
            )
            fig_cal = px.imshow(
                pivot, color_continuous_scale="YlGnBu", aspect="auto",
                labels=dict(x=T("Day of year","Día del año"),
                            y=T("Year","Año"),
                            color=T("PRCP (mm)","PRCP (mm)")),
                title=T(f"Daily PRCP by year — {BASIN_NAME}",
                        f"PRCP diaria por año — {BASIN_NAME}"),
                height=600,
            )
            st.plotly_chart(fig_cal, use_container_width=True)

        # ── SPI + SPEI ──
        with tab3:
            st.subheader(T("🌧️ SPI & SPEI Drought Indices",
                           "🌧️ Índices de Sequía SPI y SPEI"))

            with st.expander(T("ℹ️ SPI vs SPEI — what's the difference?",
                               "ℹ️ SPI vs SPEI — ¿cuál es la diferencia?"), expanded=True):
                st.markdown(T(
                    """
                    | | 🔵 SPI | 🟣 SPEI |
                    |---|---|---|
                    | **Measures** | Precipitation only | Water balance (P − PET) |
                    | **Data needed** | PRCP | PRCP + temperature |
                    | **PET method** | — | Thornthwaite (temperature-based) |
                    | **Captures** | Rainfall deficits | Drought stress incl. heat effects |
                    | **Best for** | Streamflow, recharge | Soil moisture, vegetation stress |

                    **When do they diverge?** In warm years, SPEI shows drier conditions than SPI
                    because higher temperatures raise evaporation demand even if rainfall is normal.
                    For SWAT: include **both negative and positive index years** in your calibration period.

                    | Value | Drought class |
                    |---|---|
                    | < −2.0 | Extreme drought |
                    | −2.0 to −1.5 | Severe drought |
                    | −1.5 to −1.0 | Moderate drought |
                    | −1.0 to 1.0 | Near normal |
                    | > 1.0 | Wet · > 2.0 Extremely wet |
                    """,
                    """
                    | | 🔵 SPI | 🟣 SPEI |
                    |---|---|---|
                    | **Mide** | Solo precipitación | Balance hídrico (P − ETP) |
                    | **Datos necesarios** | PRCP | PRCP + temperatura |
                    | **Método ETP** | — | Thornthwaite (basado en temperatura) |
                    | **Captura** | Déficits de lluvia | Estrés hídrico incl. efecto del calor |
                    | **Ideal para** | Escorrentía, recarga | Humedad de suelo, vegetación |

                    **¿Cuándo divergen?** En años cálidos, el SPEI muestra condiciones más secas que el SPI
                    porque temperaturas altas aumentan la demanda evaporativa aunque llueva normal.
                    Para SWAT: incluye **años negativos Y positivos** en tu periodo de calibración.

                    | Valor | Clase |
                    |---|---|
                    | < −2.0 | Sequía extrema |
                    | −2.0 a −1.5 | Sequía severa |
                    | −1.5 a −1.0 | Sequía moderada |
                    | −1.0 a 1.0 | Cerca de lo normal |
                    | > 1.0 | Húmedo · > 2.0 Extremadamente húmedo |
                    """
                ))

            def _cls(s):
                if s < -2:   return T("Extreme drought",  "Sequía extrema")
                if s < -1.5: return T("Severe drought",   "Sequía severa")
                if s < -1:   return T("Moderate drought", "Sequía moderada")
                if s < 1:    return T("Near normal",      "Cerca de lo normal")
                if s < 1.5:  return T("Moderately wet",   "Moderadamente húmedo")
                if s < 2:    return T("Severely wet",     "Severamente húmedo")
                return           T("Extremely wet",       "Extremadamente húmedo")

            # ── 🔵 SPI ──────────────────────────────────────────────────────
            st.markdown(T("### 🔵 SPI — Standardized Precipitation Index",
                          "### 🔵 SPI — Índice Estandarizado de Precipitación"))

            annual_spi = df_all.groupby(["year","DATE"])["PRCP"].mean() \
                                .groupby("year").sum().reset_index()
            mean_p = annual_spi["PRCP"].mean()
            std_p  = annual_spi["PRCP"].std()
            annual_spi["SPI"]   = (annual_spi["PRCP"] - mean_p) / std_p
            annual_spi["class"] = annual_spi["SPI"].apply(_cls)

            fig_spi = px.bar(
                annual_spi, x="year", y="SPI", color="SPI",
                color_continuous_scale="RdBu", color_continuous_midpoint=0,
                hover_data=["class", "PRCP"],
                title=T(f"Annual SPI — {BASIN_NAME}", f"SPI Anual — {BASIN_NAME}"),
            )
            fig_spi.add_hline(y=0, line_dash="dash")
            fig_spi.add_hline(y=-1, line_dash="dot", line_color="orange",
                              annotation_text=T("Drought", "Sequía"))
            fig_spi.add_hline(y=1, line_dash="dot", line_color="lightblue",
                              annotation_text=T("Wet", "Húmedo"))
            st.plotly_chart(fig_spi, use_container_width=True)

            n_tot       = len(annual_spi)
            n_dr_spi    = int((annual_spi["SPI"] < -1).sum())
            n_wet_spi   = int((annual_spi["SPI"] >  1).sum())
            st.caption(T(
                f"🔵 SPI — {n_tot} years: {n_dr_spi} drought "
                f"({n_dr_spi/n_tot*100:.0f}%), {n_wet_spi} wet ({n_wet_spi/n_tot*100:.0f}%).",
                f"🔵 SPI — {n_tot} años: {n_dr_spi} sequía "
                f"({n_dr_spi/n_tot*100:.0f}%), {n_wet_spi} húmedos ({n_wet_spi/n_tot*100:.0f}%)."
            ))

            st.divider()

            # ── 🟣 SPEI (Thornthwaite PET) ──────────────────────────────────
            st.markdown(T(
                "### 🟣 SPEI — Standardized Precipitation-Evapotranspiration Index",
                "### 🟣 SPEI — Índice Estandarizado de Precipitación-Evapotranspiración"
            ))

            df_spei        = df_all.copy()
            df_spei["TMEAN"] = (df_spei["TMAX"] + df_spei["TMIN"]) / 2
            df_spei["month"] = df_spei["DATE"].dt.month

            monthly_agg = (
                df_spei.groupby(["year", "month"])
                .agg(PRCP=("PRCP", "sum"), TMEAN=("TMEAN", "mean"))
                .reset_index()
            )
            has_temp = monthly_agg["TMEAN"].notna().mean() > 0.3

            if not has_temp:
                st.info(T(
                    "⚠️ Insufficient temperature data (TMAX/TMIN) for SPEI. "
                    "Download stations with temperature records to enable this index.",
                    "⚠️ Datos de temperatura (TMAX/TMIN) insuficientes para el SPEI. "
                    "Descarga estaciones con registros de temperatura para habilitar este índice."
                ))
            else:
                mean_lat = float(analyzable["latitude"].mean())
                lat_rad  = np.radians(mean_lat)

                # Long-term monthly means → Thornthwaite heat index (I) and exponent (a)
                lt_T     = (monthly_agg.groupby("month")["TMEAN"]
                            .mean().reindex(range(1, 13)).fillna(0).values)
                I_lt     = float(np.sum(np.maximum(lt_T, 0.0) ** 1.514) / (5.0 ** 1.514))
                # Standard formulation: i_m = (T_m/5)^1.514, I = sum(i_m)
                I_lt     = float(np.sum((np.maximum(lt_T, 0.0) / 5.0) ** 1.514))
                a_lt     = (6.75e-7 * I_lt**3 - 7.71e-5 * I_lt**2
                            + 1.792e-2 * I_lt + 0.49239) if I_lt > 0 else 0.0

                _days  = {1:31,2:28,3:31,4:30,5:31,6:30,
                          7:31,8:31,9:30,10:31,11:30,12:31}
                _midoy = {1:17,2:47,3:75,4:105,5:135,6:162,
                          7:198,8:228,9:258,10:288,11:318,12:344}

                def _pet(T_val, month):
                    if pd.isna(T_val) or T_val <= 0 or I_lt == 0:
                        return 0.0
                    doy  = _midoy[month]
                    decl = np.radians(23.45 * np.sin(np.radians(360 / 365 * (doy - 81))))
                    N    = 24.0 * np.arccos(
                               float(np.clip(-np.tan(lat_rad) * np.tan(decl), -1, 1))
                           ) / np.pi
                    cf   = (N / 12.0) * (_days[month] / 30.0)
                    return max(0.0, 16.0 * (10.0 * T_val / I_lt) ** a_lt * cf)

                monthly_agg["PET"] = [
                    _pet(r.TMEAN, r.month) for r in monthly_agg.itertuples()
                ]
                monthly_agg["WB"] = monthly_agg["PRCP"] - monthly_agg["PET"]

                annual_spei = (
                    monthly_agg.groupby("year")
                    .agg(WB=("WB","sum"), PET=("PET","sum"), PRCP=("PRCP","sum"))
                    .reset_index()
                )
                mean_wb = annual_spei["WB"].mean()
                std_wb  = annual_spei["WB"].std()
                annual_spei["SPEI"]  = (annual_spei["WB"] - mean_wb) / std_wb
                annual_spei["class"] = annual_spei["SPEI"].apply(_cls)

                fig_spei = px.bar(
                    annual_spei, x="year", y="SPEI", color="SPEI",
                    color_continuous_scale="PuOr_r", color_continuous_midpoint=0,
                    hover_data=["class", "WB", "PET", "PRCP"],
                    title=T(
                        f"Annual SPEI (Thornthwaite PET) — {BASIN_NAME}",
                        f"SPEI Anual (ETP Thornthwaite) — {BASIN_NAME}"
                    ),
                )
                fig_spei.add_hline(y=0, line_dash="dash")
                fig_spei.add_hline(y=-1, line_dash="dot", line_color="orange",
                                   annotation_text=T("Drought", "Sequía"))
                fig_spei.add_hline(y=1, line_dash="dot", line_color="purple",
                                   annotation_text=T("Wet", "Húmedo"))
                st.plotly_chart(fig_spei, use_container_width=True)

                n_dr_spei  = int((annual_spei["SPEI"] < -1).sum())
                n_wet_spei = int((annual_spei["SPEI"] >  1).sum())
                n_tot_s    = len(annual_spei)
                mean_pet   = annual_spei["PET"].mean()
                st.caption(T(
                    f"🟣 SPEI — {n_tot_s} years: {n_dr_spei} drought "
                    f"({n_dr_spei/n_tot_s*100:.0f}%), {n_wet_spei} wet "
                    f"({n_wet_spei/n_tot_s*100:.0f}%). "
                    f"Mean annual PET: {mean_pet:.0f} mm "
                    f"(Thornthwaite, lat {mean_lat:.1f}°N).",
                    f"🟣 SPEI — {n_tot_s} años: {n_dr_spei} sequía "
                    f"({n_dr_spei/n_tot_s*100:.0f}%), {n_wet_spei} húmedos "
                    f"({n_wet_spei/n_tot_s*100:.0f}%). "
                    f"ETP media anual: {mean_pet:.0f} mm "
                    f"(Thornthwaite, lat {mean_lat:.1f}°N)."
                ))

        # ── Trends ──
        with tab4:
            st.subheader(T("Long-term Climate Trends", "Tendencias Climáticas"))

            annual_p = df_all.groupby(["year","DATE"])["PRCP"].mean() \
                              .groupby("year").sum().reset_index()
            df_t = df_all.copy()
            df_t["TMEAN"] = (df_t["TMAX"] + df_t["TMIN"]) / 2
            annual_t = df_t.groupby("year")["TMEAN"].mean().reset_index()

            col1, col2 = st.columns(2)
            with col1:
                fig_p = px.scatter(annual_p, x="year", y="PRCP", trendline="ols",
                                    title=T("Annual PRCP with trend","PRCP anual con tendencia"))
                st.plotly_chart(fig_p, use_container_width=True)
                if len(annual_p) > 2:
                    slope, _, r, p, _ = linregress(annual_p["year"], annual_p["PRCP"])
                    sig = T("significant (p<0.05)","significativa (p<0.05)") if p < 0.05 \
                          else T("not significant","no significativa")
                    st.metric(T("PRCP trend","Tendencia PRCP"),
                              f"{slope*10:+.1f} mm/decade",
                              delta=f"R²={r**2:.2f} · {sig}")

            with col2:
                fig_tf = px.scatter(annual_t, x="year", y="TMEAN", trendline="ols",
                                     title=T("Annual T with trend","T anual con tendencia"))
                st.plotly_chart(fig_tf, use_container_width=True)
                if len(annual_t) > 2:
                    slope_t, _, r_t, p_t, _ = linregress(annual_t["year"], annual_t["TMEAN"])
                    sig_t = T("significant (p<0.05)","significativa (p<0.05)") if p_t < 0.05 \
                            else T("not significant","no significativa")
                    st.metric(T("Temperature trend","Tendencia T"),
                              f"{slope_t*10:+.2f} °C/decade",
                              delta=f"R²={r_t**2:.2f} · {sig_t}")

        # ── Single station ──
        with tab5:
            st.subheader(T("Inspect a single station","Inspeccionar una estación"))
            station_choice = st.selectbox(
                T("Select","Seleccionar"),
                analyzable["name"] + " — " + analyzable["id"],
            )
            sid_one = station_choice.split(" — ")[-1]
            df_one  = load_station_daily(sid_one, NOAA_RAW_DIR)

            if df_one.empty:
                st.warning(T("No data.","Sin datos."))
            else:
                meta = analyzable[analyzable["id"] == sid_one].iloc[0]
                col1, col2, col3 = st.columns(3)
                col1.metric(T("Elevation","Elevación"), f"{meta['elevation']:.0f} m")
                col2.metric(T("Record length","Longitud"), f"{meta['span_years']:.1f} yr")
                col3.metric(T("NOAA coverage","Cobertura NOAA"), f"{meta['datacoverage']:.0%}")

                ann = df_one.copy()
                ann["year"] = ann["DATE"].dt.year
                ann_p = ann.groupby("year")["PRCP"].sum().reset_index()
                if not ann_p.empty:
                    p25, p75 = ann_p["PRCP"].quantile([0.25, 0.75])
                    ann_p["type"] = ann_p["PRCP"].apply(
                        lambda v: T("Dry","Seco") if v < p25
                        else (T("Wet","Húmedo") if v > p75 else T("Normal","Normal"))
                    )
                    fig_one = px.bar(
                        ann_p, x="year", y="PRCP", color="type",
                        color_discrete_map={
                            T("Dry","Seco"): "#d62728",
                            T("Normal","Normal"): "#aec7e8",
                            T("Wet","Húmedo"): "#1f77b4",
                        },
                        title=T(f"Annual PRCP — {meta['name']}",
                                f"PRCP anual — {meta['name']}"),
                    )
                    st.plotly_chart(fig_one, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # CAL VS VAL
    # ══════════════════════════════════════════════════════════════════════════
    elif step == T("🔬 Cal vs Val", "🔬 Calibración vs Validación"):

        st.header(T("Calibration vs Validation Climate Verification",
                    "Verificación Climática Calibración vs Validación"))

        with st.expander(T("ℹ️ Why this matters","ℹ️ Por qué importa"), expanded=True):
            st.markdown(T(
                """
                SWAT is calibrated on one period and validated on a different one
                the model has **never seen**. This tests true generalization.

                **The key question:** are the two periods climatically comparable?
                - If validation is much drier/warmer, expect lower NSE in validation.
                  This is **not a failure** — it's a stress test under unseen conditions.
                  Document this honestly.
                - If both periods look identical, your validation isn't testing much.
                """,
                """
                SWAT se calibra en un periodo y se valida en otro que el modelo **nunca vio**.
                Esto prueba si realmente generaliza.

                **Pregunta clave:** ¿son los dos periodos climáticamente comparables?
                - Si la validación es más seca/cálida, espera NSE más bajo. Esto **no es un fallo** —
                  es una prueba de estrés bajo condiciones no entrenadas. Documéntalo honestamente.
                - Si ambos lucen idénticos, la validación no prueba mucho.
                """
            ))

        f = st.session_state["filters"]
        col1, col2 = st.columns(2)
        with col1:
            cal_s = st.date_input(T("Calibration start","Inicio calibración"),
                                  value=f["cal_start"], key="cv_cal_s")
            cal_e = st.date_input(T("Calibration end","Fin calibración"),
                                  value=f["cal_end"], key="cv_cal_e")
        with col2:
            val_s = st.date_input(T("Validation start","Inicio validación"),
                                  value=datetime.date(2020, 1, 1), key="cv_val_s")
            val_e = st.date_input(T("Validation end","Fin validación"),
                                  value=datetime.date(2024, 12, 31), key="cv_val_e")

        df_all = load_all_downloaded(NOAA_RAW_DIR)
        if df_all.empty:
            st.warning(T("No data.","Sin datos."))
            st.stop()

        df_all["TMEAN"] = (df_all["TMAX"] + df_all["TMIN"]) / 2
        annual_p = df_all.groupby(["year","DATE"])["PRCP"].mean() \
                          .groupby("year").sum().reset_index()
        annual_t = df_all.groupby("year")["TMEAN"].mean().reset_index()

        cal_label = T("Calibration","Calibración")
        val_label = T("Validation","Validación")

        def _period(yr):
            if cal_s.year <= yr <= cal_e.year: return cal_label
            if val_s.year <= yr <= val_e.year: return val_label
            return T("Outside","Fuera")

        annual_p["period"] = annual_p["year"].apply(_period)
        annual_t["period"] = annual_t["year"].apply(_period)

        comp_p = annual_p[annual_p["period"].isin([cal_label, val_label])]
        comp_t = annual_t[annual_t["period"].isin([cal_label, val_label])]

        st.subheader(T("📦 Side-by-side comparison","📦 Comparación lado a lado"))
        col1, col2 = st.columns(2)
        with col1:
            fig_pb = px.box(comp_p, x="period", y="PRCP", color="period",
                             points="all",
                             color_discrete_map={cal_label:"#2ca02c", val_label:"#d62728"},
                             title=T("Annual precipitation","Precipitación anual"))
            st.plotly_chart(fig_pb, use_container_width=True)
        with col2:
            fig_tb = px.box(comp_t, x="period", y="TMEAN", color="period",
                             points="all",
                             color_discrete_map={cal_label:"#2ca02c", val_label:"#d62728"},
                             title=T("Annual mean temperature","Temperatura media anual"))
            st.plotly_chart(fig_tb, use_container_width=True)

        st.subheader(T("📈 Timeline view","📈 Vista temporal"))
        mean_p_all = annual_p["PRCP"].mean()
        std_p_all  = annual_p["PRCP"].std()
        annual_p["SPI"] = (annual_p["PRCP"] - mean_p_all) / std_p_all

        fig_tl = px.bar(annual_p, x="year", y="SPI", color="SPI",
                         color_continuous_scale="RdBu", color_continuous_midpoint=0,
                         title=T("SPI with calibration (green) and validation (red)",
                                 "SPI con calibración (verde) y validación (rojo)"))
        fig_tl.add_hline(y=0, line_dash="dash")
        fig_tl.add_vrect(x0=cal_s.year, x1=cal_e.year,
                          fillcolor="green", opacity=0.12, layer="below", line_width=0)
        fig_tl.add_vrect(x0=val_s.year, x1=val_e.year,
                          fillcolor="red", opacity=0.12, layer="below", line_width=0)
        st.plotly_chart(fig_tl, use_container_width=True)

        st.subheader(T("🧠 Statistical interpretation","🧠 Interpretación estadística"))

        if not comp_p.empty and not comp_t.empty:
            cal_mp = comp_p[comp_p["period"] == cal_label]["PRCP"].mean()
            val_mp = comp_p[comp_p["period"] == val_label]["PRCP"].mean()
            cal_mt = comp_t[comp_t["period"] == cal_label]["TMEAN"].mean()
            val_mt = comp_t[comp_t["period"] == val_label]["TMEAN"].mean()

            col1, col2 = st.columns(2)
            col1.metric(T("Δ PRCP (val - cal)","Δ PRCP (val - cal)"),
                        f"{val_mp - cal_mp:+.0f} mm/yr",
                        delta=f"{(val_mp-cal_mp)/cal_mp*100:+.1f}%" if cal_mp else "—")
            col2.metric(T("Δ Temperature (val - cal)","Δ Temperatura (val - cal)"),
                        f"{val_mt - cal_mt:+.2f} °C")

            rel_p = (val_mp - cal_mp) / cal_mp * 100 if cal_mp else 0
            if rel_p < -15:
                st.warning(T(
                    "⚠️ Validation is **substantially drier**. Lower NSE expected — "
                    "this is a stress test, not a failure.",
                    "⚠️ La validación es **sustancialmente más seca**. NSE más bajo esperado — "
                    "prueba de estrés, no fallo."
                ))
            elif rel_p > 15:
                st.info(T("ℹ️ Validation is wetter than calibration.",
                          "ℹ️ La validación es más húmeda que la calibración."))
            else:
                st.success(T("✅ Precipitation regimes are comparable.",
                             "✅ Los regímenes de precipitación son comparables."))

            dt = val_mt - cal_mt
            if dt > 0.5:
                st.warning(T(
                    f"🌡️ Validation **{dt:.1f}°C warmer** — non-stationary climate. Document this.",
                    f"🌡️ Validación **{dt:.1f}°C más cálida** — clima no estacionario. Documéntalo."
                ))
            elif dt < -0.5:
                st.info(T(f"🌡️ Validation {abs(dt):.1f}°C cooler.",
                          f"🌡️ Validación {abs(dt):.1f}°C más fría."))
            else:
                st.success(T(f"✅ Temperatures similar (Δ = {dt:+.2f}°C).",
                             f"✅ Temperaturas similares (Δ = {dt:+.2f}°C)."))

    # ══════════════════════════════════════════════════════════════════════════
    # EXPORT SWAT+
    # ══════════════════════════════════════════════════════════════════════════
    elif step == T("📦 Export SWAT+", "📦 Exportar SWAT+"):

        st.header(T("Export SWAT+ Climate Files","Exportar Archivos Climáticos SWAT+"))

        if not HAS_EXPORTER:
            st.error(T("Exporter module not found.","Módulo no encontrado."))
            st.stop()

        if "filtered_stations" not in st.session_state:
            st.session_state["filtered_stations"] = apply_filters(
                catalog, st.session_state["filters"]
            )
        filtered = st.session_state["filtered_stations"]
        exportable = filtered[filtered["id"].isin(downloaded_ids)] if not filtered.empty \
                     else catalog[catalog["id"].isin(downloaded_ids)]

        st.info(T(
            f"Ready to export **{len(exportable)} stations** matching filters AND with local data.",
            f"Listo para exportar **{len(exportable)} estaciones** con filtros Y datos locales."
        ))

        if exportable.empty:
            st.warning(T("Nothing to export.","Nada para exportar."))
            st.stop()

        col1, col2 = st.columns(2)
        with col1:
            exp_start = st.date_input(T("Export from","Exportar desde"),
                                       value=datetime.date(2000, 1, 1))
        with col2:
            exp_end = st.date_input(T("Export to","Exportar hasta"),
                                     value=datetime.date(2024, 12, 31))

        output_folder = st.text_input(T("Output folder","Carpeta de salida"),
                                       value="swatplus_climate")

        if st.button(T("🚀 Generate SWAT+ files","🚀 Generar archivos SWAT+"),
                     type="primary"):
            exp_gdf = gpd.GeoDataFrame(
                exportable,
                geometry=gpd.points_from_xy(exportable.longitude, exportable.latitude),
                crs=4326
            )
            with st.spinner(T("Generating…","Generando…")):
                try:
                    result = export_swatplus(
                        stations_gdf=exp_gdf,
                        noaa_folder=NOAA_RAW_DIR,
                        output_folder=output_folder,
                        start_date=exp_start,
                        end_date=exp_end,
                    )
                except Exception as e:
                    st.error(f"Export failed: {e}")
                    st.stop()

            st.success(T(
                f"✅ {result['n_pcp']} .pcp + {result['n_tmp']} .tmp generated",
                f"✅ {result['n_pcp']} .pcp + {result['n_tmp']} .tmp generados"
            ))
            with open(result["zip_path"], "rb") as zf:
                st.download_button(
                    T("⬇️ Download SWAT+ climate package","⬇️ Descargar paquete SWAT+"),
                    data=zf.read(),
                    file_name=os.path.basename(result["zip_path"]),
                    mime="application/zip",
                )
