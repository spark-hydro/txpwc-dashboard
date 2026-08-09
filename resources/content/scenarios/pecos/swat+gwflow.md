# Scenarios

## Overview

This page describes the scenario-analysis component of the Pecos River TxPWC dashboard: evaluating how different purified produced-water release and reuse strategies influence hydrology and water quality across the basin.

The model is currently calibrated for streamflow (see **Model Calibration** below). Scenario simulations through SWAT+gwflow itself are planned once reservoir operations and a salinity-transport module are added — see **Planned SWAT+gwflow Scenarios**. In the meantime, the **Interactive Reservoir Release Lab** at the bottom of this page lets you explore real release-strategy trade-offs today, using the Pecos's actual 2000–2020 management history.

## Model Calibration (Current)

Getting the physical model right comes first. The Pecos SWAT+gwflow model is calibrated against observed streamflow using PEST++, running thousands of parameter realizations and narrowing them down to the set that best matches real observations.

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/fdc_scenarios.png?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/fdc_scenarios.png?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Flow-duration curve from the PEST++ calibration ensemble: gray lines are individual parameter realizations, the green band is the optimum subset, the blue line is the best-performing realization, and the magenta line is the calibrated baseline — together showing how the model converges toward the observations. Tap / click to zoom.*

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/mou.png?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/mou.png?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Multi-objective calibration trade-off space (PESTPP-MOU): each point is one parameter realization scored against two competing calibration objectives. Gray points are the prior, untested set; the blue and magenta clusters are posterior realizations retained after conditioning on observations. The same PESTPP-MOU workflow will later be reused to rank candidate release and irrigation-reuse strategies once the scenario model below is in place. Tap / click to zoom.*

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/ua.gif?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/ua.gif?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Animated view of the PEST++ ensemble narrowing across iterations as it converges toward the calibrated parameter set. Tap / click to zoom.*

## Planned SWAT+gwflow Scenarios

🚧 **Not yet run in SWAT+gwflow itself** — these depend on the reservoir and salinity-transport additions described on the [Hydrology](/Hydrology) page. (The **Interactive Reservoir Release Lab** at the bottom of this page already lets you explore release strategy conceptually, with real historical data — the cards below are about running the same kind of question through the calibrated physics model.)

<!-- SPLIT:planned-cards -->

**Key questions these scenarios will answer:** How do impacts change with release location, timing, and magnitude? Which reaches are most sensitive to alternative strategies? Which scenarios appear most protective under uncertainty?

## Relevant PEST++ Tools

- **PESTPP-MOU** for constrained multi-objective optimization  
- **PESTPP-SEN** for sensitivity analysis  
- **PESTPP-IES** for optimization under uncertainty  
- **PESTPP-SWP** for scenario analysis using predefined parameter or input sets 

## Status

🚧 **Planned for SWAT+gwflow**, once scenario simulations are available (the reservoir lab below already covers interactive release maps and one-click scenarios in its own right): scenario-specific hydrographs and salinity plots from the calibrated model, side-by-side baseline vs. scenario comparisons, summary tables of key metrics, and scenario selection from the sidebar.

## Interactive Reservoir Release Lab

A companion teaching tool (embedded below) lets you explore release strategy across the Pecos's **5 major dams** — Santa Rosa, Sumner, Brantley, Avalon, and Red Bluff — using their real 2000–2020 management history from the SWAT+gwflow reservoir model. A release strategy here (or eventually in SWAT+gwflow itself) comes down to the same handful of factors: release point, flow rate, timing, background hydrologic condition, and the water quality of what's released.

<!-- SPLIT:lab-tabs-cards -->

The **Flow & Management** tab ships with 5 one-click scenarios so you don't have to start from a blank slate:

<!-- SPLIT:oneclick-cards -->

Every dam can also be adjusted individually — turn on a custom rule, scale its release up or down, or set a guaranteed minimum floor — to build a policy that isn't one of the five presets.

🚧 **Status**: research prototype. The "dilution capacity" shown here is a simplified stand-in — once the Pecos salinity-transport model is finished (see [Hydrology](/Hydrology) status), it will be replaced by reach-by-reach simulated salt transport from the [Salinity Lab](/Water_Quality), closing the loop between reservoir management and where reuse water is actually safe to place.
