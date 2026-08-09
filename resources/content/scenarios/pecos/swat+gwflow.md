# Scenarios

## Overview

This page describes the scenario-analysis component of the Pecos River TxPWC dashboard. The main purpose is to evaluate how different purified produced-water release and reuse strategies influence hydrology and water quality across the basin.

The model is currently calibrated for streamflow (see **Model Calibration** below). Scenario simulations through SWAT+gwflow itself are planned once reservoir operations and a salinity-transport module are added — see **Planned SWAT+gwflow Scenarios**. In the meantime, the **Interactive Reservoir Release Lab** at the bottom of this page lets you explore real release-strategy trade-offs today, using the Pecos's actual 2000–2020 management history.

## Scenario Types (Planned)

- Baseline / existing-condition simulation
- In-stream produced-water release
- Land application / irrigation reuse

## Model Calibration (Current)

Getting the physical model right comes first. The Pecos SWAT+gwflow model is calibrated against observed streamflow using PEST++, running thousands of parameter realizations and narrowing them down to the set that best matches real observations.

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/fdc_scenarios.png?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/fdc_scenarios.png?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Flow-duration curve from the PEST++ calibration ensemble: gray lines are individual parameter realizations, the green band is the optimum subset, the blue line is the best-performing realization, and the magenta line is the calibrated baseline — together showing how the model converges toward the observations. Tap / click to zoom.*

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/mou.png?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/mou.png?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Multi-objective calibration trade-off space (PESTPP-MOU): each point is one parameter realization scored against two competing calibration objectives. Gray points are the prior, untested set; the blue and magenta clusters are posterior realizations retained after conditioning on observations. The same PESTPP-MOU workflow will later be reused to rank candidate release and irrigation-reuse strategies once the scenario model below is in place. Tap / click to zoom.*

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/ua.gif?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/ua.gif?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Animated view of the PEST++ ensemble narrowing across iterations as it converges toward the calibrated parameter set. Tap / click to zoom.*

## Planned SWAT+gwflow Scenarios

🚧 **Not yet run in SWAT+gwflow itself** — these depend on the reservoir and salinity-transport additions described on the [Hydrology](/Hydrology) page. (The **Interactive Reservoir Release Lab** at the bottom of this page already lets you explore release strategy conceptually, with real historical data — this section is about running the same kind of question through the calibrated physics model.)

### In-Stream Produced-Water Release

Once the model includes reservoir operations and a salinity/contaminant transport module, scenarios will simulate a produced-water release at a chosen point on the river and track how streamflow changes downstream, and how salinity (or another constituent) disperses through the river and into groundwater over time and distance.

### Land Application / Irrigation Reuse

A second track will evaluate reusing treated produced water for irrigation instead of (or alongside) in-stream release — showing that reuse can benefit agriculture, not only the river:

- Different crop types and irrigation water-use rates, with land-use classes derived from the existing SWAT+ model
- Distance from Red Bluff Reservoir as a feasibility factor
- Whether treatment needs to be improved to reduce a given constituent (e.g., salinity) enough to protect the river — high in-stream salinity can be lethal to fish
- Groundwater impact of sustained irrigation water quantities over time

### Higher-Resolution Groundwater (Future)

Groundwater results will later be refined using a **MODFLOW 6 unstructured grid**, concentrating finer resolution in the areas that need it most (e.g., near release or irrigation zones) rather than uniformly across the basin.

### Key Questions These Scenarios Will Answer

- How do impacts change with release location, timing, and magnitude?
- Which reaches are most sensitive to alternative strategies?
- Which scenarios appear most protective under uncertainty?

## Relevant PEST++ Tools

- **PESTPP-MOU** for constrained multi-objective optimization  
- **PESTPP-SEN** for sensitivity analysis  
- **PESTPP-IES** for optimization under uncertainty  
- **PESTPP-SWP** for scenario analysis using predefined parameter or input sets 

## Status

🚧 **Planned for SWAT+gwflow**, once scenario simulations are available (the reservoir lab below already covers interactive release maps and one-click scenarios in its own right):

- Scenario-specific hydrographs and salinity plots from the calibrated model
- Side-by-side baseline vs. scenario comparisons
- Summary tables of key metrics
- Selection of predefined SWAT+gwflow scenarios from the sidebar or page controls

## Release Configuration

A release strategy — whether tested in the lab below or, eventually, in SWAT+gwflow itself — is defined by combining several factors:

- Release point location
- Release flow rate
- Duration or timing of release
- Background hydrologic condition
- Water quality characteristics of the released water

These inputs can produce substantially different downstream and groundwater responses.

## Interactive Reservoir Release Lab

A companion teaching tool (embedded below) lets you explore release strategy across the Pecos's **5 major dams** — Santa Rosa, Sumner, Brantley, Avalon, and Red Bluff — using their real 2000–2020 management history from the SWAT+gwflow reservoir model:

- **Reservoir Map** — real dam locations, sized and colored by mean annual release.
- **Flow & Management** — set your own release policy for any dam, or load a one-click scenario, and watch the river respond.
- **Where to Place Reuse Water** — drag a candidate reuse site along the river; the reach lights up green / yellow / red.
- **Salinity & Fish** — cross-references release choices against documented natural salinity sources and the Pecos pupfish's verified range.

The **Flow & Management** tab ships with 5 one-click scenarios so you don't have to start from a blank slate:

- **Reset to history** — no changes; shows exactly what the 5 dams actually did, 2000–2020.
- **2011–13 drought, unchanged** — jumps the timeline to the real New Mexico/Texas drought, historical policy — see how the system held up (or didn't) under real stress.
- **Guarantee minimum flow, everywhere** — applies a minimum-instream-flow floor across all 5 dams at once.
- **Protect the Avalon → Red Bluff reach** — a targeted policy for the stretch closest to the candidate reuse zone.
- **Release 30% more, everywhere** — stress-tests the system against a basin-wide 30% release increase.

Every dam can also be adjusted individually — turn on a custom rule, scale its release up or down, or set a guaranteed minimum floor — to build a policy that isn't one of the five presets.

🚧 **Status**: research prototype. The "dilution capacity" shown here is a simplified stand-in — once the Pecos salinity-transport model is finished (see [Hydrology](/Hydrology) status), it will be replaced by reach-by-reach simulated salt transport from the [Salinity Lab](/Water_Quality), closing the loop between reservoir management and where reuse water is actually safe to place.
