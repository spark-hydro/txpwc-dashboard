"""One visual language for observed vs. simulated, used by every Model
Performance chart so they read the same way.

- Observed: hollow red circles -- a strong red outline over a faint red fill.
- Simulated: green; a second simulation is blue, a third purple.
"""

from __future__ import annotations

OBS_COLOR = "#dc2626"
OBS_FILL = "rgba(220, 38, 38, 0.12)"
SIM_COLORS = ["#2e9e5b", "#2563eb", "#7c3aed"]


def obs_marker(size: int = 7, symbol: str = "circle") -> dict:
    return dict(symbol=symbol, size=size, color=OBS_FILL, line=dict(color=OBS_COLOR, width=1.6))


def sim_color(index: int) -> str:
    return SIM_COLORS[index % len(SIM_COLORS)]
