import streamlit as st

from components.performance_views import render_et_view, render_hydrology_view, render_observation_view
from components.sidebar import render_sidebar
from core.services.performance_service import load_performance_bundle

st.set_page_config(layout="wide")

context = render_sidebar()
bundle = load_performance_bundle(context)

st.title("Model Performance")
st.caption("How the simulations compare with real observations, and what the model says about the basin's water.")

OBSERVATIONS = "Observations"
ET = "ET"
HYDROLOGY = "Hydrologic responses"

view = st.segmented_control(
    "View", options=[OBSERVATIONS, ET, HYDROLOGY], default=OBSERVATIONS,
    key="perf_view", label_visibility="collapsed",
) or OBSERVATIONS

if view == OBSERVATIONS:
    render_observation_view(bundle, context)
elif view == ET:
    render_et_view(bundle, context)
else:
    render_hydrology_view(bundle, context)
