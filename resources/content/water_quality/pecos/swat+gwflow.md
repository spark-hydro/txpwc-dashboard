# Water Quality

The Pecos Basin TxPWC application evaluates **salinity and trace-constituent transport** after a treated produced-water return to the Pecos River near Red Bluff Reservoir.

- **Model**: SWAT+/gwflow coupled watershed–groundwater (Pecos Basin)
- **Data**: TxPWC Pilot Testing Report (April 2026) — concentrations anchored to measured values across three treatment stages
- **Contaminants tracked**: TDS (conservative), NH₃ (reactive / nitrification), PFAS (strongly retarded by vadose air–water interface adsorption)

## Interactive Contaminant-Transport Lab

An interactive teaching lab (embedded below) lets you explore how contaminants from a **treated produced-water return** move differently through a Pecos-Basin aquifer toward the Pecos River near Red Bluff Reservoir:

- **Salinity (TDS / Cl⁻ / Na⁺)** — *conservative*: travels with the groundwater (R = 1).
- **PFAS** — *strongly retarded*: trapped on **air–water interfaces** in the unsaturated zone (R ≈ 10–100×), so it lags far behind the salt front.
- **Ammonia (NH₃)** — the residual flagged in the TxPWC pilot report as the key concern for surface-water discharge.

### How to Use the Lab

1. **Pick a scenario** (top-right of the lab): Baseline, PFAS Legacy, Drought, or Pump & Treat.
2. **Set the treatment level** in the *Treated produced-water return* panel (PW / DPW / PDPW) — the salt, PFAS and NH₃ sliders snap to the report's measured values.
3. **Release a pulse** and watch the **plan view**: the salt front races ahead while PFAS stays pinned near the field.
4. Open the **cross-section (side view)** to see PFAS trapped in the vadose zone while salt drains to the water table, which slopes down toward the river.
5. Click a **river cell** to move the return point; click **open ground** to add a pumping well and test capture vs. vadose rebound.
6. The **Learn tab** has the scenario guide, a chemical-by-chemical transport table, the governing equations (Darcy flow, well drawdown, river routing), and all references.

The lab runs as a self-contained client-side app; use the **full-screen button** below the embed if it feels cramped.
