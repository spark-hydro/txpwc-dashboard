
import streamlit as st
from noaa_selector.page import run_app

st.set_page_config(
    page_title="NOAA Station Selector",
    layout="wide"
)

st.title("NOAA Station Selector")
st.caption("Interactive discovery and screening of NOAA monitoring stations")

run_app()
