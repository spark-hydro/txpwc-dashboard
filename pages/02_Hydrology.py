import re
from pathlib import Path

import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from config.settings import APP_ICON, APP_TITLE, RESOURCES_DIR
from core.utils.content import load_hydrology, get_hydrology_path
from core.utils.page_content import build_outline_and_html, render_floating_outline
from core.services.performance_service import load_performance_bundle
from core.plotting.duration_curves import plot_fdc
from core.plotting.hydrographs import plot_streamflow_hydrograph
from core.plotting.groundwater import plot_groundwater_scatter
from core.plotting.regional_context import plot_annual_flow_trend
from core.utils.visual_kit import Card, HeroStat, render_cards, render_hero_stats, render_photo_banner


# Page config
st.set_page_config(
    page_title=f"{APP_TITLE} | Hydrology",
    page_icon=APP_ICON,
    layout="wide",
)

# Sidebar selections
context = render_sidebar()

# Load markdown text and actual file path
md_file_path = get_hydrology_path(context.basin_id, context.model_type)
md_text = load_hydrology(context.basin_id, context.model_type)

# Build outline + rendered markdown/html
toc, rendered_md = build_outline_and_html(md_text, md_file_path)

# Show floating outline
st.html(render_floating_outline(toc))

# Hero stat strip (Pecos only): immediate visual hook before any prose.
# Each number links down to the card that explains it.
if context.basin_id == "Pecos":
    render_photo_banner(
        "pecos_salt_flat.jpg",
        "Dried salt flats along the lower Pecos, near Red Bluff Reservoir. "
        "<b>Photo: Johnathan Bumgarner, USGS (public domain).</b>",
    )
    render_hero_stats([
        HeroStat("−75%", "Flow lost to diversions, pumping &amp; evaporation", "card-dry"),
        HeroStat("8×", "Saltier than seawater at the Malaga Bend springs", "card-brine"),
        HeroStat("97.8 ft", "1954 flood crest — ~60 ft above the old record", "card-flood"),
        HeroStat("700 yrs", "Of tree rings confirm today's decline is extreme", "card-dry"),
    ])

# Render content
st.markdown(rendered_md, unsafe_allow_html=True)

# ── Regional Context (Pecos only): visual cards + real historical USGS data ───
if context.basin_id == "Pecos":
    render_cards([
        Card(
            "🪨", "It's the rock",
            "Permian-age salt and gypsum formations riddle the basin with karst — "
            "the root source of the brine below.",
            card_id="card-rock",
            sources=[
                ("geology overview", "https://www.researchgate.net/publication/355493237_Overview_of_Evaporite_Karst_in_the_Greater_Permian_Evaporite_Basin_GPEB_of_Texas_New_Mexico_Oklahoma_Kansas_and_Colorado_USA"),
                ("Red Bluff karst study", "https://www.researchgate.net/publication/355493234_Evaporite_Karst_in_the_Permian_Rustler_Salado_and_Castile_Formations_at_Red_Bluff_Dam_on_the_Pecos_River_Loving_and_Reeves_Counties_Texas"),
            ],
        ),
        Card(
            "🧂", "270,000 ppm brine",
            "Malaga Bend springs run about 8× saltier than seawater, adding an "
            "estimated 450,000 tons of salt to the river every year.",
            card_id="card-brine",
            sources=[
                ("USGS", "https://pubs.usgs.gov/publication/wri804"),
                ("Pecos River Resolution Corp.", "http://www.pecosriverresolution.com/salt-alleviation-at-malaga-bend-having-impact/"),
            ],
        ),
        Card(
            "📉", "A river running dry",
            "Diversions, groundwater pumping, and reservoir evaporation have cut flow "
            "more than three-quarters below historical levels — and 700 years of tree "
            "rings confirm today's lows are extreme even against centuries of drought.",
            card_id="card-dry",
            sources=[
                ("USFWS", "https://www.fws.gov/project/identifying-areas-high-salinity-pecos-river-basin"),
                ("USGS", "https://www.usgs.gov/publications/pecos-river-basin-salinity-assessment-santa-rosa-lake-new-mexico-confluence-pecos"),
                ("Harley &amp; Maxwell 2018", "https://journals.sagepub.com/doi/10.1177/0959683617744263"),
            ],
        ),
        Card(
            "🌿", "Thirsty invaders",
            "Saltcedar thickets once drank up to 1.2 m of water a year each. A 1999–2003 "
            "removal program salvaged up to 82% of it back for the river.",
            card_id="card-saltcedar",
            sources=[
                ("water-salvage study", "https://bioone.org/journals/invasive-plant-science-and-management/volume-2/issue-4/IPSM-09-009.1/Water-Loss-and-Salvage-in-Saltcedar-Tamarix-spp-Stands-on/10.1614/IPSM-09-009.1.full"),
                ("USBR history", "https://www.usbr.gov/history/ProjectHistories/Pecos%20River%20Basin%20Water%20Salvage%20Project%20D2.pdf"),
            ],
        ),
        Card(
            "🌊", "Still capable of fury",
            "Hurricane Alice's 1954 remnants dropped 28 in of rain, sending a wall of "
            "water downriver that destroyed a US 90 bridge. It still floods hard today.",
            card_id="card-flood",
            sources=[
                ("Texas Co-op Power", "https://texascooppower.com/pecos-river-flood-of-1954/"),
                ("2021 flood report", "https://floodlist.com/america/usa/floods-new-mexico-june-2021"),
            ],
        ),
        Card(
            "⚖️", "43/57, by law",
            "A 1948 interstate compact — enforced by the U.S. Supreme Court in 1987 — "
            "legally divides every drop of the river between Texas and New Mexico.",
            card_id="card-compact",
            sources=[
                ("Texas State Historical Assoc.", "https://www.tshaonline.org/handbook/entries/pecos-river"),
                ("Cornell Law", "https://www.law.cornell.edu/supremecourt/text/462/554"),
            ],
        ),
        Card(
            "🐟", "One fragile fish",
            "The endangered Pecos bluntnose shiner needs natural flow swings to spawn — "
            "and survives in just 282 km of river left.",
            card_id="card-fish",
            sources=[("USGS / Science.gov", "https://www.science.gov/topicpages/p/pecos+bluntnose+shiner")],
        ),
    ])

    flow_history_path = (
        RESOURCES_DIR / "content" / "reference_data" / "usgs_08446500_pecos_girvin_annual_flow.csv"
    )
    if flow_history_path.exists():
        flow_history = pd.read_csv(flow_history_path)
        st.plotly_chart(plot_annual_flow_trend(flow_history), use_container_width=True)
        st.caption(
            "Source: USGS National Water Information System, site 08446500 "
            "(Pecos River near Girvin, TX), daily mean discharge, accessed August 2026. "
            "Historical observation, not a model output."
        )

# ── Basin Indicators (Pecos only): real charts from the calibrated model ──────
if context.basin_id == "Pecos":
    st.divider()
    st.subheader("Basin Indicators")
    st.caption(
        "Demo-scale dataset (monthly, 2020) used to validate the observed-vs-simulated "
        "pipeline — will be replaced with the full calibrated historical record once "
        "available."
    )

    bundle = load_performance_bundle(context)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(plot_streamflow_hydrograph(bundle.streamflow_joined), use_container_width=True)
    with col2:
        st.plotly_chart(plot_fdc(bundle.streamflow_joined), use_container_width=True)

    if not bundle.groundwater.empty:
        st.plotly_chart(plot_groundwater_scatter(bundle.groundwater), use_container_width=True)