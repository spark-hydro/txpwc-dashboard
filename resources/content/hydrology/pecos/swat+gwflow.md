# Hydrology

## Overview

The Pecos River is declining, naturally hypersaline, and still capable of catastrophic floods — exactly what makes it a demanding, credible test basin for produced-water reuse. SWAT+gwflow is currently calibrated for streamflow across the basin; reservoir operations and a salinity-transport module are next — see **Status**.

## What This Page Covers

- **Streamflow** — daily-to-seasonal variability, high/low-flow periods, upstream vs. downstream differences, and the current observed-vs-simulated fit *(Basin Indicators, below)*
- **Baseflow & groundwater** — gaining/losing reaches and groundwater's contribution to streamflow *(Basin Indicators, below)*
- **Climate drivers** — precipitation, temperature, and wet/dry variability are covered in depth on [Climate Analysis](/Climate_Analysis)

## Status

**Now:** SWAT+gwflow is calibrated for streamflow across the Pecos Basin — see **Model Calibration** below for the ensemble, and **Basin Indicators** further down for the current observed-vs-simulated fit.

🚧 **Next:**

- Add reservoir/dam operations to the model — Red Bluff Reservoir has lost roughly 20,400 acre-ft of its original 310,000 acre-ft capacity to sedimentation since it was built in 1936 ([TWDB volumetric survey](https://www.twdb.texas.gov/hydro_survey/redbluff/2011-11/RedBluff2011_FinalReport.pdf)), which the reservoir module will need to account for  
- Add a salinity transport module  
- Recalibrate against streamflow **and** salinity observations  
- Simulate produced-water release scenarios: how streamflow and salinity/contaminant concentrations change and distribute downstream and into groundwater

## Model Calibration

Getting the physical model right comes first. The Pecos SWAT+gwflow model is calibrated against observed streamflow using PEST++, running thousands of parameter realizations and narrowing them down to the set that best matches real observations.

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/fdc_scenarios.png?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/fdc_scenarios.png?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Flow-duration curve from the PEST++ calibration ensemble: gray lines are individual parameter realizations, the green band is the optimum subset, the blue line is the best-performing realization, and the magenta line is the calibrated baseline — together showing how the model converges toward the observations. Tap / click to zoom.*

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/mou.png?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/mou.png?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Multi-objective calibration trade-off space (PESTPP-MOU): each point is one parameter realization scored against two competing calibration objectives. Gray points are the prior, untested set; the blue and magenta clusters are posterior realizations retained after conditioning on observations. The same PESTPP-MOU workflow will later be reused to rank candidate release and irrigation-reuse strategies once the scenario model is in place — see [Scenarios](/Scenarios). Tap / click to zoom.*

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/ua.gif?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/ua.gif?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Animated view of the PEST++ ensemble narrowing across iterations as it converges toward the calibrated parameter set. Tap / click to zoom.*

## Regional Context: Why the Pecos Is Different

The Pecos is one of the most intensively studied rivers in the American Southwest — for the same reasons this project exists.
