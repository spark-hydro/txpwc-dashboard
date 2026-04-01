# 1. Model Construction and Setup
## 1.1 Study Area
## 1.2 APEX model

[Google](https://www.google.com)
The APEX model has been developed and tested by #jjeong  and #tabitew . The model is currently being optimized by testing with various forcing data and statistic results. 
## 1.3 MODFLOW model

An Animas MODFLOW model has been created and linked with its APEX model. More detailed description is as follows and see Figure 1.
- Grid size: 1 by 1 km
-	Boundary: Subbasin boundary from the APEX model
-	Land surface elevation: DEM from the APEX model
	-	v1 used fitted surface interpolation
	-	v2 used point average interpolation 09/04/20
-	Bedrock elevation (Figure 1.a):
	- [Shangguan et al., 2017](http://globalchange.bnu.edu.cn/research/dtb.jsp) developed a global depth to bedrock (DTB) dataset for use in Earth System Models and other applications as well.
	-	We used a 30-seconds (~ 1km) resolution of the map according to the MODFLOW construction setting (based on the size of grid cell)
	-	Spatial variation and resolution difference might increase the uncertainty of the unconfined aquifer thickness (further research).
-	Hydraulic Conductivity and Specific Yield (Figure 1.b):
	-	Huscroft et al., 2018 (https://dataverse.scholarsportal.info/dataset.xhtml?persistentId=doi:10.5683/SP2/TTJNIU) compiled and mapped global permeability of the unconsolidated and consolidated Earth. We used a variable "Near surface global permeability values (logarithmic permeability)" and convert them to Hydraulic Conductivity values (m2/day).
-	River package (Figure 1.c):
	-	A MODFLOW river package has been created using the river network information of the APEX model to provide "river stage", "riverbed conductance" and "riverbed bottom elevation" for each river grid cell. Riverbed thickness and conductance were set to 0.1, respectively and these variables were parameterized.
<br>
<p align="center"><img src="https://github.com/spark-brc/crb_apexmf/blob/main/resources/watershed/Animas (calibrated)/description/ani_model_inputs.png?raw=true" width="1000"></p>
*Figure 1. Maps of inputs for a steady-state MODFLOW model, Hydraulic Conductivity, Specific Yield, Riverbed Conductance and Riverbed thickness variables will be parameterized in an APEX-MODFLOW model.*

### 1.3.1 Steady-State MODFLOW Results
Results from a steady-state MODFLOW simulation can provide insights for evaluating the model construction and initial model inputs (parameters, initial hydraulic heads) to a transient APEX-MODFLOW model.
<br>
<p align="center">
<img src="https://github.com/spark-brc/crb_apexmf/blob/main/resources/watershed/Animas (calibrated)/description/ani_ssmf_results.png?raw=true" width="1000">
</p>
*Figure 2. Maps of simulation results from the steady-state MODFLOW model* 

## 1.4. APEX-MODFLOW model 
### 1.4.1 Linking APEX with MODFLOW
We used APEXMOD(https://github.com/spark-brc/APEXMOD), a QGIS-based graphical user interface for application and assessment of APEX-MODFLOW models (see Section 2).
### 1.4.2 Preliminary Result
Figure shows hydrographs for monthly average stream discharges at subbasins 57, 72, and 75 (outlet of watershed). The Animas APEX-MODFLOW model generally overestimated peak flows and underestimated baseflows. The model performance can be improved by adjusting APEX and MODFLOW parameters.
![](/resources/watershed/Animas/description/ani_precali.png)
# 2 Parameterization
Based on geological dataset used for building the steady-state MODFLOW model and locations of stream gages, a zonal approach (zonation), also called spatial differentiated calibration, can be applied to the optimization process of the Animas APEX-MODFLOW model.
-	MODFOW (5 zones):
	-	5 Hydraulic Conductivities
	-	5 Specific Yields
	-	1 Riverbed Conductance
	-	1 Riverbed thickness
-	APEX (Get high sensitive parameters from APEX sensitivity analysis)
	-	
We will use a parameter estimation tool called PEST developed by John Doherty and Watermark Numerical Computing organization. PEST is a model independent tool for optimizing the model. It requires pre- and post-processing to run PEST. Several Python scripts, Pyemu library developed by White et al 2018, BeoPEST for parallel optimization process, will be used to complete the auto calibration workflow.
