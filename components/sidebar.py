from __future__ import annotations

import streamlit as st

from config.settings import (
    DEFAULT_BASIN_ID,
    DEFAULT_MODEL_TYPE,
    DEFAULT_SCENARIO_ID,
)
from core.models.schema import AppContext
from core.services.catalog import load_catalog
import base64


def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _init_state() -> None:
    st.session_state.setdefault("basin_id", DEFAULT_BASIN_ID)
    st.session_state.setdefault("model_type", DEFAULT_MODEL_TYPE)
    st.session_state.setdefault("scenario_id", DEFAULT_SCENARIO_ID)


def render_sidebar() -> AppContext:
    st.markdown("""
        <style>
            div[data-testid="stSidebarHeader"] {
                padding-top: 50px;
                padding-bottom: 30px;
            }
            div[data-testid="stSidebarHeader"] > div {
                height: 80px !important;
            }
            div[data-testid="stSidebarHeader"] img {
                height: 80px !important;
                width: auto !important;
                max-height: none !important;
            }
        </style>
    """, unsafe_allow_html=True)
    st.logo("assets/logos/txpwc.png", link="https://www.depts.ttu.edu/research/tx-water-consortium/")


    _init_state()
    catalog = load_catalog()


    with st.sidebar:
        st.header("Analysis Settings")

        basin_options = list(catalog["basins"].keys())
        selected_basin = st.selectbox(
            "Basin",
            options=basin_options,
            index=basin_options.index(st.session_state["basin_id"]) if st.session_state["basin_id"] in basin_options else 0,
        )
        st.session_state["basin_id"] = selected_basin

        basin_info = catalog["basins"][selected_basin]
        model_options = basin_info.get("model_types", [DEFAULT_MODEL_TYPE])
        scenario_options = basin_info.get("scenarios", [DEFAULT_SCENARIO_ID])

        current_model = st.session_state["model_type"] if st.session_state["model_type"] in model_options else model_options[0]
        current_scenario = st.session_state["scenario_id"] if st.session_state["scenario_id"] in scenario_options else scenario_options[0]

        selected_model = st.selectbox(
            "Model type",
            options=model_options,
            index=model_options.index(current_model),
        )
        selected_scenario = st.selectbox(
            "Scenario",
            options=scenario_options,
            index=scenario_options.index(current_scenario),
        )

        st.session_state["model_type"] = selected_model
        st.session_state["scenario_id"] = selected_scenario
        st.sidebar.markdown("---")

        # Push logos to bottom
        st.sidebar.markdown(
            f"""
            <style>
                .sidebar-logos {{
                    position: fixed;
                    bottom: 20px;
                    width: 100%;
                    display: flex;
                    gap: 1px;
                }}
            </style>
            <div class="sidebar-logos">
                <a href="https://www.depts.ttu.edu/waterresources/" target="_blank">
                    <img src="data:image/png;base64,{get_base64_image('assets/logos/water_center.png')}" 
                        style="width:160px;">
                </a>
                <a href="https://spark-hydro.github.io/" target="_blank">
                    <img src="data:image/png;base64,{get_base64_image('assets/logos/ihydro_lab.png')}" 
                        style="width:80px;">
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return AppContext(
        basin_id=st.session_state["basin_id"],
        model_type=st.session_state["model_type"],
        scenario_id=st.session_state["scenario_id"],
    )


def get_selected_context() -> AppContext:
    _init_state()
    return AppContext(
        basin_id=st.session_state["basin_id"],
        model_type=st.session_state["model_type"],
        scenario_id=st.session_state["scenario_id"],
    )
