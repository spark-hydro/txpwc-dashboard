import streamlit as st

from components.sidebar import render_sidebar
from config.settings import APP_ICON, APP_TITLE
from core.io.filesystem import safe_markdown_read
from config.settings import CONTENT_DIR
from core.utils.kiosk import render_kiosk, should_show_kiosk
from core.utils.visual_kit import Card, HeroStat, render_cards, render_hero_stats, render_photo_banner
from pathlib import Path
import re

# -----------------------------
# Page config (global layout)
# -----------------------------
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)

# The kiosk splash is the app's front door: "/" shows it, and the QR codes /
# links on it lead to "/?app=1", which opens the dashboard for the rest of the
# session. "/?kiosk=1" forces the splash back up for the next visitor.
if should_show_kiosk():
    render_kiosk()
    st.stop()

# If the floating box overlaps content, add this
# st.markdown("""
# <style>
# .block-container {
#     padding-right: 300px;
# }
# </style>
# """, unsafe_allow_html=True)


# Sidebar (existing app context: basin/model/scenario)
context = render_sidebar()

#
# -----------------------------
# Utilities
# -----------------------------
def read_markdown_file(markdown_file):
    """Read markdown file as raw text."""
    return Path(markdown_file).read_text(encoding="utf-8")


def slugify(text: str) -> str:
    """Convert section titles → URL-friendly anchors (e.g., 'Project Overview' → 'project-overview')."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text


def build_outline_and_html(md_text: str):
    """
    Parse markdown:
    - Extract headings (#, ##, ###) → build TOC
    - Replace headings with HTML <h*> tags with id anchors
    """
    lines = md_text.splitlines()
    toc = []
    html_lines = []

    for line in lines:
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            level = len(m.group(1))      # heading level (1–3)
            title = m.group(2).strip()
            anchor = slugify(title)

            toc.append((level, title, anchor))

            # Replace markdown heading with HTML heading + anchor id
            tag = f"h{min(level,3)}"
            html_lines.append(f'<{tag} id="{anchor}">{title}</{tag}>')
        else:
            html_lines.append(line)

    return toc, "\n".join(html_lines)

#
# -----------------------------
# Load and process markdown
# -----------------------------
# st.title("Home")

md_text = read_markdown_file(CONTENT_DIR / "home.md")
toc, rendered_md = build_outline_and_html(md_text)


# -----------------------------
# Floating collapsible outline
# -----------------------------
# Uses HTML/CSS (st.html) so it can stay fixed while scrolling
st.html(f"""
<style>
.toc-float {{
    position: fixed;              /* keeps it visible while scrolling */
    top: 110px;
    right: 24px;
    z-index: 999;
    font-size: 0.92rem;
}}

.toc-details {{
    background: white;
    border: 1px solid rgba(49, 51, 63, 0.2);
    border-radius: 999px;         /* pill shape when collapsed */
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    overflow: hidden;
    transition: all 0.2s ease;
}}

.toc-details[open] {{
    width: 260px;                 /* expanded width */
    max-height: 70vh;
    overflow-y: auto;
    border-radius: 12px;
}}

.toc-summary {{
    list-style: none;
    cursor: pointer;
    padding: 10px 14px;
    font-weight: 600;
    user-select: none;
    white-space: nowrap;
}}

.toc-summary::-webkit-details-marker {{
    display: none;                /* remove default arrow */
}}

.toc-details:not([open]) .toc-summary::after {{
    content: "▸";                 /* collapsed arrow */
    margin-left: 8px;
}}

.toc-details[open] .toc-summary {{
    border-bottom: 1px solid rgba(49, 51, 63, 0.12);
}}

.toc-details[open] .toc-summary::after {{
    content: "▾";                 /* expanded arrow */
    float: right;
}}

.toc-content {{
    padding: 10px 14px 12px 14px;
}}

.toc-link {{
    display: block;
    text-decoration: none;
    color: inherit;
    margin-bottom: 6px;
}}

.toc-link:hover {{
    text-decoration: underline;
}}

/* Hide on small screens */
@media (max-width: 1200px) {{
    .toc-float {{
        display: none;
    }}
}}
</style>

<div class="toc-float">
  <details class="toc-details">
    <summary class="toc-summary">Outline</summary>
    <div class="toc-content">
      {''.join(
          f'<a class="toc-link" href="#{anchor}" style="margin-left:{12*(level-1)}px;">{title}</a>'
          for level, title, anchor in toc
      )}
    </div>
  </details>
</div>
""")


# -----------------------------
# Hook: a real photo, then proof numbers from the pilot report
# -----------------------------
render_photo_banner(
    "pecos_river_highbridge.jpg",
    "The Pecos River, looking downstream toward the Rio Grande confluence near Comstock, TX. "
    "<b>Photo: Natalie Houston, USGS (public domain).</b>",
)

render_hero_stats([
    HeroStat("99.7%", "Of salt removed in pilot testing — 131,000 → 352 mg/L"),
    HeroStat("8×", "Saltier than seawater at the Malaga Bend brine springs"),
    HeroStat("121,404 km²", "Of the Pecos Basin represented in the model"),
    HeroStat("1,110", "Climate stations feeding the simulations"),
])

# -----------------------------
# Render main content
# -----------------------------
# Use unsafe_allow_html because headings contain custom <h*> with id anchors
st.markdown(rendered_md, unsafe_allow_html=True)

# -----------------------------
# Why this matters, per audience
# -----------------------------
st.subheader("What this means for you")
render_cards([
    Card(
        "🚜", "If you farm or ranch here",
        "Treated produced water is a potential new irrigation supply in a basin where "
        "flow has fallen more than 75%. The model tests whether it can be delivered at "
        "a salinity your crops and soils can actually tolerate.",
    ),
    Card(
        "🛢️", "If you operate in the Permian",
        "Every barrel reused is a barrel not disposed of. This work builds the technical "
        "evidence for where reuse is defensible — and where it is not.",
    ),
    Card(
        "🏛️", "If you write or enforce the rules",
        "SB601 asked whether beneficial reuse is feasible. This is the modeling that "
        "turns that question into numbers: what reaches the river, what reaches the "
        "aquifer, and under which release strategies.",
    ),
    Card(
        "🐟", "If you care about the river",
        "The Pecos is already among the saltiest rivers in the country and supports an "
        "endangered fish. Any reuse plan has to be shown not to make that worse — which "
        "is exactly what these simulations are for.",
    ),
])