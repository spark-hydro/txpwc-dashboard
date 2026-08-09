import re
from pathlib import Path

import streamlit as st

from components.sidebar import render_sidebar
from config.settings import APP_ICON, APP_TITLE
from core.utils.content import load_hydrology, get_hydrology_path
from core.utils.page_content import build_outline_and_html, render_floating_outline
from core.services.performance_service import load_performance_bundle
from core.plotting.duration_curves import plot_fdc
from core.plotting.hydrographs import plot_streamflow_hydrograph
from core.plotting.groundwater import plot_groundwater_scatter


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

# Render content
st.markdown(rendered_md, unsafe_allow_html=True)

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