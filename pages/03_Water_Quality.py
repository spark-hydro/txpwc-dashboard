import re
from pathlib import Path

import streamlit as st

from components.sidebar import render_sidebar
from config.settings import APP_ICON, APP_TITLE
from core.utils.content import load_water_quality, get_water_quality_path
from core.utils.page_content import build_outline_and_html, render_floating_outline


# Page config
st.set_page_config(
    page_title=f"{APP_TITLE} | Water Quality",
    page_icon=APP_ICON,
    layout="wide",
)

# Sidebar selections
context = render_sidebar()

# Load markdown text and actual file path
md_file_path = get_water_quality_path(context.basin_id, context.model_type)
md_text = load_water_quality(context.basin_id, context.model_type)

# Build outline + rendered markdown/html
toc, rendered_md = build_outline_and_html(md_text, md_file_path)

# Show floating outline
st.html(render_floating_outline(toc))

# Render content
st.markdown(rendered_md, unsafe_allow_html=True)