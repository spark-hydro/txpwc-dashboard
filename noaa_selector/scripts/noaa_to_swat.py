import pandas as pd
import os

def create_swat_pcp(df, station_id, out_folder):
    """
    Convert NOAA dataframe to SWAT+ precipitation file (.pcp)
    """
    if "PRCP" not in df.columns:
        raise ValueError("NOAA data does not contain PRCP column")

    df_pcp = df[["date", "PRCP"]].copy()
    df_pcp["year"] = df_pcp["date"].dt.year
    df_pcp["month"] = df_pcp["date"].dt.month
    df_pcp["day"] = df_pcp["date"].dt.day

    df_pcp = df_pcp[["year", "month", "day", "PRCP"]]

    out_path = os.path.join(out_folder, f"{station_id}.pcp")
    df_pcp.to_csv(out_path, sep=" ", index=False, header=False)

    return out_path


def create_swat_tmp(df, station_id, out_folder):
    """
    Convert NOAA dataframe to SWAT+ temperature file (.tmp)
    """
    if "TMAX" not in df.columns or "TMIN" not in df.columns:
        raise ValueError("NOAA data missing TMAX or TMIN")

    df_tmp = df[["date", "TMAX", "TMIN"]].copy()
    df_tmp["year"] = df_tmp["date"].dt.year
    df_tmp["month"] = df_tmp["date"].dt.month
    df_tmp["day"] = df_tmp["date"].dt.day

    df_tmp = df_tmp[["year", "month", "day", "TMAX", "TMIN"]]

    out_path = os.path.join(out_folder, f"{station_id}.tmp")
    df_tmp.to_csv(out_path, sep=" ", index=False, header=False)

    return out_path


def create_swat_sta(station_row, out_folder, var_type="pcp"):
    """
    Create SWAT+ station metadata file (.sta)
    """
    lat = station_row["latitude"]
    lon = station_row["longitude"]
    elev = station_row["elevation"]
    name = station_row["name"]
    sid = station_row["id"]

    out_path = os.path.join(out_folder, f"{sid}.{var_type}.sta")

    with open(out_path, "w") as f:
        f.write(f"{sid}\n")
        f.write(f"{lat:.4f} {lon:.4f} {elev:.1f}\n")
        f.write(f"{name}\n")

    return out_path

