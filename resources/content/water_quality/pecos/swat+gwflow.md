# Water Quality

The Pecos Basin TxPWC application evaluates **salinity transport** after a treated produced-water return to the Pecos River near Red Bluff Reservoir.

- **Model**: SWAT+/gwflow coupled watershed–groundwater (Pecos Basin)
- **Data**: TxPWC Pilot Testing Report (April 2026) — concentrations anchored to measured values across three treatment stages
- **Constituent tracked**: TDS (conservative — travels with the groundwater, R = 1)

## Interactive Salinity-Transport Lab

An interactive teaching lab (embedded below) lets you explore how salinity from a **treated produced-water return** moves through a Pecos-Basin aquifer toward the Pecos River near Red Bluff Reservoir — and how treatment level, aquifer properties, and pumping change the outcome.

### Scenario Guide — What Changes and Why

Each scenario in the top-right dropdown snaps all sliders to a physically plausible configuration for the Pecos Basin — see the cards below. Load one to apply it instantly, then adjust sliders one at a time to see what drives each result.

### How to Use the Lab

1. **Pick a scenario** (top-right of the lab): Pristine Baseline, High TDS Loading, Drought Year, or Pump & Treat.
2. **Set the treatment level** in the *Treated produced-water return* panel (PW / DPW / PDPW) — the salt-load slider snaps to the report's measured TDS values.
3. **Release a pulse** and watch the **plan view**: the salt front advances outward from the return point toward the river.
4. Open the **cross-section (side view)** to see how salt drains through the vadose zone to the water table, which slopes down toward the river.
5. Click a **river cell** to move the return point; click **open ground** to add a pumping well and test capture vs. rebound.
6. The **Learn tab** has this scenario guide, the governing equations (Darcy flow, well drawdown, river routing), and all references.

The lab runs as a self-contained client-side app; use the **full-screen button** below the embed if it feels cramped.
