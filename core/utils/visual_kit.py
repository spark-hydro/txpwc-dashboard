"""Shared visual components: hero stats, icon cards, and roadmap phases.

Used across Hydrology / Scenarios / Water Quality / Data-Driven so the whole
dashboard reads as one designed system rather than page-by-page markdown.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import streamlit as st

IMAGES_DIR = Path(__file__).resolve().parents[2] / "resources" / "content" / "images"


@lru_cache(maxsize=32)
def _image_data_uri(filename: str) -> str:
    path = IMAGES_DIR / filename
    if not path.exists():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode()
    ext = path.suffix.lstrip(".").lower()
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64,{b64}"

# Status vocabulary shared by every page, so a visitor learns the colour code once.
STATUS_STYLES = {
    "live": ("#059669", "#d1fae5", "Live now"),
    "next": ("#b45309", "#fef3c7", "Next up"),
    "planned": ("#475569", "#e2e8f0", "Planned"),
}

VK_CSS = """
<style>
/* ---------- hero stat strip ---------- */
.vk-hero {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 14px;
    margin: 4px 0 26px;
}
.vk-hero-card {
    display: block;
    background: linear-gradient(160deg, #0e7490 0%, #164e63 100%);
    border-radius: 14px;
    padding: 18px 16px;
    color: #ffffff !important;
    text-align: center;
    text-decoration: none !important;
    box-shadow: 0 6px 18px rgba(14,116,144,0.22);
    transition: transform .15s ease, box-shadow .15s ease;
}
a.vk-hero-card:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 12px 26px rgba(14,116,144,0.38);
}
a.vk-hero-card:hover .vk-hero-cue { opacity: 1; }
div.vk-hero-card { cursor: default; }
.vk-hero-num { font-size: 1.85rem; font-weight: 800; line-height: 1.1; }
.vk-hero-label { font-size: .78rem; opacity: .92; margin-top: 6px; line-height: 1.3; }
.vk-hero-cue {
    font-size: .68rem; margin-top: 8px; opacity: .55;
    letter-spacing: .04em; transition: opacity .15s ease;
}

