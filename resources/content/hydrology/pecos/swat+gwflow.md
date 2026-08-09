# Hydrology

## Overview

This page summarizes the hydrologic behavior of the Pecos River Basin, with focus on streamflow, baseflow, groundwater–surface water interaction, and spatial and temporal variability across the watershed. The underlying SWAT+gwflow model is currently calibrated for streamflow (see the calibration ensemble on the [Scenarios](/Scenarios) page); reservoir representation and a salinity transport module are the next additions — see **Status** below.

## Hydrologic Focus

The hydrology analysis supports:

- Historical streamflow evaluation at key stations  
- Comparison of simulated and observed flow behavior  
- Assessment of low-flow and baseflow conditions  
- Evaluation of groundwater contributions to streamflow  
- Basin-scale response under alternative management scenarios  

## Streamflow Dynamics

Streamflow in the Pecos River Basin varies across space and time due to climate forcing, watershed characteristics, channel routing, and groundwater interaction:

- Daily, monthly, and seasonal flow variability  
- High-flow and low-flow periods  
- Upstream and downstream flow differences  

The **Basin Indicators** panel below plots the current observed-vs-simulated streamflow and flow-duration curve directly from the calibrated model.

## Baseflow and Groundwater Interaction

Groundwater–surface water interaction is an important component of the Pecos River system:

- Baseflow contribution to streamflow  
- Gaining and losing stream reaches  
- Temporal changes in groundwater discharge  

The **Basin Indicators** panel also includes an observed-vs-simulated groundwater comparison across monitored sites.

## Climate and Hydrologic Variability

Hydrologic conditions are influenced by climate variability and forcing inputs used in the model. Precipitation and temperature summaries, historical climate patterns, and hydrologic sensitivity to wet/dry periods are covered in depth on the [Climate Analysis](/Climate_Analysis) page.

## Status

**Now:** SWAT+gwflow is calibrated for streamflow across the Pecos Basin (see Scenarios page for the calibration ensemble, and Basin Indicators below for the current observed-vs-simulated fit).

🚧 **Next:**

- Add reservoir/dam operations to the model  
- Add a salinity transport module  
- Recalibrate against streamflow **and** salinity observations  
- Simulate produced-water release scenarios: how streamflow and salinity/contaminant concentrations change and distribute downstream and into groundwater