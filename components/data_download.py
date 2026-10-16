"""Download panel for the Model Performance observation points.

Pick families (all of them, or any mix of streamflow / reservoirs / wells /
salinity), optionally narrow each to specific points, choose locations and/or
time series, and get CSV files back -- one CSV when a single file is asked for,
a ZIP of CSVs otherwise.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass

import pandas as pd
import streamlit as st


@dataclass
class Family:
    key: str
    label: str
    locations: pd.DataFrame
    series: pd.DataFrame
    loc_id: str       # id column in `locations`
    series_id: str    # id column in `series`
    name_col: str | None = None  # human-readable name column in `locations`


def _point_label(fam: Family, row) -> str:
    ident = str(row[fam.loc_id])
    name = row[fam.name_col] if fam.name_col else None
    return f"{name} ({ident})" if name and str(name) != ident else ident


def _csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def render_download_panel(
    families: list[Family], basin: str = "Pecos", map_selection: dict[str, list[str]] | None = None,
) -> None:
    labels = {f.key: f.label for f in families}
    st.subheader("Download data")
    with st.container():
        st.caption(
            "Choose the families you want — all of them or any mix — then what to include. "
            "One family and one table downloads as a CSV; anything larger comes as a ZIP of CSVs."
        )
        picked_keys = st.multiselect(
            "Families", options=[f.key for f in families], default=[f.key for f in families],
            format_func=labels.get, key="dl_families",
        )
        content = st.radio(
            "Include", ["Locations", "Time series", "Both"], index=2, key="dl_content",
            help="Locations: one row per point (name, lat/lon, summary). Time series: the observed and simulated values.",
        )
        use_map = False
        if map_selection:
            total = sum(len(v) for v in map_selection.values())
            use_map = st.checkbox(
                f"Only the {total:,} points selected on the map", value=True, key="dl_use_map",
                help="Uncheck to go back to the families chosen above.",
            )
        narrow = st.checkbox("Choose individual points", value=False, key="dl_narrow")

        files: dict[str, pd.DataFrame] = {}
        n_points = 0
        for fam in families:
            if fam.key not in picked_keys or (use_map and fam.key not in map_selection):
                continue
            loc = fam.locations
            ids = loc[fam.loc_id].astype(str).tolist()
            if use_map:
                ids = [i for i in ids if i in set(map_selection.get(fam.key, []))]
            if narrow:
                names = {str(r[fam.loc_id]): _point_label(fam, r) for _, r in loc.iterrows()}
                chosen = st.multiselect(
                    labels[fam.key], options=ids, default=ids, format_func=lambda i, n=names: n.get(i, i),
                    key=f"dl_pts_{fam.key}",
                )
            else:
                chosen = ids
            if not chosen:
                continue
            n_points += len(chosen)
            if content in ("Locations", "Both"):
                files[f"{basin}_{fam.key}_locations.csv"] = loc[loc[fam.loc_id].astype(str).isin(chosen)]
            if content in ("Time series", "Both"):
                files[f"{basin}_{fam.key}_timeseries.csv"] = fam.series[fam.series[fam.series_id].astype(str).isin(chosen)]

        if not files:
            st.info("Nothing selected yet.")
            return

        rows = sum(len(df) for df in files.values())
        st.caption(f"{n_points:,} points · {len(files)} file{'s' if len(files) > 1 else ''} · {rows:,} rows")
        st.dataframe(
            pd.DataFrame({"File": list(files), "Rows": [len(df) for df in files.values()]}),
            hide_index=True, width="stretch",
        )
        if len(files) == 1:
            (name, df), = files.items()
            st.download_button("Download CSV", _csv_bytes(df), file_name=name, mime="text/csv", key="dl_button_csv")
        else:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for name, df in files.items():
                    zf.writestr(name, _csv_bytes(df))
            st.download_button(
                "Download ZIP", buf.getvalue(), file_name=f"{basin}_selected_data.zip", mime="application/zip",
                key="dl_button_zip",
            )