/* ---------- icon cards ---------- */
.vk-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
    gap: 16px;
    margin: 10px 0 22px;
}
.vk-card {
    background: #ffffff;
    border: 1px solid rgba(15,23,42,.08);
    border-left: 5px solid #0e7490;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 2px 10px rgba(15,23,42,.05);
    transition: transform .15s ease, box-shadow .15s ease;
    scroll-margin-top: 90px;
}
.vk-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(15,23,42,.12); }
.vk-card:target {
    border-left-color: #f59e0b;
    box-shadow: 0 0 0 3px rgba(245,158,11,.35), 0 8px 20px rgba(15,23,42,.12);
}
.vk-card-icon { font-size: 1.5rem; }
.vk-card-title { font-size: 1.05rem; font-weight: 800; color: #0e2a35; margin: 6px 0 4px; }
.vk-card-text { font-size: .92rem; color: #334155; line-height: 1.45; margin: 0 0 8px; }
.vk-card-src { font-size: .72rem; color: #64748b; }
.vk-card-src a { color: #0e7490; text-decoration: none; }
.vk-card-src a:hover { text-decoration: underline; }

/* ---------- status pill ---------- */
.vk-pill {
    display: inline-block;
    font-size: .68rem;
    font-weight: 700;
    letter-spacing: .05em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 999px;
    margin-bottom: 6px;
}

/* ---------- photo banner ---------- */
.vk-banner {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
    margin: 4px 0 26px;
    box-shadow: 0 8px 24px rgba(15,23,42,.18);
    height: 200px;
}
.vk-banner-img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
}
.vk-banner-fade {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(6,20,28,0) 45%, rgba(6,20,28,.82) 100%);
}
.vk-banner-caption {
    position: absolute;
    left: 18px;
    right: 18px;
    bottom: 12px;
    color: #e7f6fb;
    font-size: .78rem;
    line-height: 1.35;
    text-shadow: 0 1px 3px rgba(0,0,0,.5);
}
.vk-banner-caption b { color: #ffffff; }
@media (max-width: 700px) {
    .vk-banner { height: 150px; }
}

/* ---------- call to action ---------- */
.vk-cta {
    display: flex;
    align-items: center;
    gap: 18px;
    flex-wrap: wrap;
    background: linear-gradient(135deg, #0f766e 0%, #0e7490 55%, #155e75 100%);
    border-radius: 16px;
    padding: 22px 26px;
    margin: 6px 0 26px;
    text-decoration: none !important;
    color: #fff !important;
    box-shadow: 0 8px 24px rgba(13,148,136,.28);
    transition: transform .15s ease, box-shadow .15s ease;
}
.vk-cta:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 34px rgba(13,148,136,.42);
}
.vk-cta-icon { font-size: 2.4rem; line-height: 1; }
.vk-cta-body { flex: 1 1 260px; }
.vk-cta-title { font-size: 1.25rem; font-weight: 800; margin-bottom: 4px; }
.vk-cta-text { font-size: .92rem; opacity: .93; line-height: 1.45; }
.vk-cta-btn {
    background: #ffffff;
    color: #0f766e;
    font-weight: 800;
    font-size: .92rem;
    padding: 11px 22px;
    border-radius: 999px;
    white-space: nowrap;
}

/* ---------- roadmap phases ---------- */
.vk-road {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 14px;
    margin: 10px 0 24px;
}
.vk-phase {
    position: relative;
    background: #ffffff;
    border: 1px solid rgba(15,23,42,.08);
    border-top: 5px solid var(--vk-accent, #475569);
    border-radius: 12px;
    padding: 16px 16px 18px;
    box-shadow: 0 2px 10px rgba(15,23,42,.05);
    transition: transform .15s ease, box-shadow .15s ease;
}
.vk-phase:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(15,23,42,.12); }
.vk-phase-step {
    font-size: .7rem; font-weight: 700; color: #94a3b8;
    letter-spacing: .08em; text-transform: uppercase;
}
.vk-phase-title { font-size: 1rem; font-weight: 800; color: #0e2a35; margin: 4px 0 8px; }
.vk-phase-text { font-size: .88rem; color: #334155; line-height: 1.45; }

@media (prefers-color-scheme: dark) {
    /* Set only the non-accent edges, so the coloured left/top border survives. */
    .vk-card {
        background: #1c2732;
        border-top-color: rgba(255,255,255,.08);
        border-right-color: rgba(255,255,255,.08);
        border-bottom-color: rgba(255,255,255,.08);
    }
    .vk-phase {
        background: #1c2732;
        border-right-color: rgba(255,255,255,.08);
        border-bottom-color: rgba(255,255,255,.08);
        border-left-color: rgba(255,255,255,.08);
    }
    .vk-card-title, .vk-phase-title { color: #f1f5f9; }
    .vk-card-text, .vk-phase-text { color: #cbd5e1; }
    .vk-card-src { color: #94a3b8; }
    .vk-card-src a { color: #67e8f9; }
}
</style>
"""


@dataclass
class HeroStat:
    number: str
    label: str
    anchor: str | None = None  # id of the card this number explains
    cue: str = "Tap for the story"


@dataclass
class Card:
    icon: str
    title: str
    text: str
    card_id: str | None = None
    status: str | None = None  # key of STATUS_STYLES
    sources: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Phase:
    step: str
    title: str
    text: str
    status: str = "planned"


def _pill(status: str) -> str:
    if status not in STATUS_STYLES:
        return ""
    fg, bg, label = STATUS_STYLES[status]
    return f'<div class="vk-pill" style="color:{fg};background:{bg};">{label}</div>'


def render_hero_stats(stats: list[HeroStat]) -> None:
    """Big headline numbers. Cards with an anchor become real links to their detail card."""
    html = []
    for s in stats:
        inner = (
            f'<div class="vk-hero-num">{s.number}</div>'
            f'<div class="vk-hero-label">{s.label}</div>'
        )
        if s.anchor:
            html.append(
                f'<a class="vk-hero-card" href="#{s.anchor}">{inner}'
                f'<div class="vk-hero-cue">{s.cue} ↓</div></a>'
            )
        else:
            html.append(f'<div class="vk-hero-card">{inner}</div>')
    st.html(f'{VK_CSS}<div class="vk-hero">{"".join(html)}</div>')


def render_cards(cards: list[Card]) -> None:
    html = []
    for c in cards:
        el_id = f' id="{c.card_id}"' if c.card_id else ""
        pill = _pill(c.status) if c.status else ""
        src = ""
        if c.sources:
            links = " &middot; ".join(
                f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'
                for label, url in c.sources
            )
            src = f'<div class="vk-card-src">Source: {links}</div>'
        html.append(
            f'<div class="vk-card"{el_id}>{pill}'
            f'<div class="vk-card-icon">{c.icon}</div>'
            f'<div class="vk-card-title">{c.title}</div>'
            f'<div class="vk-card-text">{c.text}</div>{src}</div>'
        )
    st.html(f'{VK_CSS}<div class="vk-grid">{"".join(html)}</div>')


def render_photo_banner(filename: str, caption: str) -> None:
    """Full-width real photo with a bottom fade + small credit line."""
    src = _image_data_uri(filename)
    if not src:
        return
    st.html(
        f'{VK_CSS}<div class="vk-banner">'
        f'<img class="vk-banner-img" src="{src}" alt="{caption}">'
        f'<div class="vk-banner-fade"></div>'
        f'<div class="vk-banner-caption">{caption}</div></div>'
    )


def render_cta(icon: str, title: str, text: str, url: str, button_label: str) -> None:
    """Full-width banner for the one action we most want a visitor to take."""
    st.html(
        f'{VK_CSS}<a class="vk-cta" href="{url}" target="_blank" rel="noopener">'
        f'<div class="vk-cta-icon">{icon}</div>'
        f'<div class="vk-cta-body"><div class="vk-cta-title">{title}</div>'
        f'<div class="vk-cta-text">{text}</div></div>'
        f'<div class="vk-cta-btn">{button_label}</div></a>'
    )


def render_roadmap(phases: list[Phase]) -> None:
    html = []
    for p in phases:
        accent = STATUS_STYLES.get(p.status, STATUS_STYLES["planned"])[0]
        html.append(
            f'<div class="vk-phase" style="--vk-accent:{accent};">'
            f'{_pill(p.status)}'
            f'<div class="vk-phase-step">{p.step}</div>'
            f'<div class="vk-phase-title">{p.title}</div>'
            f'<div class="vk-phase-text">{p.text}</div></div>'
        )
    st.html(f'{VK_CSS}<div class="vk-road">{"".join(html)}</div>')
