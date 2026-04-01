import re
from pathlib import Path

import streamlit as st

from components.sidebar import render_sidebar
from config.settings import APP_ICON, APP_TITLE
from core.utils.content import load_model_info, get_model_info_path

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title=f"{APP_TITLE} | Model Info",
    page_icon=APP_ICON,
    layout="wide",
)

# Sidebar: returns current basin / model / scenario
context = render_sidebar()


# -----------------------------
# Utilities
# -----------------------------
def slugify(text: str) -> str:
    """Convert section titles to URL-friendly anchors."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text


def build_outline_and_html(md_text: str, md_file_path: Path):
    """
    Parse markdown text and:
    1. Extract headings for outline
    2. Replace headings with HTML headings with anchor ids
    3. Convert image markdown to HTML using paths relative to the markdown file
    """
    lines = md_text.splitlines()
    toc = []
    html_lines = []

    for line in lines:
        # Handle headings
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            anchor = slugify(title)

            toc.append((level, title, anchor))

            tag = f"h{min(level, 3)}"
            html_lines.append(f'<{tag} id="{anchor}">{title}</{tag}>')

        # Handle pure image lines only
        elif re.match(r'^\s*!\[.*?\]\((.*?)\)\s*$', line):
            img_match = re.findall(r'!\[.*?\]\((.*?)\)', line)
            if img_match:
                img_path = img_match[0]

                # Resolve image path relative to the markdown file location
                full_path = (md_file_path.parent / img_path).resolve()

                html_lines.append(
                    f'<img src="{full_path}" '
                    f'style="max-width:100%; border-radius:10px; margin:10px 0;">'
                )
            else:
                html_lines.append(line)

        else:
            html_lines.append(line)

    return toc, "\n".join(html_lines)

# -----------------------------
# Load model info markdown
# -----------------------------
# Example:
# basin = Pecos, model = SWAT+ gwflow
# -> resources/content/model_info/pecos/swat+gwflow.md
# Load markdown text and its actual file path
md_file_path = get_model_info_path(context.basin_id, context.model_type)
md_text = load_model_info(context.basin_id, context.model_type)

# Build outline and render markdown/html
toc, rendered_md = build_outline_and_html(md_text, md_file_path)

# -----------------------------
# Floating collapsible outline
# -----------------------------
st.html(f"""
<style>
.toc-float {{
    position: fixed;
    top: 110px;
    right: 24px;
    z-index: 999;
    font-size: 0.92rem;
}}

.toc-details {{
    background: white;
    border: 1px solid rgba(49, 51, 63, 0.2);
    border-radius: 999px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    overflow: hidden;
    transition: all 0.2s ease;
}}

.toc-details[open] {{
    width: 260px;
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
    display: none;
}}

.toc-details:not([open]) .toc-summary::after {{
    content: "▸";
    margin-left: 8px;
}}

.toc-details[open] .toc-summary {{
    border-bottom: 1px solid rgba(49, 51, 63, 0.12);
}}

.toc-details[open] .toc-summary::after {{
    content: "▾";
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
# Render page content
# -----------------------------
st.markdown(rendered_md, unsafe_allow_html=True)


# -----------------------------
# Optional current selection
# -----------------------------
st.subheader("Current selection")
st.write(
    {
        "basin_id": context.basin_id,
        "model_type": context.model_type,
        "scenario_id": context.scenario_id,
    }
)