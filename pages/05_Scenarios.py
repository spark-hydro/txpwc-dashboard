import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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

# ── Interactive reservoir-release lab (Pecos only) ─────────────────────────────
RESERVOIR_LABS = {
    "Pecos": "https://josephauresy.github.io/pecos-reservoirs/",
}

reservoir_lab_url = RESERVOIR_LABS.get(context.basin_id)
if reservoir_lab_url:
    st.divider()
    st.subheader("Interactive lab — Reservoir release &amp; reuse siting")
    st.link_button("↗ Open the lab in full screen", reservoir_lab_url, use_container_width=True)
    components.iframe(reservoir_lab_url, height=1000, scrolling=True)
    st.caption(
        "Source: real 2000–2020 release records for the Pecos's 5 major dams, via the "
        "Pecos_USA SWAT+gwflow reservoir model. Research prototype, not an operational "
        "product — the salinity indicator is a simplified stand-in until the salinity-"
        "transport model is finished."
    )