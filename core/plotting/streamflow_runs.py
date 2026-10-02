from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

RUN_COLORS = {"v30ext": "#7a7f86", "v33": "#008080", "v52prod": "#0f8fb4"}


def _gauge_pairs(monthly: pd.DataFrame, gauge_id: str, run_key: str) -> pd.DataFrame:
    sub = monthly[monthly["gauge_id"] == gauge_id].copy()
    sim_col = f"sim_{run_key}_m3s"
    sub = sub.dropna(subset=["observed_m3s", sim_col])
    sub["cal_month"] = sub["month"].str.slice(5, 7).astype(int)
    return sub


def compute_gauge_stats(monthly: pd.DataFrame, gauge_id: str, run_key: str) -> dict | None:
    """NSE/KGE/PBIAS/R2/RMSE and Jan-Dec climatology, observed vs one run at one gauge."""
    pairs = _gauge_pairs(monthly, gauge_id, run_key)
    if len(pairs) < 12:
        return None

    obs = pairs["observed_m3s"].to_numpy(dtype=float)
    sim = pairs[f"sim_{run_key}_m3s"].to_numpy(dtype=float)

    mo = obs.mean()
    nse = 1 - np.sum((sim - obs) ** 2) / np.sum((obs - mo) ** 2)
    pbias = 100 * (sim.sum() - obs.sum()) / obs.sum()
    r = np.corrcoef(sim, obs)[0, 1] if len(obs) >= 3 else np.nan
    r2 = r ** 2 if not np.isnan(r) else np.nan
    rmse = np.sqrt(np.mean((sim - obs) ** 2))
    alpha = sim.std() / obs.std() if obs.std() else np.nan
    beta = sim.mean() / obs.mean() if obs.mean() else np.nan
    kge = 1 - np.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2) if not np.isnan(r) else np.nan

    clim = pairs.groupby("cal_month").agg(obs=("observed_m3s", "mean"), sim=(f"sim_{run_key}_m3s", "mean"))
    clim = clim.reindex(range(1, 13))
    co = clim["obs"].to_numpy(dtype=float)
    cs = clim["sim"].to_numpy(dtype=float)
    ok = ~np.isnan(co) & ~np.isnan(cs)
    sr = np.corrcoef(cs[ok], co[ok])[0, 1] if ok.sum() >= 3 else np.nan

    return {
        "n": len(pairs), "obs_mean": obs.mean(), "sim_mean": sim.mean(),
        "ratio": sim.mean() / obs.mean() if obs.mean() else np.nan,
        "nse": nse, "kge": kge, "pbias": pbias, "r2": r2, "rmse": rmse, "seasonal_r": sr,
        "clim_obs": co, "clim_sim": cs,
    }


def plot_seasonal_shape(stats: dict, run_key: str, normalize: bool = False) -> go.Figure:
    """Observed vs. one run's mean flow by calendar month."""
    co, cs = stats["clim_obs"], stats["clim_sim"]
    if normalize:
        co = co / np.nanmean(co)
        cs = cs / np.nanmean(cs)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=MONTH_NAMES, y=co, mode="lines+markers", name="USGS observed",
                              line=dict(color="#111827", width=2), marker=dict(size=7)))
    fig.add_trace(go.Scatter(x=MONTH_NAMES, y=cs, mode="lines+markers", name="Simulated",
                              line=dict(color=RUN_COLORS.get(run_key, "#0f8fb4"), width=2), marker=dict(size=7)))

    fig.update_layout(
        yaxis_title="flow ÷ own mean" if normalize else "m³/s",
        template="plotly_white",
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_multirun_timeseries(monthly: pd.DataFrame, gauge_id: str, run_keys: list[str], log_scale: bool = True) -> go.Figure:
    """Observed monthly flow against several runs, 2002-2007."""
    sub = monthly[monthly["gauge_id"] == gauge_id].sort_values("month")
    fig = go.Figure()

    obs = sub["observed_m3s"].clip(lower=0.01) if log_scale else sub["observed_m3s"]
    fig.add_trace(go.Scatter(x=sub["month"], y=obs, mode="lines+markers", name="USGS observed",
                              line=dict(color="#111827", width=1.8), marker=dict(size=4)))

    for run_key in run_keys:
        col = f"sim_{run_key}_m3s"
        if col not in sub.columns:
            continue
        y = sub[col].clip(lower=0.01) if log_scale else sub[col]
        fig.add_trace(go.Scatter(x=sub["month"], y=y, mode="lines+markers", name=run_key,
                                  line=dict(color=RUN_COLORS.get(run_key, "#888")), marker=dict(size=3)))

    fig.update_layout(
        yaxis=dict(title="m³/s (log)" if log_scale else "m³/s", type="log" if log_scale else "linear"),
        xaxis=dict(tickangle=-45),
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=20, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
