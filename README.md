# RadReirradiation 🧬

### Radiotherapy Re-irradiation Analysis and Biological Dose Summation in 3D Slicer

**RadReirradiation** utilizes the **Linear-Quadratic (LQ)** model to perform voxel-by-voxel calculations of Biologically Effective Dose (BED) and EQD2 (Equivalent Dose in 2 Gy fractions), enabling precise evaluation of the accumulated dose in critical structures and tumor volumes (DVH).

<img width="1919" height="701" alt="image" src="https://github.com/user-attachments/assets/8ca2476f-8099-419e-a42c-a3b2d6cb43af" />

## 🚀 What's New in Version 3.0 (Major Clinical Update)

Version 3.0 represents a massive structural and clinical refactoring, upgrading the core algorithm to a true voxel-based radiobiology engine and introducing full support for sequential boost treatments.

-  **Voxel-Based Radiobiology Engine:** Upgraded the core mathematical engine to calculate EQD2 and BED on a strict voxel-by-voxel basis.
- **Structure-Specific Parameters:** Alpha/beta (α/β) ratios and tissue recovery parameters can now be independently assigned per anatomical structure. Overlap conflicts between Target and OAR structures are automatically resolved using user-defined clinical priorities.
- **Sequential Boost Integration:** Full clinical support for sequential boost plans. The system features automated geometric resampling for boost volumes with a built-in fail-safe dose selector to prevent base/boost assignment errors.
- **Smart DICOM Loader:** The data import module now offers intelligent date-based automatic matching alongside a new "Manual Override" mode for complex datasets or single-day exports. It dynamically displays patient names and dates in the headers.
- **Clinical Workflow UI:** The user interface has been entirely reorganized into 4 sequential panels that strictly mirror the medical physics clinical workflow.
- **Advanced Clinical PDF Reports:** PDF generation dynamically extracts DICOM study dates, calculates the exact elapsed time between treatments, and seamlessly integrates sequential boost plan metrics for legal and clinical traceability.

## ✨ Key Features

- **Hybrid Image Registration:** Choose between fully automatic Rigid, Affine, and Deformable (B-Spline) registration workflows (powered by BRAINSFit) or highly precise Manual Alignment with 6 Degrees of Freedom (Translational & Rotational).
- **Auto-Resampling Dose Engine:** Automatically resamples the moving dose grids (both Base and Boost plans) to perfectly match the reference geometry, preventing matrix dimension errors.
- **Absolute & Relative DVH:** Toggle between Relative Volume (%) and Absolute Volume (cc) directly on the generated Dose-Volume Histogram.
- **"Eclipse-Style" Dose Wash:** Custom dynamic color map transition (Dark Blue to Red) with a 2 Gy threshold and 40% opacity that correctly overlays on the native CT background.
- **Automated TPS DICOM Export (Eclipse Ready):** Export your accumulated EQD2 dose directly back to commercial TPS environments. The algorithm traces the original DICOM metadata, generates a "shadow" RTPLAN, and bundles the original RTSTRUCT to ensure 100% compatibility upon import.

## 📚 Scientific Foundation and References
The development of RadReirradiation is based on international standards for reporting and accumulating biological doses.

### Reference Publication (RadReirradiation)
* **Status:** In Preparation. 
* *Note:* Once the specific scientific article for this tool is published, this section will be updated with a direct link to PubMed/the corresponding Journal.

