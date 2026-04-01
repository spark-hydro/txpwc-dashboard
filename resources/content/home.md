# TxPWC Dashboard
## Project Overview
The Texas Produced Water Consortium (TxPWC) was established by SB601 (2021) to evaluate the technical and economic feasibility of beneficial reuse of treated produced water in Texas.

The consortium is led by Texas Tech University and brings together a diverse group of stakeholders, including:

### Texas Tech Research Team
<p align="center"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/research_team.png?raw=true" width="1000"></p>

### Active and diverse stakeholder membership
<p align="center"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/members_enhanced.png?raw=true" width="1000"></p>

- Agriculture and landowners  
- Oil and gas (upstream and midstream)  
- Environmental organizations  
- Government agencies  
- Consulting and industry partners  

### Legislative reports:

- [2022 Report](https://www.depts.ttu.edu/research/tx-water-consortium/2022-report.php)  
- [2024 Report](https://www.depts.ttu.edu/research/tx-water-consortium/TXPWCFINALDRAFT.pdf)  

---

## Why This Matters

Texas faces increasing water demand and supply challenges:

- **Statewide demand (2020 - 2030):** ~18 million acre-feet/year  
- **Projected additional needs:**
  - 4.8 million acre-feet/year by 2030  
  - 6.9 million acre-feet/year by 2070  

This growing gap highlights the need for alternative water resources, including treated produced water.

---

## Project Objective

The goal of this project is to understand hydrological and ecological impacts of releasing treated produced water into river systems.

Key objectives:

- Simulate watershed-scale hydrological processes  
- Track transport and fate of released water  
- Evaluate impacts on streamflow, groundwater, and ecosystems  
- Capture spatial and temporal variability  
- Support safe and informed water reuse decisions  

---

### Dashboard Purpose

This dashboard provides an interactive platform to explore model results and data for the TxPWC project.

It integrates:
- Observed data (e.g., USGS streamflow)  
- Simulated outputs (e.g., SWAT+ / SWAT+ gwflow)  
- Spatial datasets (subbasins, stations, release points)
- Scenario-based model outputs  

---

### How to Use this Dashboard

Use the **Analysis Settings** in the sidebar to control:

- Basin  
- Model type  
- Scenario  

These selections dynamically update all analysis pages.

---

## Pages Overview

### Model Info

- Model structure and components  
- Input datasets and preprocessing  
- Calibration approach and parameters  

### Model Performance

- Comparison of observed vs simulated data  
- Performance metrics (e.g., NSE, RMSE)  
- Spatial visualization by subbasin  

### Hydrology

- Historical streamflow and climate data  
- Hydrologic trends and variability  

### Water Quality

- Salinity and key water quality indicators  
- Transport and mixing behavior  

### Scenarios

- Produced water release configurations  
- Spatial distribution of release points  
- Scenario-based model outputs  


### Data-Driven Analysis (Machine Learning)

- Surrogate modeling to emulate SWAT+gwflow outputs for rapid scenario evaluation and interactive analysis
- Residual learning to correct model errors and improve accuracy without modifying the physical model
- Spatiotemporal prediction to capture flow and salinity dynamics under varying climate and release conditions
- Feature importance analysis to identify key drivers of hydrologic and water quality responses
-  Scenario risk classification to predict threshold exceedance and assess risk under different release strategies

---


## Dashboard Code Pipeline

The system follows a data-driven pipeline:
<p align="center"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/txpwc_code_pipeline.png?raw=true" width="1000"></p>

*Figure 2. Maps of simulation results from the steady-state MODFLOW model* 

### 1. Data ingestion

- Observed data (CSV)  
- Simulated outputs (Parquet)  

### 2. Data processing  

- Station matching  
- Variable selection  
- Time-series alignment  

### 3. Visualization  

- Interactive maps (subbasins, stations)  
- Time-series plots  
- Performance metrics  

