import re
from pathlib import Path

import streamlit as st

from components.sidebar import render_sidebar
from config.settings import APP_ICON, APP_TITLE
from core.utils.content import load_model_info, get_model_info_path
from core.utils.page_content import build_outline_and_html, render_floating_outline
from core.utils.content import load_data_driven, get_data_driven_path
from core.utils.visual_kit import Card, render_cards

# Page config
st.set_page_config(
    page_title=f"{APP_TITLE} | Data-Driven",
    page_icon=APP_ICON,
    layout="wide",
)

# Sidebar selections
context = render_sidebar()

# Load markdown text and actual file path
md_file_path = get_data_driven_path(context.basin_id, context.model_type)
md_text = load_data_driven(context.basin_id, context.model_type)

# Build outline + rendered markdown/html
toc, rendered_md = build_outline_and_html(md_text, md_file_path)

# Show floating outline
st.html(render_floating_outline(toc))

# Render content
st.markdown(rendered_md, unsafe_allow_html=True)

# The planned ML layer, as cards rather than a wall of table rows.
if context.basin_id == "Pecos":
    render_cards([
        Card(
            "⚡", "Surrogate model",
            "Learn from SWAT+gwflow runs to emulate its output, so a new scenario can "
            "be screened in moments instead of waiting on a full physical simulation.",
            status="planned",
        ),
        Card(
            "🎯", "Residual learning",
            "Train on where the physical model misses the observations, then correct "
            "for that bias — station by station, regime by regime.",
            status="planned",
        ),
        Card(
            "🗺️", "Spatiotemporal prediction",
            "Capture how flow and salinity evolve across the basin and through time, "
            "not just at a single gauge.",
            status="planned",
        ),
        Card(
            "🔍", "Feature importance",
            "Rank which drivers — rainfall, release timing, land use, upstream flow — "
            "actually move the outcome, and by how much.",
            status="planned",
        ),
        Card(
            "🚦", "Risk classification",
            "Flag which scenarios are likely to push a constituent past a regulatory "
            "or ecological threshold, before anyone runs them in full.",
            status="planned",
        ),
    ])