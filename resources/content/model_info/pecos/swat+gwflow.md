# Model Construction and Setup
## Study Area

The study area is the **Pecos River Basin**, which was selected to evaluate the hydrological impacts of purified produced water application under the Texas Produced Water Consortium (TxPWC) project. The overall objective is to identify the major hydrological and ecological processes during and after the release of purified produced water, including impacts on streamflow, ecosystems, and aquifer systems. 

The current Pecos River model domain includes:

- **Watershed area:** approximately 161,070 km²  
- **Subbasins:** 460  
- **HRUs:** 2,874  
- **Land use classes:** 13  
- **Soil classes:** 18

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/study_area.png?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/study_area.png?raw=true" width="500" style="cursor:zoom-in;"></a></p>

*Figure 1. Pecos River Basin study area and model domain. Tap / click to zoom.*

## SWAT+gwflow Model Construction

This project uses **SWAT+gwflow** as the primary integrated hydrologic modeling framework. SWAT+ provides a semi-distributed watershed-scale ecosystem model that simulates land-phase hydrologic processes, in-stream routing, nutrient transport, crop growth, and water management processes across long time periods using a daily time step. 

The SWAT+gwflow framework was selected because it supports:

- Integrated watershed hydrology  
- Explicit groundwater–surface water interaction  
- Solute transport and concentration tracking  
- Water availability and management scenario analysis  
- In-stream and land-application assessments 

In this project, the framework is used to simulate:

- Key hydrological and ecological processes  
- Fate and transport of released purified produced water  
- Spatial and temporal variability in watershed response  
- Potential impacts under alternative release strategies  

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/swat+gwflow_framework.png?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/swat+gwflow_framework.png?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Figure 2. SWAT+gwflow conceptual framework used in the Pecos River Basin. Tap / click to zoom.*

## Model Inputs and Configuration

The Pecos River Basin model was developed using datasets and workflows adapted from the **CoSWAT framework**. The model setup shown in the presentation includes the following main inputs: 

- **DEM:** ASTER Global DEM  
- **Land use:** ESA land cover data  
- **Soils:** FAO soil data  
- **Weather:** reanalysis forcing through the ISIMIP framework  

The development workflow shown in the presentation includes:

- Watershed delineation and preprocessing  
- Model setup using **QSWAT+**  
- Configuration and editing in the **SWAT+ Editor**  
- Model execution using **SWAT+ executable tools**  
- Preparation for server-based evaluation and dashboard integration

<p align="center"><a href="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/dataset.png?raw=true" target="_blank" rel="noopener"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/dataset.png?raw=true" width="1000" style="cursor:zoom-in;"></a></p>

*Figure 3. Pecos River model setup and preprocessing workflow. Tap / click to zoom.*

## Solute Transport and Produced Water Representation

A key advantage of the selected framework is its ability to represent **solute transport** together with coupled hydrologic processes. The presentation highlights tracking of multiple dissolved constituents and exchange across watershed, vadose zone, stream, and groundwater systems. 

This is important for the TxPWC project because treated produced water assessment requires analysis of:

- Mixing and transport after release  
- Groundwater–surface water exchange  
- In-stream transport processes  
- Land application and irrigation scenarios  
- Salinity and constituent response under different management conditions

🚧 **In development** — a conceptual diagram of coupled hydrologic and solute-transport processes is planned for this section.

## Parameterization and Calibration Uncertainty

The broader modeling workflow includes calibration, uncertainty analysis, and scenario evaluation using **pyEMU**, **FloPy**, and PEST++-based utilities. The presentation also references supporting workflows such as **swatp_pst_wf**, as well as scenario-based and optimization tools for uncertainty-aware decision support. 

The uncertainty and scenario-analysis framework is intended to support evaluation of:

- Surface discharge  
- Groundwater levels  
- Water quality responses  
- Scenario-based comparisons  
- Optimization of release strategies 

Relevant PEST++ tools mentioned in the presentation include:

- **PESTPP-MOU** for constrained multi-objective optimization  
- **PESTPP-SEN** for sensitivity analysis  
- **PESTPP-IES** for optimization under uncertainty  
- **PESTPP-SWP** for scenario analysis using predefined parameter or input sets 


## Current Development Status

The current dashboard-connected model information page is intended to summarize:

- Study area and model domain  
- SWAT+gwflow framework   
- Input datasets and configuration  
- Solute transport and water quality relevance  
- Calibration, uncertainty, and scenario-analysis approach  

Additional basin-specific and model-specific figures, parameter tables, and workflow diagrams can be added as the dashboard content continues to expand.

## Planned Manuscripts and Submission Timeline

- Assessing Hydrological Impacts of Purified Produced Water Reuse in the Pecos River Basin Using SWAT+ gwflow (target: August)
- Assessing Salinity Sources and Baseflow Constraints in the Pecos River Basin Using SWAT+ gwflow (target: December)
- Integrating Random Forest with SWAT+ gwflow for Predicting and Mapping River Salinity in the Pecos River Basin (target: December)