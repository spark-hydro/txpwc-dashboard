
import streamlit as st
from noaa_selector.page import run_app

st.set_page_config(
    page_title="Climate Analysis",
    layout="wide"
)

st.title("Climate Analysis")
st.caption("Interactive discovery and screening of climate monitoring stations")

run_app()
