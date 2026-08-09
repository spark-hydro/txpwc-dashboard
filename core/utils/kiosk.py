"""Full-screen kiosk landing page for poster-session displays.

Triggered by opening the app with ?kiosk=1 in the URL. Shows a large QR
code pointing at the deployed dashboard plus a lightweight animated
water/salinity-plume backdrop, with no Streamlit chrome or sidebar.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import streamlit as st

DASHBOARD_URL = "https://txpwc-dashboard.streamlit.app/"
REPO_URL = "https://github.com/spark-hydro/txpwc-dashboard"

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
QR_SVG_PATH = ASSETS_DIR / "qr_dashboard.svg"
LOGO_PATH = ASSETS_DIR / "logos" / "txpwc.png"
STATIONS_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "noaa_selector" / "data" / "stations_catalog.csv"
)

BASIN_AREA_KM2 = 121_404


@st.cache_data
def _load_kiosk_stats() -> dict:
    stats = {
        "area_km2": BASIN_AREA_KM2,
        "station_count": None,
        "record_years": None,
    }
    if STATIONS_CATALOG_PATH.exists():
        df = pd.read_csv(STATIONS_CATALOG_PATH)
        stats["station_count"] = len(df)
        mindate = pd.to_datetime(df["mindate"], errors="coerce").min()
        maxdate = pd.to_datetime(df["maxdate"], errors="coerce").max()
        if pd.notna(mindate) and pd.notna(maxdate):
            stats["record_years"] = int(round((maxdate - mindate).days / 365.25))
    return stats


@st.cache_data
def _load_base64_image(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def is_kiosk_mode() -> bool:
    return st.query_params.get("kiosk") is not None


def render_kiosk() -> None:
    """Render the full-screen kiosk landing page in place of the normal Home content."""
    stats = _load_kiosk_stats()
    qr_b64 = _load_base64_image(str(QR_SVG_PATH))
    qr_data_uri = f"data:image/svg+xml;base64,{qr_b64}" if qr_b64 else ""
    logo_b64 = _load_base64_image(str(LOGO_PATH))

    station_stat = f"{stats['station_count']:,}" if stats["station_count"] else "1,100+"
    record_stat = f"{stats['record_years']}+ yrs" if stats["record_years"] else "170+ yrs"
    area_stat = f"{stats['area_km2']:,} km²"

    st.html(f"""
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"],
header[data-testid="stHeader"], #MainMenu, footer {{
    display: none !important;
}}
.block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}
[data-testid="stAppViewContainer"], .stApp {{
    background: radial-gradient(ellipse at 50% -10%, #0f3d52 0%, #082433 45%, #04121c 100%) !important;
}}

@keyframes kiosk-wave-drift {{
    from {{ transform: translateX(0); }}
    to   {{ transform: translateX(-50%); }}
}}
@keyframes kiosk-particle-drift {{
    0%   {{ transform: translate(0, 0) scale(0.8); opacity: 0; }}
    12%  {{ opacity: 0.75; }}
    100% {{ transform: translate(var(--dx), var(--dy)) scale(1.15); opacity: 0; }}
}}
@keyframes kiosk-glow-pulse {{
    0%, 100% {{ opacity: 0.55; }}
    50%      {{ opacity: 0.9; }}
}}
@keyframes kiosk-fade-up {{
    from {{ opacity: 0; transform: translateY(14px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

.kiosk-root {{
    position: relative;
    width: 100%;
    min-height: 100vh;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, sans-serif;
    color: #eaf6fb;
}}

.kiosk-plume {{
    position: absolute;
    top: 12%;
    left: -10%;
    width: 70vw;
    height: 70vw;
    max-width: 900px;
    max-height: 900px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(56,189,178,0.35) 0%, rgba(45,155,176,0.16) 40%, rgba(10,40,55,0) 70%);
    filter: blur(6px);
    animation: kiosk-glow-pulse 7s ease-in-out infinite;
    pointer-events: none;
}}
.kiosk-plume.kiosk-plume-b {{
    top: auto;
    bottom: 8%;
    left: auto;
    right: -12%;
    width: 55vw;
    height: 55vw;
    max-width: 700px;
    max-height: 700px;
    background: radial-gradient(circle, rgba(34,211,238,0.28) 0%, rgba(20,120,150,0.14) 45%, rgba(10,40,55,0) 70%);
    animation-delay: 2.3s;
}}

.kiosk-particle {{
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(165,243,252,0.95) 0%, rgba(45,180,190,0.55) 60%, rgba(45,180,190,0) 100%);
    animation: kiosk-particle-drift linear infinite;
    pointer-events: none;
}}

.kiosk-waves {{
    position: absolute;
    left: 0;
    bottom: 0;
    width: 100%;
    height: 32vh;
    overflow: hidden;
    pointer-events: none;
    background: linear-gradient(180deg, rgba(8,36,51,0) 0%, rgba(14,116,144,0.30) 55%, rgba(4,18,28,0.82) 100%);
}}
.kiosk-wave-band {{
    position: absolute;
    top: -20%;
    left: -20%;
    width: 140%;
    height: 140%;
}}
.kiosk-wave-1 {{
    background-image: repeating-linear-gradient(100deg, rgba(34,211,238,0.20) 0px, rgba(34,211,238,0.20) 36px, rgba(34,211,238,0) 36px, rgba(34,211,238,0) 90px);
    animation: kiosk-wave-drift 24s linear infinite;
}}
.kiosk-wave-2 {{
    background-image: repeating-linear-gradient(96deg, rgba(14,116,144,0.28) 0px, rgba(14,116,144,0.28) 50px, rgba(14,116,144,0) 50px, rgba(14,116,144,0) 120px);
    animation: kiosk-wave-drift 17s linear infinite reverse;
}}
.kiosk-wave-3 {{
    background-image: repeating-linear-gradient(104deg, rgba(110,231,216,0.14) 0px, rgba(110,231,216,0.14) 22px, rgba(110,231,216,0) 22px, rgba(110,231,216,0) 70px);
    animation: kiosk-wave-drift 31s linear infinite;
}}

.kiosk-card {{
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 22px;
    padding: 48px 56px 40px;
    text-align: center;
    animation: kiosk-fade-up 0.9s ease-out;
}}

.kiosk-logo {{
    height: 64px;
    width: auto;
    margin-bottom: 4px;
}}

.kiosk-title {{
    font-size: clamp(1.8rem, 3.2vw, 2.75rem);
    font-weight: 800;
    letter-spacing: 0.01em;
    margin: 0;
    color: #ffffff;
}}
.kiosk-subtitle {{
    font-size: clamp(1rem, 1.5vw, 1.3rem);
    color: #a9d8e6;
    margin: -10px 0 6px;
    max-width: 640px;
}}

.kiosk-qr-wrap {{
    background: #ffffff;
    border-radius: 24px;
    padding: 22px;
    box-shadow: 0 18px 60px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.06);
}}
.kiosk-qr-wrap img {{
    display: block;
    width: clamp(220px, 22vw, 320px);
    height: clamp(220px, 22vw, 320px);
}}

.kiosk-scan-label {{
    font-size: clamp(1.05rem, 1.6vw, 1.4rem);
    font-weight: 700;
    color: #ffffff;
    margin-top: 4px;
}}
.kiosk-scan-sub {{
    font-size: 0.95rem;
    color: #8fc4d4;
    margin-top: -8px;
}}

.kiosk-stats {{
    display: flex;
    gap: clamp(18px, 4vw, 56px);
    margin-top: 14px;
    flex-wrap: wrap;
    justify-content: center;
}}
.kiosk-stat {{
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 100px;
}}
.kiosk-stat-value {{
    font-size: clamp(1.4rem, 2.4vw, 2rem);
    font-weight: 800;
    color: #6ee7d8;
}}
.kiosk-stat-label {{
    font-size: 0.8rem;
    color: #9fc9d6;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 2px;
}}

.kiosk-footer {{
    margin-top: 18px;
    font-size: 0.8rem;
    color: #6b98a8;
}}
.kiosk-footer a {{
    color: #8fd6e8;
    text-decoration: none;
}}

@media (max-width: 700px) {{
    .kiosk-card {{ padding: 32px 20px 28px; gap: 16px; }}
    .kiosk-stats {{ gap: 20px; }}
}}
</style>

<div class="kiosk-root">
  <div class="kiosk-plume"></div>
  <div class="kiosk-plume kiosk-plume-b"></div>

  {"".join(
      f'<div class="kiosk-particle" style="'
      f'left:{(i * 37 + 4) % 100}%; top:{(i * 53 + 8) % 90}%; '
      f'width:{6 + (i % 4) * 3}px; height:{6 + (i % 4) * 3}px; '
      f'--dx:{(-1 if i % 2 else 1) * (40 + (i * 11) % 90)}px; '
      f'--dy:{-(60 + (i * 17) % 120)}px; '
      f'animation-duration:{9 + (i % 6)}s; '
      f'animation-delay:{(i * 0.7) % 8}s;"></div>'
      for i in range(18)
  )}

  <div class="kiosk-waves">
    <div class="kiosk-wave-band kiosk-wave-1"></div>
    <div class="kiosk-wave-band kiosk-wave-2"></div>
    <div class="kiosk-wave-band kiosk-wave-3"></div>
  </div>

  <div class="kiosk-card">
    {f'<img class="kiosk-logo" src="data:image/png;base64,{logo_b64}" alt="TxPWC logo">' if logo_b64 else ''}
    <h1 class="kiosk-title">Texas Produced Water Consortium</h1>
    <p class="kiosk-subtitle">Interactive hydrologic modeling &amp; data dashboard — Pecos River Basin</p>

    <div class="kiosk-qr-wrap">
      {f'<img src="{qr_data_uri}" alt="QR code to the TxPWC dashboard">' if qr_data_uri else ''}
    </div>
    <div class="kiosk-scan-label">📱 Scan to explore on your phone</div>
    <div class="kiosk-scan-sub">Escanea para explorar en tu celular</div>

    <div class="kiosk-stats">
      <div class="kiosk-stat">
        <div class="kiosk-stat-value">{area_stat}</div>
        <div class="kiosk-stat-label">Watershed area</div>
      </div>
      <div class="kiosk-stat">
        <div class="kiosk-stat-value">{station_stat}</div>
        <div class="kiosk-stat-label">Climate stations</div>
      </div>
      <div class="kiosk-stat">
        <div class="kiosk-stat-value">{record_stat}</div>
        <div class="kiosk-stat-label">Of climate record</div>
      </div>
    </div>

    <div class="kiosk-footer">
      {DASHBOARD_URL.replace("https://", "")} &nbsp;·&nbsp; Texas Tech University
    </div>
  </div>
</div>
""")
