import re
from pathlib import Path


def slugify(text: str) -> str:
    """Convert heading text to clean anchor ids."""
    text = text.strip().lower()

    # Remove leading numbering like 1.2.1 if present
    text = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", text)

    # Remove special characters except spaces/hyphens/underscores
    text = re.sub(r"[^\w\s-]", "", text)

    # Replace spaces with hyphens
    text = re.sub(r"\s+", "-", text)
    return text


def build_outline_and_html(md_text: str, md_file_path: Path):
    """
    Parse markdown text and:
    - collect headings for outline
    - add anchor ids to headings
    - convert image-only markdown lines into HTML <img> tags
    """
    lines = md_text.splitlines()
    toc = []
    html_lines = []

    for line in lines:
        # Match markdown headings: #, ##, ###
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            anchor = slugify(title)

            # Save for outline
            toc.append((level, title, anchor))

            # Replace markdown heading with HTML heading carrying id anchor
            tag = f"h{min(level, 3)}"
            html_lines.append(f'<{tag} id="{anchor}">{title}</{tag}>')

        # Handle image-only markdown lines
        elif re.match(r'^\s*!\[.*?\]\((.*?)\)\s*$', line):
            img_match = re.findall(r'!\[.*?\]\((.*?)\)', line)
            if img_match:
                img_path = img_match[0]

                # Resolve image relative to the markdown file location
                full_path = (md_file_path.parent / img_path).resolve()

                html_lines.append(
                    f'<img src="{full_path}" '
                    f'style="max-width:100%; border-radius:10px; margin:10px 0;">'
                )
            else:
                html_lines.append(line)

        else:
            # Keep normal markdown lines unchanged
            html_lines.append(line)

    return toc, "\n".join(html_lines)


def render_floating_outline(toc: list[tuple[int, str, str]]) -> str:
    """
    Return floating outline HTML/CSS.
    toc format: [(level, title, anchor), ...]
    """
    links_html = "".join(
        f'<a class="toc-link" href="#{anchor}" style="margin-left:{12*(level-1)}px;">{title}</a>'
        for level, title, anchor in toc
    )

    return f"""
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
      {links_html}
    </div>
  </details>
</div>
"""