# Data-Driven Analysis

## Overview

A full physics-based run of SWAT+gwflow is expensive. When a stakeholder asks *"what if we released here instead, in August, at half the volume?"*, waiting on a complete simulation for every variation doesn't scale.

Machine learning is the shortcut — **not a replacement for SWAT+gwflow, but a fast approximation trained on it.** Learn from the runs already completed, then screen hundreds of alternatives in the time one full simulation would take, and send only the promising ones to the physical model.

## What's Planned

🚧 **Nothing on this page is running yet.** The cards below are the intended data-driven layer, built once the reservoir and salinity modules are in place.

## What It Would Learn From

**Inputs:** precipitation · temperature · upstream flow · release amount and timing · basin and reach attributes · simulated states from SWAT+gwflow

**Outputs:** streamflow at selected stations · salinity and constituent concentrations · residual corrections · threshold-exceedance probabilities

## Status

🚧 **Planned** — this page populates once the reservoir and salinity modules are added to the calibrated SWAT+gwflow model (see [Hydrology](/Hydrology) and [Scenarios](/Scenarios)), giving the surrogate real scenario output to train on.
