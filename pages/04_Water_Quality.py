import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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

# ── Treatment train diagram (Pecos only) ──────────────────────────────────────
_TREATMENT_HTML = """
<div style="font-family:sans-serif;margin:1.5rem 0 2rem 0;">
  <p style="font-size:13px;font-weight:600;color:#666;margin-bottom:12px;letter-spacing:.05em;text-transform:uppercase;">
    Pilot Treatment Train — TxPWC Report (April 2026)
  </p>
  <div style="display:flex;align-items:stretch;gap:0;flex-wrap:wrap;justify-content:center;">

    <div style="background:#fee2e2;border:2px solid #dc2626;border-radius:10px;padding:14px 20px;min-width:130px;text-align:center;">
      <div style="font-weight:700;color:#dc2626;font-size:14px;">Raw PW</div>
      <div style="font-size:12px;color:#333;margin-top:8px;line-height:1.7;">
        TDS&nbsp;<b>131,000 mg/L</b><br>
        NH₃&nbsp;<b>620 mg/L</b><br>
        PFAS&nbsp;<b>ND</b>
      </div>
    </div>

    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 10px;min-width:70px;">
      <span style="font-size:22px;color:#aaa;">&#x2192;</span>
      <span style="font-size:10px;color:#888;text-align:center;">Desalination<br>&gt;99.7% TDS</span>
    </div>

    <div style="background:#fef9c3;border:2px solid #ca8a04;border-radius:10px;padding:14px 20px;min-width:130px;text-align:center;">
      <div style="font-weight:700;color:#92400e;font-size:14px;">Desalinated PW</div>
      <div style="font-size:12px;color:#333;margin-top:8px;line-height:1.7;">
        TDS&nbsp;<b>317 mg/L</b><br>
        NH₃&nbsp;<b>21.9 mg/L</b><br>
        PFAS&nbsp;<b>ND</b>
      </div>
    </div>

    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 10px;min-width:70px;">
      <span style="font-size:22px;color:#aaa;">&#x2192;</span>
      <span style="font-size:10px;color:#888;text-align:center;">Polishing<br>96% NH₃</span>
    </div>

    <div style="background:#dcfce7;border:2px solid #16a34a;border-radius:10px;padding:14px 20px;min-width:130px;text-align:center;">
      <div style="font-weight:700;color:#15803d;font-size:14px;">Polished DPW</div>
      <div style="font-size:12px;color:#333;margin-top:8px;line-height:1.7;">
        TDS&nbsp;<b>352 mg/L</b><br>
        NH₃&nbsp;<b>6.46 mg/L</b><br>
        PFAS&nbsp;<b>ND</b>
      </div>
    </div>

    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 10px;min-width:70px;">
      <span style="font-size:22px;color:#aaa;">&#x2192;</span>
      <span style="font-size:10px;color:#888;text-align:center;">Beneficial<br>reuse</span>
    </div>

    <div style="background:#dbeafe;border:2px solid #2563eb;border-radius:10px;padding:14px 20px;min-width:130px;text-align:center;">
      <div style="font-weight:700;color:#1d4ed8;font-size:14px;">Pecos River</div>
      <div style="font-size:12px;color:#333;margin-top:8px;line-height:1.7;">
        Dilution&nbsp;+<br>aquifer transport<br>&#x2193; lab below
      </div>
    </div>

  </div>
  <p style="font-size:11px;color:#999;margin-top:10px;">
    PFAS: EPA Method 1633, 7 samples, LOQ 1–2 ng/L — not detected at any treatment stage.
    WET toxicity at 100% PDPW: 89% non-toxic.
  </p>
</div>
"""

if context.basin_id == "Pecos":
    st.html(_TREATMENT_HTML)

# ── Interactive contaminant-transport lab ─────────────────────────────────────
# The lab is a self-contained client-side app served by GitHub Pages, so it runs at
# full speed without loading the Streamlit server. An <iframe> cannot be injected
# through the markdown above (st.markdown strips it), so it is embedded here.
INTERACTIVE_LABS = {
    "Pecos": "https://josephauresy.github.io/pecos-pfas-lab/",
}

lab_url = INTERACTIVE_LABS.get(context.basin_id)
if lab_url:
    st.divider()
    st.subheader("Interactive lab — PFAS vs. salinity transport")
    st.link_button("↗ Open the lab in full screen", lab_url, use_container_width=True)
    components.iframe(lab_url, height=1000, scrolling=True)
    st.caption(
        "Source: Texas Produced Water Consortium, *Produced Water Treatment Pilot "
        "Testing: Water Quality Report*, April 2026. Conceptual 2-D teaching model "
        "(SWAT+/gwflow + USGT-PFAS physics), not a calibrated MODFLOW-USG run."
    )