### Background Literature and Consensus
This module formally implements the concepts discussed in the following key publications:
1. **ReCOG Consensus (2024):** *Reirradiation Collaborative Group (ReCOG) consensus on
standards for dose evaluation and reporting in patients with
multiple courses of radiation therapy:*. [https://pubmed.ncbi.nlm.nih.gov/41643699/]
2. **Nieder et al. (2017/2018):** Second re-irradiation: a narrative review of the available clinical data. [https://pubmed.ncbi.nlm.nih.gov/29187033/]
3. **Nieder et al. (2017/2018):** Repeat reirradiation of the spinal cord: multi-national expert treatment
recommendations*. [https://doi.org/10.1007/s00066-018-1266-6]

## 💻 Installation

### Option 1 — 3D Slicer Extensions Manager (Recommended)

RadReirradiation is officially available in the 
3D Slicer Extensions Manager.

1. Open **3D Slicer 5.12.3** or **Slicer Preview**
2. Go to **Extensions Manager** (top menu or Edit → 
   Extensions Manager)
3. Search for: `RadReirradiation`
4. Click **Install**
5. Restart 3D Slicer

> ⚠️ **Requirement:** [SlicerRT](https://slicerrt.github.io) 
> must be installed before RadReirradiation. 
> It provides full DICOM-RT file support (RT Dose, 
> RT Structure Set, RT Plan).

---

### Option 2 — Manual Installation (Development)

If you want to test the latest development version 
directly from this repository:

1. Clone or download this repository
2. Open 3D Slicer
3. Go to **Edit → Application Settings → Modules**
4. Under **Additional module paths**, click **Add**
5. Select the folder containing `RadReirradiation.py`
6. Click **OK** and restart 3D Slicer

---

> 💡 **Tip:** Option 1 is recommended for clinical use. 
> Option 2 is intended for developers and contributors 
> who want to test new features before an official release.

## 📹 Video Tutorial (v1.2)

A complete step-by-step tutorial is available on YouTube, 
covering the full reirradiation analysis workflow:

- Installation and DICOM RT data preparation
- Image registration (Rigid, Affine & Deformable)
- Auto-Center tool for CBCT field-of-view correction
- EQD2/BED biological dose accumulation (α/β = 3 and 10 Gy)
- DVH analysis and dosimetric metrics (Dmax, Dmean)

[![RadReirradiation Tutorial](https://img.youtube.com/vi/xFspmJT0Wr8/maxresdefault.jpg)](https://www.youtube.com/watch?v=xFspmJT0Wr8)

> 💡 **Tip:** You can switch between α/β = 3 Gy (OARs) and 
> α/β = 10 Gy (tumor) without repeating the image 
> registration — just change the parameter and click Calculate.

## Step-by-step tutorial (v3.0)🛠️


**1. Data Preparation: From TPS to 3D Slicer**

To perform an accurate re-irradiation analysis, you must export two complete datasets (in the same folder) from your Treatment Planning System (TPS): the Previous (1) Treatment and the Current/Planned Treatment (2).

<img width="679" height="266" alt="0" src="https://github.com/user-attachments/assets/4493ec9f-dac8-485c-b845-ac161f34d67d" />

Export Requirements (from your TPS):
- CT Images (CT)
- RT Doses (RD) *(Include Sequential Boost Doses if applicable)*
- RT Structure Sets (RS)
- RT Plan (RP)

<img width="1182" height="581" alt="1" src="https://github.com/user-attachments/assets/4051c8e3-1dba-4cd6-8d44-8b48f292e470" />

Succesfull exportation of the previous treatmet, repeat the same steps for the current/planned treatmet

<img width="1187" height="577" alt="2" src="https://github.com/user-attachments/assets/35867a76-7435-4e8c-b387-591fc5b4e4d0" />

**Importing into 3D Slicer:**

Ensure you have the SlicerRT extension installed. It is a mandatory requirement to read and process Radiotherapy DICOM files. Drag and drop your exported DICOM folders into the 3D Slicer application or use the native DICOM Browser and click on Examine button.

<img width="1202" height="772" alt="3" src="https://github.com/user-attachments/assets/c8e57085-13bf-4b7d-af89-d7e2dae9fa4e" />

Once the DICOM files are loaded only check the TAC, RD and RS of the previous and current treatmets, click on Load button. Is not necessary load the the RP plans (the algorithm extracts the number of fractions from RP Plans without the need to load them). 
<img width="1915" height="1006" alt="LOAD DATA" src="https://github.com/user-attachments/assets/f5d0f31f-3503-4d56-af19-47d86d661bb8" />
 
Crucial Steps: When the DICOM import window appears, ensure the "eye" icon next to your RT Structures is toggled ON (visible). If this icon is closed, the structures will not be loaded into the scene and the Biological Role and DVH cannot be evaluated.

**2. Launching RadReirradiation**

Once your DICOM data is properly imported and organized in 3D Slicer, it is time to load it into the Radreirradiation extension.

Launching the Module:

* Open the module dropdown menu (usually displaying "Welcome to Slicer").
* Navigate to Radiotherapy and select RadReirradiation.

<img width="892" height="792" alt="Launch radreirradiation" src="https://github.com/user-attachments/assets/ec05b60a-cbfc-47c1-ac00-4a78673e0f7f" />

**RadReirradiation**  has 4 important modules, which are:

1. Load Reirradiation data.
2. Image registration with Dose resample.
3. Structures visualization and Biolgical configurations and EQD2 calculation
4. EQD2 Metrics, DVH Analysis, PDF Report and Export Dicom.
     
<img width="709" height="414" alt="MODULOS" src="https://github.com/user-attachments/assets/16c53463-0b2f-40e5-925b-52c087180354" />

**2. Panel 1: Load Reirradiation Data**

Launch the **RadReirradiation** module. Use the **Load Data: Auto-match (by date)** button to automatically scan the DICOM database, identify the loaded patient, and assign the correct CTs, Doses, and RTSTRUCTs based on chronological order. 
- If multiple treatment dates are detected, a dialog will prompt you to select the dates to compare. 
- If your TPS exported the data on the exact same date, use the **Manual-match** button to bypass the strict date filter.
- **Sequential Boosts:** If either plan includes a boost, check the *Add Sequential Boost* box. A fail-safe mechanism ensures you manually assign the Base Dose and Boost Dose to prevent clinical swapping errors.
  
<img width="638" height="535" alt="LOAD DATA" src="https://github.com/user-attachments/assets/245f0880-b254-454f-8c92-274c16ab7b7d" />

While the **Auto-match (by date)** algorithm is designed to handle 95% of standard clinical workflows, the **Manual-match** mode acts as a critical fail-safe. It temporarily removes the strict DICOM chronological filters, allowing the medical physicist to freely assign any loaded volume to any specific role.

**When to use Manual-match:**
- **Auto-match Failure or Misassignment:** If the algorithm fails to group the CT, RTDOSE, and RTSTRUCT correctly due to missing, corrupted, or anonymized DICOM metadata (e.g., stripped `StudyDate` tags).
- **Same-Day Consolidations:** When the Treatment Planning System (TPS) exports both the historical dose and the current plan under the exact same date and timestamp, making chronological sorting impossible.
- **Complex Multi-Plan Scenarios:** When dealing with multiple sum plans, composite doses, or comparative evaluations where the user needs absolute, granular control over which specific dose matrix is assigned to RT1 (Previous) or RT2 (Current).
- **External Data Imports:** When importing imaging or dose matrices from third-party software (like synthetic CTs or external Monte Carlo dose engines) that do not conform to standard TPS DICOM hierarchy trees.
**Assigning Volumes:**
  
<img width="635" height="539" alt="manual load" src="https://github.com/user-attachments/assets/7939ab9b-5ee4-4270-b10c-4eb5137d95fd" />

In the Data Selection panel, carefully assign your loaded volumes to their corresponding roles:
* Moving CT / Previous CT: The historical anatomy that needs to be registered.
* RTDOSE Previous treatment.
* RTSTRUCT : Structures from the previous treatment
* Fixed CT / Current /planned CT: The anatomy where the final dose summation will be evaluated.
* RTDOSE Current/planned Treatment.
* RTSTRUCT : Structures from the current treatment

**Data Organization Tip for Manual-match:**
Since TPS exports often generate generic names (In this example, the RTDOSE files in both treatmets have the same name), it is highly recommended to rename your loaded volumes immediately (e.g., rename them to CT_Previous, CT_Current, Dose_Previous, Dose_Current). This will prevent confusion when assigning volumes in the RadReirradiation module.
<img width="1881" height="984" alt="6" src="https://github.com/user-attachments/assets/fe9bea1a-5ed5-43a5-8bde-c243d972ddac" />
<img width="1130" height="285" alt="7" src="https://github.com/user-attachments/assets/58de03d2-7cf9-46bb-9243-8ed392857d68" />

**3. Panel 2: Pre-Alignment, Image Registration and Dose Resample**

Before computing any biological dose, both CTs must be spatially aligned. Click the "Auto-Center CTs" button. This will automatically match the mathematical centers of both image sets, providing an excellent starting point.
At this point, if all the structres are visible it is recommended to hide the structures to better visualize the Pre-Aligment and image Registration results. To do this, use module 2 (Structures visualization), and press the "Hide all structures" button.

<img width="1797" height="918" alt="Autecenter2" src="https://github.com/user-attachments/assets/de742b8b-8095-44eb-a648-d5f61388c0ad" />

💡 Clinical Tip: To better guide your alignment, use Module 2 (Structures Visualization) to turn on the visibility of the current PTV or target volume. This provides a clear visual anchor, helping you focus the registration on the most critical clinical area.

<img width="1871" height="910" alt="prealigment2" src="https://github.com/user-attachments/assets/958d82dc-4938-4b37-9ac0-9a8a7d6e37a9" />

Use the translational sliders (Right/Left, Ant/Post, Sup/Inf) to manually fine-tune the alignment. Once the initial pre-alignment is set, you have two paths to finalize the registration:

**Path A: Auto-Registration (Recommended)**
Let the built-in BRAINSFit engine lock the previous CT onto the current anatomy. The module includes two checkable options to improve the algorithmic results:

**Enable Affine Transform:** Performs a linear transformation (translation, rotation, scaling, and shearing).

**Enable Deformable (B-Spline) Registration:** Performs a non-linear transformation that adapts to anatomical changes between the two scans (e.g., weight loss or tumor shrinkage).
      
* ⚠️ Warning: Please note that checking those options (Affine/Deformable), is computationally intensive. It may take several minutes to complete depending on your computer's hardware specifications, if you want a quick registration, do not click either of the two options.

**Path B: Advanced Manual Registration (6-DOF)**
If the automatic registration algorithms do not yield favorable results, or if you prefer full control over the fusion, you can perform a purely manual registration. Check the Use Manual Alignment Only (Disable Auto-Registration) box. Check Advanced: Enable Rotation to unlock the Pitch, Roll, and Yaw sliders. Manually align the images using the full 6 Degrees of Freedom (6-DOF).

<img width="1914" height="925" alt="performing registration2" src="https://github.com/user-attachments/assets/cf352de7-0767-4ddb-8f9f-14f30369fa89" />

⚠️ CRITICAL STEP: Whether you choose Path A or Path B, you must click the final action button at the bottom of the panel (Auto Registration and Dose Resample OR Apply Manual Alignment / Resample Dose). This step is mandatory. It not only locks the image fusion but also mathematically resamples the previous RTDOSE grid to match the current patient geometry, preventing matrix dimension errors during the biological summation.

**Visualizing the Fusion Results:**

After the registration is complete, it is highly recommended to perform a visual Quality Assurance (QA). Use Slicer's native foreground/background fade sliders (located at the top of the 2D slice views) to blend the Previous CT and Current CT. This visual check ensures the accuracy of the alignment before proceeding to the dose calculation.

<img width="1886" height="873" alt="registration succesfull" src="https://github.com/user-attachments/assets/efbce12f-1568-4fa5-a7a7-97b9d5ff63ac" />


**Structure Selection and Biological Role Assignment**

Once the image registration and dose resampling are complete, it is time to define the specific structures you want to evaluate for the re-irradiation summation.
Visualizing the Target Structures:
Navigate to Module 2 (Structures Visualization). You can choose to use either the Previous or the Current Structure Set (RTSTRUCT) from the dropdown menu. Expand the list and toggle the "eye" icon (visibility) ON only for the specific structures you wish to include in the dosimetric analysis (e.g., PTVs and critical OARs). The algorithm will solely process the structures that are visible in the scene.

<img width="1910" height="936" alt="biological role2" src="https://github.com/user-attachments/assets/c84ab529-6ec4-477d-8a0c-fd54de6e7c99" />

Configuring the Biological Roles:
After making your target structures visible, proceed to Panel 2.1 (Biological Configuration) and click the Generate / Update Biological Roles Table button. The module will automatically populate the table exclusively with your visible structures.

For each structure in the table, you must define two critical dosimetric parameters:

Role (Tumor vs. OAR): Assign whether the structure is a Target (Tumor) or an Organ At Risk (OAR). This dictates which specific Alpha/Beta (α/β) ratio the algorithm will apply to that volume during the voxel-by-voxel EQD2/BED conversion.

Overlap Priority: In clinical scenarios where a Target volume and an OAR overlap, you must dictate how those intersecting voxels are mathematically treated. You can choose whether the intersection behaves strictly as an OAR (conservative approach, prioritizing healthy tissue constraints) or as a Tumor (prioritizing target dose accumulation).


**3. Reirradiation Caulculation settings**

With the CT images already registered, the extension streamlines your workflow. Thanks to the image registration algorithm, the newly registered and mapped Previous RT Dose (RD PREVIOUS_Resampled) is automatically loaded in the module, saving you manual steps and reducing setup errors.

<img width="1814" height="925" alt="Reirradiation settings2" src="https://github.com/user-attachments/assets/3657c90e-b8ce-4fd7-ace2-676fd89fc131" />


**Reirradiation Settings:**

**Fractions:** Enter the number of delivered fractions for the previous treatment (RT1) and the planned fractions for the current treatment (RT2). (Note: If your RTDOSE was loaded with its corresponding RTPLAN, the module's DICOM tracker will automatically detect and populate these values for you).

**Dual Alpha/Beta (α/β) Ratios:** The module now supports simultaneous dual biological summations. Enter both the α/β Ratio (OARs) (e.g., 3.0 Gy) and the α/β Ratio (Tumor) (e.g., 10.0 Gy). The algorithm evaluates each voxel and applies the correct ratio perfectly respecting the Roles and Overlap Priorities defined in your Biological Configuration table. You no longer need to run separate calculations for targets and healthy tissues.

**Time-Discount Factor (Partial Recovery):** If you consider it necessary to apply a dose discount factor, enable the "Time-based Recovery" option. This feature accounts for the partial biological recovery of healthy tissues over time. Based on the selected elapsed time interval, the module applies a specific dose reduction factor to the previous treatment before the final summation (Note: These factors are based on *Nieder C, et al. Update of human spinal cord reirradiation tolerance based on additional data from 38 patients and provide a realistic biological estimation*):

0 to 6 months: No recovery assumed. 0% discount is applied (100% of the previous dose is considered).

6 to 12 months: Partial recovery assumed. A 25% discount factor is applied (75% of the previous dose is considered).

12 to 24 months: Advanced recovery assumed. A 50% discount factor is applied (50% of the previous dose is considered).

> 24 months: Prolonged recovery assumed. A 65% discount factor is applied (35% of the previous dose is considered).

Click the Calculate Cumulative EQD2 Dose button.

<img width="1911" height="928" alt="calculating EQD2 2" src="https://github.com/user-attachments/assets/6f2e51f0-cfe1-4fe4-a4f3-c6b7110a1138" />

<img width="1911" height="925" alt="calculating EQD2 FINAL" src="https://github.com/user-attachments/assets/610fa803-4211-444e-aab0-52f3f51ff079" />

**4 Visualizing the Results and DVH Analytics:**

Once the cumulative EQD2 dose is calculated, you can instantly extract the dosimetric data for the structures you previously selected in the Biological Roles table.

**Configurable DMax and Metrics Table:**

<img width="1917" height="931" alt="DVH Y METRICAS" src="https://github.com/user-attachments/assets/c905dfb5-65a7-47f4-a2db-b22e41edc4f3" />

Adjustable DMax Volume Constraint: Before calculating the metrics, you can specify the exact volume used to evaluate the Maximum Dose (DMax). Depending on your clinical protocol or the specific organ evaluated (e.g., spinal cord vs. bowel), you can select a true point dose (0 cc), a near-maximum dose (0.03 cc), or larger volumetric constraints (1 cc, 2 cc, up to 5 cc). Calculate Metrics: Click the calculate button to generate a detailed table displaying the Cumulative DMax and Cumulative Mean Dose (DMean) exclusively for the structures actively participating in your biological analysis.

**Dose-Volume Histogram (DVH) Generation:**
<img width="1918" height="932" alt="SOLO DVH" src="https://github.com/user-attachments/assets/3917eca8-0440-4db5-9959-956feaee0fa3" />

To visually analyze the dose distribution, click the Generate DVH button. The module will plot interactive DVH curves for the accumulated EQD2 dose.
Absolute vs. Relative Volume Toggle: You can easily switch the DVH Y-axis between Relative Volume (%) and Absolute Volume (cc). The algorithm extracts precise voxel spacing dimensions directly from the DICOM metadata, ensuring highly accurate volumetric rendering for your clinical constraints.


**5 Exporting Data and Clinical Reporting**

Once your metrics and DVH are generated and clinically validated, you can securely export the accumulated dose and analysis for your medical records and Treatment Planning System (TPS).

**Export EQD2 to DICOM:** Click the green button to package the accumulated EQD2 dose for direct import into your TPS (e.g., Varian Eclipse, Monaco). The module utilizes "Silent DICOM Tracking" to trace original metadata, generates a compatible "shadow" RTPLAN, and bundles the active RTSTRUCT. This ensures seamless import compatibility and bypasses standard TPS dose-lock restrictions.

**Export Clinical Report (PDF):** Click the red button to generate a native, print-ready PDF document. This feature automatically traverses the DICOM hierarchy to extract patient metadata (Name, ID) and compiles a comprehensive document logging all registration parameters, biological roles, tissue recovery settings, and the final dosimetric metrics (DMax, DMean) for your legal and medical traceability.


## Disclaimer ⚠️
**This software is for research and educational purposes only and has not been cleared for clinical use by any regulatory body (FDA, CE, etc.).**
The user assumes all responsibility for the interpretation and clinical application of the results provided by this tool. Calculations must be independently verified by a certified Medical Physicist or Radiation Oncologist before any clinical decision.

**Autor:** Luis Paredes, Clinical Medical Physicist (Cali, Colombia), [www.linkedin.com/in/lfparedes1].

**Web version:** [radcomp.streamlit.app](https://radcomp.streamlit.app)
