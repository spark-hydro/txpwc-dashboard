import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from components.sidebar import render_sidebar
from config.settings import APP_ICON, APP_TITLE
from core.utils.content import load_scenarios, get_scenarios_path
from core.utils.page_content import build_outline_and_html, render_floating_outline
from core.utils.visual_kit import Card, Phase, render_cards, render_roadmap





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

# The Pecos content has <!-- SPLIT:... --> markers so card grids can be
# injected between markdown fragments, in the middle of the document
# (st.markdown renders as one block otherwise). Other basins fall back to
# a single, unsplit render.
SPLIT_MARKERS = ["<!-- SPLIT:planned-cards -->", "<!-- SPLIT:lab-tabs-cards -->", "<!-- SPLIT:oneclick-cards -->"]
has_splits = all(marker in md_text for marker in SPLIT_MARKERS)

if has_splits:
    frag1, rest = md_text.split(SPLIT_MARKERS[0])
    frag2, rest = rest.split(SPLIT_MARKERS[1])
    frag3, frag4 = rest.split(SPLIT_MARKERS[2])

    toc1, html1 = build_outline_and_html(frag1, md_file_path)
    toc2, html2 = build_outline_and_html(frag2, md_file_path)
    toc3, html3 = build_outline_and_html(frag3, md_file_path)
    toc4, html4 = build_outline_and_html(frag4, md_file_path)
    toc = toc1 + toc2 + toc3 + toc4
else:
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

if not has_splits:
    # Render content (fallback for basins without card-split markers)
    st.markdown(rendered_md, unsafe_allow_html=True)
else:
    st.markdown(html1, unsafe_allow_html=True)

    render_cards([
        Card(
            "🛢️", "In-Stream Produced-Water Release",
            "Simulates a produced-water release at a chosen river point — tracks how "
            "streamflow changes downstream, and how salinity (or another constituent) "
            "disperses into groundwater over time and distance.",
            status="planned",
        ),
        Card(
            "🌾", "Land Application / Irrigation Reuse",
            "Reusing treated water for irrigation instead of in-stream release: different "
            "crops and water-use rates, distance from Red Bluff as a feasibility factor, "
            "and the groundwater impact of sustained irrigation.",
            status="planned",
        ),
        Card(
            "🗺️", "Higher-Resolution Groundwater",
            "A MODFLOW 6 unstructured grid will refine groundwater results, concentrating "
            "resolution near release or irrigation zones instead of uniformly across the basin.",
            status="planned",
        ),
    ])

    st.markdown(html2, unsafe_allow_html=True)

    render_cards([
        Card("🗺️", "Reservoir Map", "Real dam locations, sized and colored by mean annual release."),
        Card("📊", "Flow &amp; Management", "Set your own release policy for any dam, or load a one-click scenario, and watch the river respond."),
        Card("🛢️", "Where to Place Reuse Water", "Drag a candidate reuse site along the river; the reach lights up green / yellow / red."),
        Card("🐟", "Salinity &amp; Fish", "Cross-references release choices against documented natural salinity sources and the Pecos pupfish's verified range."),
    ])

    st.markdown(html3, unsafe_allow_html=True)

    render_cards([
        Card("🔄", "Reset to History", "No changes — shows exactly what the 5 dams actually did, 2000–2020."),
        Card("🏜️", "2011–13 Drought, Unchanged", "Jumps the timeline to the real NM/TX drought under historical policy — see how the system held up."),
        Card("💧", "Guarantee Minimum Flow", "Applies a minimum-instream-flow floor across all 5 dams at once."),
        Card("🎯", "Protect Avalon → Red Bluff", "A targeted policy for the stretch closest to the candidate reuse zone."),
        Card("📈", "Release 30% More", "Stress-tests the system against a basin-wide 30% release increase."),
    ])

    st.markdown(html4, unsafe_allow_html=True)

# ── Interactive reservoir-release lab (Pecos only) ─────────────────────────────
RESERVOIR_LABS = {
    "Pecos": "https://josephauresy.github.io/pecos-reservoirs/",
}

reservoir_lab_url = RESERVOIR_LABS.get(context.basin_id)
if reservoir_lab_url:
    st.divider()
    st.subheader("Interactive lab — Reservoir release & reuse siting")
    st.link_button("↗ Open the lab in full screen", reservoir_lab_url, use_container_width=True)
    components.iframe(reservoir_lab_url, height=1000, scrolling=True)
    st.caption(
        "Source: real 2000–2020 release records for the Pecos's 5 major dams, via the "
        "Pecos_USA SWAT+gwflow reservoir model. Research prototype, not an operational "
        "product — the salinity indicator is a simplified stand-in until the salinity-"
        "transport model is finished."
    )