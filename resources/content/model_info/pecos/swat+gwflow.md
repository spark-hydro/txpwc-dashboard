# 1. Model Construction and Setup

## 1.1 Study Area

The study area is the **Pecos River Basin**, which was selected to evaluate the hydrological impacts of purified produced water application under the Texas Produced Water Consortium (TxPWC) project. The overall objective is to identify the major hydrological and ecological processes during and after the release of purified produced water, including impacts on streamflow, ecosystems, and aquifer systems. :contentReference[oaicite:1]{index=1}

The current Pecos River model domain includes:

- **Watershed area:** approximately 161,070 km²  
- **Subbasins:** 460  
- **HRUs:** 2,874  
- **Land use classes:** 13  
- **Soil classes:** 18  :contentReference[oaicite:2]{index=2}

<!-- Placeholder: Pecos study area map -->
<p align="center"><img src="https://github.com/spark-hydro/txpwc-dashboard/blob/main/resources/content/images/study_area.png?raw=true" width="1000"></p>

*Figure 1. Placeholder for the Pecos River Basin study area and model domain.*

## 1.2 SWAT+gwflow Model

This project uses **SWAT+gwflow** as the primary integrated hydrologic modeling framework. SWAT+ provides a semi-distributed watershed-scale ecosystem model that simulates land-phase hydrologic processes, in-stream routing, nutrient transport, crop growth, and water management processes across long time periods using a daily time step. :contentReference[oaicite:3]{index=3}

The SWAT+gwflow framework was selected because it supports:

- Integrated watershed hydrology  
- Explicit groundwater–surface water interaction  
- Solute transport and concentration tracking  
- Water availability and management scenario analysis  
- In-stream and land-application assessments  :contentReference[oaicite:4]{index=4}

In this project, the framework is used to simulate:

- Key hydrological and ecological processes  
- Fate and transport of released purified produced water  
- Spatial and temporal variability in watershed response  
- Potential impacts under alternative release strategies  :contentReference[oaicite:5]{index=5}

<!-- Placeholder: SWAT+gwflow conceptual figure -->
![SWAT+gwflow conceptual framework](images/swat_gwflow_concept_placeholder.png)

*Figure 2. Placeholder for the SWAT+gwflow conceptual framework used in the Pecos River Basin.*

## 1.3 Model Inputs and Configuration

The Pecos River Basin model was developed using datasets and workflows adapted from the **CoSWAT framework**. The model setup shown in the presentation includes the following main inputs: :contentReference[oaicite:6]{index=6}

- **DEM:** ASTER Global DEM  
- **Land use:** ESA land cover data  
- **Soils:** FAO soil data  
- **Weather:** reanalysis forcing through the ISIMIP framework  :contentReference[oaicite:7]{index=7}

The development workflow shown in the presentation includes:

- Watershed delineation and preprocessing  
- Model setup using **QSWAT+**  
- Configuration and editing in the **SWAT+ Editor**  
- Model execution using **SWAT+ executable tools**  
- Preparation for server-based evaluation and dashboard integration  :contentReference[oaicite:8]{index=8}

<!-- Placeholder: model setup workflow -->
![Model setup workflow](images/model_setup_workflow_placeholder.png)

*Figure 3. Placeholder for the Pecos River model setup and preprocessing workflow.*

## 1.4 Solute Transport and Produced Water Representation

A key advantage of the selected framework is its ability to represent **solute transport** together with coupled hydrologic processes. The presentation highlights tracking of multiple dissolved constituents and exchange across watershed, vadose zone, stream, and groundwater systems. :contentReference[oaicite:9]{index=9}

This is important for the TxPWC project because treated produced water assessment requires analysis of:

- Mixing and transport after release  
- Groundwater–surface water exchange  
- In-stream transport processes  
- Land application and irrigation scenarios  
- Salinity and constituent response under different management conditions  :contentReference[oaicite:10]{index=10}

<!-- Placeholder: solute transport schematic -->
![Solute transport schematic](images/solute_transport_placeholder.png)

*Figure 4. Placeholder for a conceptual diagram of coupled hydrologic and solute transport processes.*

## 1.5 Calibration, Uncertainty, and Scenario Analysis

The broader modeling workflow includes calibration, uncertainty analysis, and scenario evaluation using **pyEMU**, **FloPy**, and PEST++-based utilities. The presentation also references supporting workflows such as **swatp_pst_wf**, as well as scenario-based and optimization tools for uncertainty-aware decision support. :contentReference[oaicite:11]{index=11}

The uncertainty and scenario-analysis framework is intended to support evaluation of:

- Surface discharge  
- Groundwater levels  
- Water quality responses  
- Scenario-based comparisons  
- Optimization of release strategies  :contentReference[oaicite:12]{index=12}

Relevant PEST++ tools mentioned in the presentation include:

- **PESTPP-MOU** for constrained multi-objective optimization  
- **PESTPP-SEN** for sensitivity analysis  
- **PESTPP-IES** for optimization under uncertainty  
- **PESTPP-SWP** for scenario analysis using predefined parameter or input sets  :contentReference[oaicite:13]{index=13}

## 1.6 Produced Water Application Scenarios

The Pecos River case study is being used to evaluate real and potential produced water reuse scenarios. The presentation highlights both:

- **In-stream application scenarios**  
- **Land application (irrigation) scenarios**  :contentReference[oaicite:14]{index=14}

It also references example release capacities associated with candidate applications, indicating the model is intended to support comparison of baseline, scenario, and optimized release strategies. :contentReference[oaicite:15]{index=15}

<!-- Placeholder: scenario map -->
![Produced water application scenarios](images/scenario_map_placeholder.png)

*Figure 5. Placeholder for produced water release locations and scenario configurations.*

## 1.7 Current Development Status

The current dashboard-connected model information page is intended to summarize:

- Study area and model domain  
- SWAT+gwflow framework and rationale  
- Input datasets and configuration  
- Solute transport and water quality relevance  
- Calibration, uncertainty, and scenario-analysis approach  

Additional basin-specific and model-specific figures, parameter tables, and workflow diagrams can be added as the dashboard content continues to expand.