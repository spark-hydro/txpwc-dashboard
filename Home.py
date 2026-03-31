import streamlit as st

from components.sidebar import render_sidebar
from config.settings import APP_ICON, APP_TITLE
from core.io.filesystem import safe_markdown_read
from config.settings import CONTENT_DIR
from pathlib import Path


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    # initial_sidebar_state="expanded",
)

context = render_sidebar()
#
# st.title("Home")
# st.markdown(safe_markdown_read(CONTENT_DIR / "home.md"))
def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()

st.markdown(read_markdown_file(CONTENT_DIR / "home.md"),  unsafe_allow_html=True)

st.subheader("Current selection")
st.write(
    {
        "basin_id": context.basin_id,
        "model_type": context.model_type,
        "scenario_id": context.scenario_id,
    }
)



# st.title(APP_TITLE)
# st.caption("Initial scaffold for hydrologic model performance, data exploration, and future scenario analysis.")

# left, right = st.columns([2, 1])

# with left:
#     st.markdown(
#         """
#         This starter app is designed to replace the legacy Hydralit-based dashboard with a
#         cleaner native Streamlit structure that is easier to maintain and extend to
#         **SWAT+ gwflow** and TxPWC-specific workflows.
#         """
#     )

#     st.info(
#         f"Current context: basin = **{context.basin_id}**, model = **{context.model_type}**, "
#         f"scenario = **{context.scenario_id}**"
#     )

#     st.markdown(
#         """
#         Use the pages in the left sidebar to move through:

#         - Home
#         - Model Performance
#         - Hydrology
#         - Water Quality
#         - Scenarios
#         - Model Info
#         """
#     )

# with right:
#     st.subheader("Starter status")
#     st.metric("Architecture", "Ready")
#     st.metric("Demo basin", context.basin_id)
#     st.metric("Model adapter", context.model_type)
