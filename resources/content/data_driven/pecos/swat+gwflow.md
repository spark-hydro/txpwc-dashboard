# Data-Driven Analysis

## Overview

This page describes how data-driven and machine-learning methods can complement the physically based Pecos River TxPWC modeling framework.

The goal is not to replace SWAT+gwflow, but to enhance model analysis, accelerate scenario evaluation, and improve insight extraction from simulation and observation datasets.

## Roadmap

🚧 **Not yet implemented.** This page describes the planned data-driven layer; nothing below is running in the dashboard yet.

| Capability | Purpose | Status |
|---|---|---|
| Surrogate modeling | Emulate SWAT+gwflow outputs for rapid scenario evaluation | Planned |
| Residual learning | Correct model errors, improve prediction accuracy | Planned |
| Spatiotemporal prediction | Capture flow and salinity dynamics | Planned |
| Feature importance analysis | Identify dominant hydrologic / water-quality drivers | Planned |
| Scenario risk classification | Predict threshold exceedance under alternative strategies | Planned |

## Why It Is Useful

Machine-learning methods can help when:

- Full process-based simulations are computationally expensive
- Many alternative scenarios must be screened quickly
- Model bias varies across stations or hydrologic regimes
- Complex nonlinear relationships are difficult to interpret directly

## Example Inputs and Outputs

Potential input variables include:

- Precipitation
- Temperature
- Upstream flow
- Release amount
- Release timing
- Basin and reach attributes
- Simulated states from SWAT+gwflow

Potential outputs include:

- Streamflow at selected stations
- Salinity or constituent concentrations
- Residual correction terms
- Threshold exceedance probabilities
- Fast scenario-response estimates

## Planned Dashboard Views

| View | Shows |
|---|---|
| ML workflow summary | Pipeline from SWAT+gwflow outputs to trained surrogate |
| Predictor importance | Which inputs drive flow / salinity predictions |
| Observed vs. simulated vs. corrected | Residual-learning improvement over raw SWAT+gwflow |
| Risk classification | Threshold-exceedance probability by scenario |
| Fast-response surrogate | Near-instant scenario screening without a full model run |

## Status

🚧 **Planned** — this page will populate once the reservoir and salinity modules are added to the calibrated SWAT+gwflow model (see the [Hydrology](/Hydrology) and [Scenarios](/Scenarios) pages), giving the surrogate model real scenario outputs to train on.