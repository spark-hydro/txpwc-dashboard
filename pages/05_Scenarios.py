import re
from pathlib import Path

import streamlit as st

from components.sidebar import render_sidebar
from config.settings import APP_ICON, APP_TITLE
from core.utils.content import load_scenarios, get_scenarios_path
from core.utils.page_content import build_outline_and_html, render_floating_outline
from core.utils.visual_kit import Phase, render_roadmap





# Page config
st.set_page_config(
    page_title=f"{APP_TITLE} | Scenarios",
    page_icon=APP_ICON,
    layout="wide",
)

# Sidebar selections
context = render_sidebar()

# Load markdown text and actual file path
md_file_path = get_scenarios_path(context.basin_id, context.model_type)
md_text = load_scenarios(context.basin_id, context.model_type)

# Build outline + rendered markdown/html
toc, rendered_md = build_outline_and_html(md_text, md_file_path)

# Show floating outline
st.html(render_floating_outline(toc))

# Where the project stands today, at a glance, before the detail below.
if context.basin_id == "Pecos":
    render_roadmap([
        Phase(
            "Phase 1", "Calibrate the model",
            "Thousands of PEST++ parameter runs tuned SWAT+gwflow against observed "
            "streamflow. The ensemble figures below are that process.",
            status="live",
        ),
        Phase(
            "Phase 2", "Reservoirs + salinity",
            "Add dam operations and a salinity-transport module, then recalibrate "
            "against both flow and salinity observations.",
            status="next",
        ),
        Phase(
            "Phase 3", "Release &amp; reuse scenarios",
            "Simulate where treated water enters the system — in-stream release or "
            "irrigation reuse — and track flow and salinity downstream.",
            status="planned",
        ),
        Phase(
            "Phase 4", "Sharper groundwater",
            "Refine groundwater results with a MODFLOW 6 unstructured grid, "
            "concentrating resolution where it matters most.",
            status="planned",
        ),
    ])

# Render content
st.markdown(rendered_md, unsafe_allow_html=True)