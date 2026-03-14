# SlicerRadComp 🧬

A clinical tool for 3D Slicer that calculates biologically effective dose (BED) and equivalent dose in 2 Gy fractions (EQD2) for radiotherapy plan accumulation and reirradiation analysis. 

This module performs voxel-by-voxel mathematical operations to biologically sum multiple radiation courses, applying time-based recovery factors, and returns a fully integrated EQD2 volume for clinical analysis (DVH).

Companion web application: [RadComp on Streamlit](https://radcomp.streamlit.app)

## Features 🚀
* **Voxel-by-Voxel processing:** Operates directly on DICOM RTDOSE arrays using NumPy for high-performance biological conversion.
* **Simultaneous Integrated Boost (SIB) support:** Automatically respects varying dose-per-fraction gradients within the same volume.
* **Time-Based Recovery Factor:** Applies partial biological recovery discounts to the base plan based on the interval between treatments.
* **Automated Visuals:** Instantly generates a clinical color wash overlay (Rainbow palette) with customizable transparency and a dynamic Scalar Bar.
* **Seamless SlicerRT Integration:** Output volumes are directly compatible with SlicerRT's Dose Volume Histogram (DVH) module.

## Installation 🛠️
1. Download or clone this repository to your local machine.
2. Open 3D Slicer.
3. Go to **Edit -> Application Settings -> Modules**.
4. Click the `>>` button next to "Additional module paths" and Add the `SlicerRadComp` folder.
5. Restart 3D Slicer. The module will now appear under the **Radiotherapy** category.

## Disclaimer ⚠️
**This software is for research and educational purposes only and has not been cleared for clinical use by any regulatory body (FDA, CE, etc.).**
The user assumes all responsibility for the interpretation and clinical application of the results provided by this tool. Calculations must be independently verified by a certified Medical Physicist or Radiation Oncologist before any clinical decision.
