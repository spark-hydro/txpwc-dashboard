import plotly.express as px
import streamlit as st

def plot_noaa_interactive(df, station_name):
    if df.empty:
        st.warning("No data available for this station.")
        return

    st.subheader(f"📈 {station_name} — Interactive Plotly Charts")

    variables = [c for c in df.columns if c not in ["date"]]

    for var in variables:
        fig = px.line(
            df,
            x="date",
            y=var,
            title=f"{var}",
            labels={"date": "Date", var: "Value"},
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
