"""Embed external pages or generated HTML in an iframe.

Newer Streamlit replaces `components.iframe` / `components.html` with `st.iframe`; use it when it
exists and fall back to the older API so the app runs on both.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def show_iframe(url: str, height: int) -> None:
    if hasattr(st, "iframe"):
        st.iframe(url, height=height)
    else:
        components.iframe(url, height=height, scrolling=True)


def show_html(html: str, height: int) -> None:
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:
        components.html(html, height=height)
