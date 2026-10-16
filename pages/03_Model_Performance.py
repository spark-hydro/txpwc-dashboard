from types import SimpleNamespace

import streamlit as st

from components.performance_views import render_et_view, render_hydrology_view, render_observation_view
from components.sidebar import render_sidebar
from config.settings import RESOURCES_DIR
from core.io.txpwc_reader import get_basin_dir
from core.services.performance_service import load_performance_bundle

st.set_page_config(layout="wide")

context = render_sidebar()

st.title("Model Performance")
st.caption("How the simulations compare with real observations, and what the model says about the basin's water.")

OBSERVATIONS = "Observations"
ET = "Evapotranspiration"
HYDROLOGY = "Hydrologic responses"

# The three views are the page's main navigation, so they get a heavier look than the
# secondary controls (map tool, layer pickers) further down: equal widths, a taller
# bold button, and a filled colour for the active one.
st.markdown(
    """
    <style>
    .st-key-perf_view [data-testid="stButtonGroup"] { width: 100%; }
    .st-key-perf_view button { flex: 1 1 0; min-width: 12.5rem; min-height: 3.2rem; border-width: 1.5px; }
    .st-key-perf_view button p { font-size: 1.05rem; font-weight: 700; white-space: normal; text-overflow: clip; overflow: visible; }
    .st-key-perf_view button[aria-checked="true"],
    .st-key-perf_view button[data-selected="true"],
    .st-key-perf_view button[data-testid="stBaseButton-segmented_controlActive"] {
        background: #1f77b4 !important; border-color: #1f77b4 !important;
    }
    .st-key-perf_view button[aria-checked="true"] *,
    .st-key-perf_view button[data-selected="true"] *,
    .st-key-perf_view button[data-testid="stBaseButton-segmented_controlActive"] * { color: #ffffff; }
    </style>
    """,
    unsafe_allow_html=True,
)

view = st.segmented_control(
    "View", options=[OBSERVATIONS, ET, HYDROLOGY], default=OBSERVATIONS,
    key="perf_view", label_visibility="collapsed",
) or OBSERVATIONS

# Only the hydrologic-responses view needs the full data bundle (gauge series, channel output);
# loading and copying it on every rerun slowed the other two views for nothing.
light = SimpleNamespace(basin_dir=get_basin_dir(RESOURCES_DIR, context.basin_id))

if view == OBSERVATIONS:
    render_observation_view(light, context)
elif view == ET:
    render_et_view(light, context)
else:
    render_hydrology_view(load_performance_bundle(context), context)
