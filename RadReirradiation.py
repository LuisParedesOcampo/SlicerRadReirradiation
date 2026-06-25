import logging
import os
import vtk
import ctk
import qt
import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin


# ==========================================================
# 1. METADATOS DEL MÓDULO
# ==========================================================
class RadReirradiation(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "RadReirradiation: Radiotherapy Reirradiation Analysis"
        self.parent.categories = ["Radiotherapy"]
        self.parent.dependencies = []
        self.parent.contributors = [
            "Luis Paredes, Clinical Medical Physicist (Cali, Colombia) www.linkedin.com/in/lfparedes1"]
        self.parent.helpText = """
        This module allows for re-irradiation analysis through EQD2 dose calculation, study alignment, and integrated dosimetric metrics.
        Visit: https://RadComp.streamlit.app .
        """
        self.parent.acknowledgementText = "Developed for the Medical Physics community."


# ==========================================================
# 2. INTERFAZ GRÁFICA (WIDGET / GUI)
# ==========================================================
class RadReirradiationWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = RadReirradiationLogic()

        # =========================================================================================================
        # PANEL 1: IMAGE REGISTRATION
        # ==========================================================================================================
        registrationCollapsibleButton = ctk.ctkCollapsibleButton()
        registrationCollapsibleButton.text = "1: Load Reirradiation Data"
        registrationCollapsibleButton.collapsed = False  # Que inicie abierto
        self.layout.addWidget(registrationCollapsibleButton)

        # Layout principal del panel
        registrationFormLayout = qt.QFormLayout(registrationCollapsibleButton)

        # =======================================================
        # GRUPO 1: DATOS PREVIOS (MÓVILES)
        # =======================================================
        rt1_groupBox = qt.QGroupBox("RT1: Previous Treatment (Moving)")
        rt1_groupBox.setStyleSheet("QGroupBox { font-weight: bold; }")
        rt1_layout = qt.QFormLayout(rt1_groupBox)

        # Selector: CT RT1 Tratamiento Móvil (Antiguo)
        self.moving_ct_selector = slicer.qMRMLNodeComboBox()
        self.moving_ct_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.moving_ct_selector.setMRMLScene(slicer.mrmlScene)
        self.moving_ct_selector.setToolTip("CT from the previous treatment RT1 (Moving).")
        rt1_layout.addRow("CT Volume: ", self.moving_ct_selector)

        # Selector: Dosis Antigua (A remuestrear)
        self.moving_dose_selector = slicer.qMRMLNodeComboBox()
        self.moving_dose_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.moving_dose_selector.showChildNodeTypes = True  # Vital para ver RTDOSE
        self.moving_dose_selector.setMRMLScene(slicer.mrmlScene)
        self.moving_dose_selector.setToolTip(
            "The Dose (RD) from the previous treatment RT1 that you want to align to the new grid.")
        rt1_layout.addRow("Dose (RTDOSE): ", self.moving_dose_selector)

        # Selector para las estructuras del TAC móvil (Prev)
        self.moving_rtstruct_selector = slicer.qMRMLNodeComboBox()
        self.moving_rtstruct_selector.nodeTypes = ["vtkMRMLSegmentationNode"]
        self.moving_rtstruct_selector.selectNodeUponCreation = False
        self.moving_rtstruct_selector.addEnabled = False
        self.moving_rtstruct_selector.removeEnabled = False
        self.moving_rtstruct_selector.noneEnabled = True
        self.moving_rtstruct_selector.setMRMLScene(slicer.mrmlScene)
        self.moving_rtstruct_selector.setToolTip("Selecciona las estructuras asociadas al TAC móvil previo")
        rt1_layout.addRow("Structures (RTSTRUCT): ", self.moving_rtstruct_selector)

        # Añadimos el Grupo 1 completo al layout principal
        registrationFormLayout.addRow(rt1_groupBox)

        # =======================================================
        # GRUPO 2: DATOS ACTUALES (FIJOS)
        # =======================================================
        rt2_groupBox = qt.QGroupBox("RT2: Current Plan (Fixed)")
        rt2_groupBox.setStyleSheet("QGroupBox { font-weight: bold; }")
        rt2_layout = qt.QFormLayout(rt2_groupBox)

        # Selector: CT RT2 tratamiento Fijo (Nuevo)
        self.fixed_ct_selector = slicer.qMRMLNodeComboBox()
        self.fixed_ct_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.fixed_ct_selector.setMRMLScene(slicer.mrmlScene)
        self.fixed_ct_selector.setToolTip("CT from the planned treatment RT2 (Fixed).")
        rt2_layout.addRow("CT Volume: ", self.fixed_ct_selector)

        # Selector: Dosis Nueva (Para usar su cuadrícula como molde)
        self.fixed_dose_selector = slicer.qMRMLNodeComboBox()
        self.fixed_dose_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.fixed_dose_selector.showChildNodeTypes = True
        self.fixed_dose_selector.setMRMLScene(slicer.mrmlScene)
        self.fixed_dose_selector.setToolTip(
            "The Dosage of the NEW plan. Its geometric matrix will be used as a template.")
        rt2_layout.addRow("Dose (RTDOSE): ", self.fixed_dose_selector)

        # Selector de seguridad para las estructuras del TAC fijo (Current)
        self.fixed_rtstruct_selector = slicer.qMRMLNodeComboBox()
        self.fixed_rtstruct_selector.nodeTypes = ["vtkMRMLSegmentationNode"]
        self.fixed_rtstruct_selector.selectNodeUponCreation = False
        self.fixed_rtstruct_selector.addEnabled = False
        self.fixed_rtstruct_selector.removeEnabled = False
        self.fixed_rtstruct_selector.noneEnabled = True
        self.fixed_rtstruct_selector.setMRMLScene(slicer.mrmlScene)
        self.fixed_rtstruct_selector.setToolTip("Selecciona las estructuras asociadas al TAC fijo actual")
        rt2_layout.addRow("Structures (RTSTRUCT): ", self.fixed_rtstruct_selector)

        # Añadimos el Grupo 2 completo al layout principal
        registrationFormLayout.addRow(rt2_groupBox)

        # =======================================================
        # CONEXIONES DE SEÑALES
        # =======================================================
        self.fixed_rtstruct_selector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateVisualizationSelector)
        self.moving_rtstruct_selector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateVisualizationSelector)

        # --- NUEVO: Panel Seguro de Pre-Alineación Manual ---
        self.preAlignCollapsibleButton = ctk.ctkCollapsibleButton()
        self.preAlignCollapsibleButton.text = "1.2: Pre-Alignment, Image Registration and Dose resample "
        registrationFormLayout.addRow(self.preAlignCollapsibleButton)
        preAlignLayout = qt.QFormLayout(self.preAlignCollapsibleButton)

        # Botón de teletransporte
        self.centerButton = qt.QPushButton("Auto-Center CTs")
        self.centerButton.toolTip = "Teleports the Moving CT to the Fixed CT center before manual adjustment."
        self.centerButton.setStyleSheet("background-color: #0078D7; color: white; font-weight: bold; padding: 5px;")
        preAlignLayout.addRow(self.centerButton)

        # Sliders (barras deslizadoras)
        self.sliderX = ctk.ctkSliderWidget()
        self.sliderX.minimum, self.sliderX.maximum, self.sliderX.value = -300, 300, 0
        self.sliderX.suffix = " mm"
        self.sliderX.enabled = False
        preAlignLayout.addRow("Right/Left (X):", self.sliderX)

        self.sliderY = ctk.ctkSliderWidget()
        self.sliderY.minimum, self.sliderY.maximum, self.sliderY.value = -300, 300, 0
        self.sliderY.suffix = " mm"
        self.sliderY.enabled = False
        preAlignLayout.addRow("Ant/Post (Y):", self.sliderY)

        self.sliderZ = ctk.ctkSliderWidget()
        self.sliderZ.minimum, self.sliderZ.maximum, self.sliderZ.value = -400, 400, 0
        self.sliderZ.suffix = " mm"
        self.sliderZ.enabled = False
        preAlignLayout.addRow("Sup/Inf (Z):", self.sliderZ)

        # Variables de control
        self.manual_transform_node = None
        self.base_translation = [0.0, 0.0, 0.0]

        # --- NUEVO: Control Manual Exclusivo y Rotación Avanzada ---

        # 1. Casilla para Forzar Solo Alineación Manual (Manual Override)
        self.manual_only_checkbox = qt.QCheckBox("Use Manual Alignment Only (Disable Auto-Registration)")
        self.manual_only_checkbox.setChecked(False)
        self.manual_only_checkbox.setToolTip(
            "If checked, the algorithm will be bypassed, and only dose resampling will be applied using your manual alignment.")
        self.manual_only_checkbox.setStyleSheet(
            "font-weight: bold; color: #d35400;")  # Color naranja para advertencia visual
        preAlignLayout.addRow(self.manual_only_checkbox)

        # 2. Casilla de Revelación Progresiva para Rotación
        self.advanced_rotation_checkbox = qt.QCheckBox("Advanced: Enable Rotation")
        self.advanced_rotation_checkbox.setChecked(False)
        self.advanced_rotation_checkbox.setEnabled(False)
        preAlignLayout.addRow(self.advanced_rotation_checkbox)

        # 3. Sliders de Rotación (Nacen ocultos usando .hide())
        self.sliderPitch = ctk.ctkSliderWidget()
        self.sliderPitch.minimum, self.sliderPitch.maximum, self.sliderPitch.value = -180, 180, 0
        self.sliderPitch.suffix = " °"
        self.sliderPitch.enabled = False
        self.sliderPitch.hide()
        preAlignLayout.addRow("Pitch (X-axis):", self.sliderPitch)

        self.sliderRoll = ctk.ctkSliderWidget()
        self.sliderRoll.minimum, self.sliderRoll.maximum, self.sliderRoll.value = -180, 180, 0
        self.sliderRoll.suffix = " °"
        self.sliderRoll.enabled = False
        self.sliderRoll.hide()
        preAlignLayout.addRow("Roll (Y-axis):", self.sliderRoll)

        self.sliderYaw = ctk.ctkSliderWidget()
        self.sliderYaw.minimum, self.sliderYaw.maximum, self.sliderYaw.value = -180, 180, 0
        self.sliderYaw.suffix = " °"
        self.sliderYaw.enabled = False
        self.sliderYaw.hide()
        preAlignLayout.addRow("Yaw (Z-axis):", self.sliderYaw)

        # Conectar los botones y barras a las funciones
        self.centerButton.connect('clicked(bool)', self.onCenterButtonClicked)
        self.sliderX.connect('valueChanged(double)', self.onSliderValueChanged)
        self.sliderY.connect('valueChanged(double)', self.onSliderValueChanged)
        self.sliderZ.connect('valueChanged(double)', self.onSliderValueChanged)

        self.sliderPitch.connect('valueChanged(double)', self.onSliderValueChanged)
        self.sliderRoll.connect('valueChanged(double)', self.onSliderValueChanged)
        self.sliderYaw.connect('valueChanged(double)', self.onSliderValueChanged)

        # Conectar las nuevas casillas a la lógica de la interfaz
        self.advanced_rotation_checkbox.connect('toggled(bool)', self.onAdvancedRotationToggled)
        self.manual_only_checkbox.connect('toggled(bool)', self.onManualOnlyToggled)

        # Casilla para Registro Afín (Escala y Cizalladura)
        self.affine_checkbox = qt.QCheckBox("Enable Affine Transform (Slower, high RAM)")
        self.affine_checkbox.setChecked(False)
        self.affine_checkbox.setToolTip(
            "It adds 12 degrees of freedom. Ideal for skull or calibration differences between CTs, but it requires a lot of RAM.")
        registrationFormLayout.addRow(self.affine_checkbox)

        # Casilla para Registro Deformable
        self.deformable_checkbox = qt.QCheckBox(
            "Enable Deformable (B-Spline) Registration, It will take several minutes..")
        self.deformable_checkbox.setChecked(False)
        self.deformable_checkbox.setToolTip(
            "First calculate Rigid, then apply Deformable. This may take several minutes.")
        registrationFormLayout.addRow(self.deformable_checkbox)

        # Botón Azul de Registro
        self.registerButton = qt.QPushButton("Auto-Registration and Dose Resample")
        self.registerButton.toolTip = "It performs an automatic hard registration and adjusts the dose grid.."
        self.registerButton.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        registrationFormLayout.addRow(self.registerButton)

        # Connect Register button to function
        self.registerButton.connect('clicked(bool)', self.onRegisterButton)

        # ===========================================================================================================
        # PANEL 2: ESTRUCTURAS Y VISUALIZACIÓN
        # ===========================================================================================================
        structuresCollapsibleButton = ctk.ctkCollapsibleButton()
        structuresCollapsibleButton.text = "2: Structures & Visualization"
        self.layout.addWidget(structuresCollapsibleButton)
        structuresFormLayout = qt.QFormLayout(structuresCollapsibleButton)

        # 1. Selector del RTSTRUCT (Nodos de Segmentación)
        self.rtstruct_selector = slicer.qMRMLNodeComboBox()
        self.rtstruct_selector.nodeTypes = ["vtkMRMLSegmentationNode"]  # Filtra solo RTSTRUCTs
        self.rtstruct_selector.selectNodeUponCreation = True
        self.rtstruct_selector.addEnabled = False
        self.rtstruct_selector.removeEnabled = False
        self.rtstruct_selector.noneEnabled = True
        self.rtstruct_selector.showHidden = False
        self.rtstruct_selector.showChildNodeTypes = False
        self.rtstruct_selector.setMRMLScene(slicer.mrmlScene)
        self.rtstruct_selector.setToolTip("Selecciona el conjunto de estructuras (RTSTRUCT) a visualizar.")

        # =======================================================
        # MAGIA DE FILTRADO: Exigir la etiqueta de RadReirradiation
        # =======================================================
        self.rtstruct_selector.addAttribute("vtkMRMLSegmentationNode", "RadReirradiationUse", "True")

        structuresFormLayout.addRow("RT2 Structures: ", self.rtstruct_selector)

        # --- BOTÓN PARA OCULTAR TODAS LAS ESTRUCTURAS ---
        self.hide_all_button = qt.QPushButton("Hide all Structures")
        self.hide_all_button.setStyleSheet("background-color: #34495e; color: white; padding: 5px;")
        structuresFormLayout.addRow(self.hide_all_button)

        # Conectar el botón a la función
        self.hide_all_button.connect('clicked(bool)', self.onHideAllStructures)

        # 2. Inyectar la Tabla Nativa de Segmentos de Slicer
        self.segments_table = slicer.qMRMLSegmentsTableView()
        self.segments_table.setMRMLScene(slicer.mrmlScene)
        structuresFormLayout.addRow(self.segments_table)

        # 3. Conectar el selector con la tabla
        self.rtstruct_selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onRTStructSelected)

        # (Aquí termina tu código del Panel 2)
        # 3. Conectar el selector con la tabla
        self.rtstruct_selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onRTStructSelected)

        # ==========================================================
        # PANEL 2.1: CONFIGURACIÓN BIOLÓGICA Y ASIGANCION DE ROLES
        # ==========================================================
        bioCollapsibleButton = ctk.ctkCollapsibleButton()
        bioCollapsibleButton.text = "2.1: Biological Configuration "
        self.layout.addWidget(bioCollapsibleButton)
        bioFormLayout = qt.QFormLayout(bioCollapsibleButton)

        # --- BOTÓN DE EMBUDO ---
        self.load_bio_button = qt.QPushButton("Biological Role of Visible Structures")
        self.load_bio_button.setStyleSheet(
            "background-color: #2980b9; color: white; font-weight: bold; margin-top: 5px;")
        self.load_bio_button.setToolTip(
            "Carga solo las estructuras que dejaste con el 'ojito' encendido en el Panel 2.")
        bioFormLayout.addRow(self.load_bio_button)

        # --- TABLA PURA DE ROLES (Qt) ---
        self.bio_table = qt.QTableWidget()
        self.bio_table.setColumnCount(3)
        self.bio_table.setHorizontalHeaderLabels(["Structure Name", "Role", "Overlap Priority"])

        # Estética de la tabla
        self.bio_table.horizontalHeader().setStretchLastSection(True)
        self.bio_table.horizontalHeader().setSectionResizeMode(0, qt.QHeaderView.Stretch)
        self.bio_table.verticalHeader().setVisible(False)
        self.bio_table.setMinimumHeight(180)
        bioFormLayout.addRow(self.bio_table)

        # Conectamos el botón a nuestra nueva función
        self.load_bio_button.connect('clicked(bool)', self.onLoadStructuresForBiology)

        # =========================================================================================================================================
        # PANEL 3: REIRRADIATION ANALYSIS
        # ========================================================================================================================================
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "3: Reirradiation Calculation Settings"
        self.layout.addWidget(parametersCollapsibleButton)

        # Layout principal del panel
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        # =======================================================
        # GRUPO 1: VOLÚMENES DE DOSIS (INPUTS)
        # =======================================================
        doses_groupBox = qt.QGroupBox("3.1: Dose Volumes")
        doses_groupBox.setStyleSheet("QGroupBox { font-weight: bold; }")
        doses_layout = qt.QFormLayout(doses_groupBox)

        # Selector for Dose A (RT1)
        self.dose_a_selector = slicer.qMRMLNodeComboBox()
        self.dose_a_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.dose_a_selector.selectNodeUponCreation = True
        self.dose_a_selector.addEnabled = False
        self.dose_a_selector.removeEnabled = False
        self.dose_a_selector.noneEnabled = False
        self.dose_a_selector.showHidden = False
        self.dose_a_selector.showChildNodeTypes = True
        self.dose_a_selector.setMRMLScene(slicer.mrmlScene)
        self.dose_a_selector.setToolTip("Select the dose matrix for the Previous Radiation Course (RT1).")
        doses_layout.addRow("RD Previous (RT1) (Resampled) : ", self.dose_a_selector)

        # Selector for Dose B (RT2)
        self.dose_b_selector = slicer.qMRMLNodeComboBox()
        self.dose_b_selector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.dose_b_selector.selectNodeUponCreation = True
        self.dose_b_selector.addEnabled = False
        self.dose_b_selector.removeEnabled = False
        self.dose_b_selector.noneEnabled = False
        self.dose_b_selector.showHidden = False
        self.dose_b_selector.showChildNodeTypes = True
        self.dose_b_selector.setMRMLScene(slicer.mrmlScene)
        self.dose_b_selector.setToolTip("Select the dose matrix for the Planned Radiation Course (RT2).")
        doses_layout.addRow("RD Planned (RT2): ", self.dose_b_selector)

        # Añadimos el Grupo 1 al layout principal
        parametersFormLayout.addRow(doses_groupBox)

        # =======================================================
        # GRUPO 2: PARÁMETROS BIOLÓGICOS Y DE FRACCIONAMIENTO
        # =======================================================
        bio_groupBox = qt.QGroupBox("3.2: Biological & Fractionation Parameters")
        bio_groupBox.setStyleSheet("QGroupBox { font-weight: bold; }")
        bio_layout = qt.QFormLayout(bio_groupBox)

        # SpinBox for fractions_a (RT1)
        self.fractions_a_spinbox = qt.QSpinBox()
        self.fractions_a_spinbox.setValue(25)
        self.fractions_a_spinbox.setMaximum(100)
        bio_layout.addRow("Fractions (RT1): ", self.fractions_a_spinbox)

        # SpinBox for fractions_b (RT2)
        self.fractions_b_spinbox = qt.QSpinBox()
        self.fractions_b_spinbox.setValue(10)
        self.fractions_b_spinbox.setMaximum(100)
        bio_layout.addRow("Fractions (RT2): ", self.fractions_b_spinbox)

        # SpinBox for Alpha/Beta Ratio fo OARs (ab)
        self.ab_spinbox = qt.QDoubleSpinBox()
        self.ab_spinbox.setValue(3.0)
        self.ab_spinbox.setDecimals(1)
        self.ab_spinbox.setToolTip("Alpha/Beta Ratio (\u03b1/\u03b2) Organs at risk (OARs) (Gy).")
        bio_layout.addRow("\u03b1/\u03b2 Ratio OARs (Gy): ", self.ab_spinbox)

        # SpinBox for Alpha/Beta Ratio for Tumor (ab)
        self.ab_tumor_spinbox = qt.QDoubleSpinBox()
        self.ab_tumor_spinbox.setValue(10)
        self.ab_tumor_spinbox.setDecimals(1)
        self.ab_tumor_spinbox.setToolTip("Alpha/Beta Ratio (\u03b1/\u03b2) Tumor (Gy).")
        bio_layout.addRow("\u03b1/\u03b2 Ratio Tumor (Gy): ", self.ab_tumor_spinbox)

        # Añadimos el Grupo 2 al layout principal
        parametersFormLayout.addRow(bio_groupBox)

        # =======================================================
        # GRUPO 3: RECUPERACIÓN TISULAR Y SALIDA
        # =======================================================
        recovery_groupBox = qt.QGroupBox("3.3: Tissue Recovery & Output Configuration")
        recovery_groupBox.setStyleSheet("QGroupBox { font-weight: bold; }")
        recovery_layout = qt.QFormLayout(recovery_groupBox)

        # Recovery Factor Checkbox
        self.recovery_checkbox = qt.QCheckBox("Enable Partial Recovery (Time-based model)")
        self.recovery_checkbox.setChecked(False)
        self.recovery_checkbox.setToolTip(
            "The BED contribution from the previous irradiation course is reduced according its recovery assumption before being combined with the new treatment")
        recovery_layout.addRow(self.recovery_checkbox)

        # Months Spinbox
        self.months_spinbox = qt.QSpinBox()
        self.months_spinbox.setRange(0, 100)
        self.months_spinbox.setValue(12)
        self.months_spinbox.setSuffix(" months")
        self.months_spinbox.setEnabled(False)  # Inicia apagado
        recovery_layout.addRow("Time interval: ", self.months_spinbox)

        # Output Volume Name
        self.output_name_input = qt.QLineEdit()
        self.output_name_input.setPlaceholderText("Optional: Custom name for the new volume...")
        self.output_name_input.setToolTip("If you leave it blank, it will use the default name.")
        recovery_layout.addRow("Output Dose Name: ", self.output_name_input)

        # Añadimos el Grupo 3 al layout principal
        parametersFormLayout.addRow(recovery_groupBox)

        # --- Conexión de la casilla de meses ---
        self.recovery_checkbox.connect('toggled(bool)', self.months_spinbox.setEnabled)

        # =======================================================
        # BOTÓN DE CÁLCULO MAESTRO
        # =======================================================
        self.applyButton = qt.QPushButton("Calculate Cumulative EQD2 Dose")
        self.applyButton.toolTip = "Execute the voxel-by-voxel BED/EQD2 accumulation."
        self.applyButton.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                padding: 8px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        parametersFormLayout.addRow(self.applyButton)

        # Connect button to function
        self.applyButton.connect('clicked(bool)', self.onApplyButton)
        # ==========================================================
        # PANEL 4: ANÁLISIS DOSIMÉTRICO (EQD2 METRICS)
        # ==========================================================

        metricsCollapsibleButton = ctk.ctkCollapsibleButton()
        metricsCollapsibleButton.text = "4: EQD2 Metrics and DVH"
        self.layout.addWidget(metricsCollapsibleButton)
        metricsFormLayout = qt.QFormLayout(metricsCollapsibleButton)

        # Botón para calcular
        self.calc_metrics_button = qt.QPushButton("Calculate Metrics EQD2")
        self.calc_metrics_button.setStyleSheet(
            "background-color: #9b59b6; color: white; font-weight: bold; padding: 5px;")
        metricsFormLayout.addRow(self.calc_metrics_button)

        # Tabla de resultados nativa
        self.metrics_table = qt.QTableWidget()
        self.metrics_table.setColumnCount(3)
        self.metrics_table.setHorizontalHeaderLabels(["Estructure", "Max Dose (Gy)", "Mean Dose (Gy)"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(
            qt.QHeaderView.Stretch)  # Ajusta las columnas al ancho
        metricsFormLayout.addRow(self.metrics_table)

        # --- EL  BOTÓN PARA EL DVH ---
        self.plot_dvh_button = qt.QPushButton("Show DVH")
        self.plot_dvh_button.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 5px;")
        metricsFormLayout.addRow(self.plot_dvh_button)

        # --- Botón de Exportación DICOM ---
        self.exportButton = qt.QPushButton("Export EQD2 to DICOM ")
        self.exportButton.toolTip = "Exports the calculated EQD2 dose with the original patient's DICOM tags."
        self.exportButton.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 5px;")
        self.exportButton.enabled = False  # Nace apagado hasta que se calcule la dosis

        # Asumiendo que parametersFormLayout es el layout donde tienes tus botones principales
        # Ajusta el nombre del layout si lo llamaste diferente en esta sección
        metricsFormLayout.addRow(self.exportButton)

        # Conectar el botón a la función
        self.calc_metrics_button.connect('clicked(bool)', self.onCalculateMetrics)
        self.plot_dvh_button.connect('clicked(bool)', self.onGenerateDVH)
        self.exportButton.connect('clicked(bool)', self.onExportDICOMClicked)

        # Empuja todo hacia arriba para que quede ordenado
        self.layout.addStretch(1)

    # ====================================================================================================================
    # FUNCIONES CONECTADAS
    # ==================================================================================================================

    def onCenterButtonClicked(self):

        self.onHideAllStructures()
        slicer.util.showStatusMessage("Structures Hidden for a clean start.")
        # SEGURIDAD: Limpiar interfaz ANTES de hacer cualquier cálculo
        self.resetResultsDisplay()

        fixed_ct = self.fixed_ct_selector.currentNode()
        moving_ct = self.moving_ct_selector.currentNode()

        # 1. Validación de seguridad básica
        if not fixed_ct or not moving_ct:
            slicer.util.warningDisplay("Please select the Fixed CT and Moving CT first.")
            return

        # 2. Validación: Evitar la ilusión óptica de Slicer
        if fixed_ct == moving_ct:
            slicer.util.warningDisplay("Fixed CT and Moving CT cannot be the exact same volume.")
            return

        import numpy as np
        import vtk

        try:
            # ==========================================================
            # NUEVO: VALIDACIÓN ANTI "CLOSE SCENE" (Exorcismo de Fantasmas)
            # ==========================================================
            if self.manual_transform_node:
                try:
                    # Intentamos buscar el nodo en la escena actual
                    if not slicer.mrmlScene.GetNodeByID(self.manual_transform_node.GetID()):
                        self.manual_transform_node = None  # Estaba borrado, reseteamos la variable
                except:
                    # Si el C++ fue destruido, pedir el GetID falla. Lo atrapamos aquí.
                    self.manual_transform_node = None

            # Si la variable está vacía (o la acabamos de vaciar), creamos un volante nuevo y real
            if not self.manual_transform_node:
                self.manual_transform_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode",
                                                                                "Manual_PreAlign")
            # ==========================================================

            moving_ct.SetAndObserveTransformNodeID(None)
            slicer.app.processEvents()

            # Cálculo de centros
            def get_true_center(volume_node):
                matrix = vtk.vtkMatrix4x4()
                volume_node.GetIJKToRASMatrix(matrix)
                image_data = volume_node.GetImageData()
                if image_data:
                    dims = image_data.GetDimensions()
                    center_ijk = [dims[0] / 2.0, dims[1] / 2.0, dims[2] / 2.0, 1.0]
                    center_ras = matrix.MultiplyPoint(center_ijk)
                    return np.array(center_ras[0:3])
                else:
                    bounds = np.zeros(6)
                    volume_node.GetBounds(bounds)
                    return np.array(
                        [(bounds[0] + bounds[1]) / 2.0, (bounds[2] + bounds[3]) / 2.0, (bounds[4] + bounds[5]) / 2.0])

            cf = get_true_center(fixed_ct)
            cm = get_true_center(moving_ct)

            self.base_translation = cf - cm

            # Resetear barras visualmente (sin disparar el evento)
            self.sliderX.blockSignals(True);
            self.sliderY.blockSignals(True);
            self.sliderZ.blockSignals(True)
            self.sliderX.value = 0;
            self.sliderY.value = 0;
            self.sliderZ.value = 0;
            self.sliderX.blockSignals(False);
            self.sliderY.blockSignals(False);
            self.sliderZ.blockSignals(False)

            self.updateManualTransform(0, 0, 0)
            moving_ct.SetAndObserveTransformNodeID(self.manual_transform_node.GetID())

            slicer.util.setSliceViewerLayers(background=fixed_ct, foreground=moving_ct, foregroundOpacity=0.5)
            slicer.modules.markups.logic().JumpSlicesToLocation(cf[0], cf[1], cf[2], True)

            # Despertar las barras
            self.sliderX.enabled = True
            self.sliderY.enabled = True
            self.sliderZ.enabled = True

            self.sliderPitch.enabled = True
            self.sliderRoll.enabled = True
            self.sliderYaw.enabled = True

            slicer.util.showStatusMessage("CTs Centered .")

        except Exception as e:
            slicer.util.errorDisplay(f"Error during Auto-Center: {str(e)}\nPlease check if the CT is fully loaded.")

    def onSliderValueChanged(self, value):
        # Bloque de seguridad para cuando mueves las barras
        if self.manual_transform_node:
            try:
                # Comprobar que el nodo existe en la escena antes de inyectarle movimiento
                if slicer.mrmlScene.GetNodeByID(self.manual_transform_node.GetID()):
                    self.updateManualTransform(
                        self.sliderX.value, self.sliderY.value, self.sliderZ.value,
                        self.sliderPitch.value, self.sliderRoll.value, self.sliderYaw.value)
            except:
                pass  # Ignorar silenciosamente si el nodo es un fantasma

    def updateManualTransform(self, dx, dy, dz, pitch=0, roll=0, yaw=0):
        import vtk
        # 1. IDENTIFICAR EL VOLUMEN MÓVIL
        # Asegúrate de que este sea el nombre correcto de tu selector del CT previo
        moving_volume = self.moving_ct_selector.currentNode()

        if not moving_volume:
            return

        # ---  Memorizar el centro para evitar el "brinco" visual ---
        volume_id = moving_volume.GetID()
        current_origin = moving_volume.GetOrigin()

        # Si es la primera vez que movemos ESTE volumen, le calculamos el centro puro
        if not hasattr(self, "pure_center_id") or self.pure_center_id != volume_id or \
                not hasattr(self, "pure_center_origin") or self.pure_center_origin != current_origin:

            moving_volume.SetAndObserveTransformNodeID(None)
            bounds = [0, 0, 0, 0, 0, 0]
            moving_volume.GetRASBounds(bounds)
            cx = (bounds[0] + bounds[1]) / 2.0
            cy = (bounds[2] + bounds[3]) / 2.0
            cz = (bounds[4] + bounds[5]) / 2.0

            # Guardamos los datos en la memoria del módulo
            self.pure_center = (cx, cy, cz)
            self.pure_center_id = volume_id
            self.pure_center_origin = current_origin  # Memorizamos el origen actual

            moving_volume.SetAndObserveTransformNodeID(self.manual_transform_node.GetID())
        else:
            # Si ya lo habíamos medido, simplemente rescatamos el dato de la memoria
            cx, cy, cz = self.pure_center

        # ------------------------------------------------------------------------

        # CREAR LA MATRIZ DE TRANSFORMACIÓN
        transform = vtk.vtkTransform()
        transform.PostMultiply()

        # PASO A: Llevar al origen
        transform.Translate(-cx, -cy, -cz)

        # PASO B: Rotar
        transform.RotateX(pitch)
        transform.RotateY(roll)
        transform.RotateZ(yaw)

        # PASO C: Devolver al centro
        transform.Translate(cx, cy, cz)

        # PASO D: Traslación final de los sliders
        transform.Translate(self.base_translation[0] + dx,
                            self.base_translation[1] + dy,
                            self.base_translation[2] + dz)

        self.manual_transform_node.SetMatrixTransformToParent(transform.GetMatrix())


    def onAdvancedRotationToggled(self, isChecked):
        """Muestra u oculta los sliders de rotación para mantener la interfaz limpia."""
        if isChecked:
            self.sliderPitch.show()
            self.sliderRoll.show()
            self.sliderYaw.show()
        else:
            self.sliderPitch.hide()
            self.sliderRoll.hide()
            self.sliderYaw.hide()
            # Opcional: Si se ocultan, podríamos devolver la rotación a 0 para mayor seguridad clínica.
            # Por ahora solo los ocultamos para no perder el trabajo del usuario.

    def onManualOnlyToggled(self, isChecked):
        """Si el usuario decide usar SOLO alineación manual, desactivamos las opciones de BRAINSFit."""
        if isChecked:
            self.affine_checkbox.setChecked(False)
            self.deformable_checkbox.setChecked(False)
            self.affine_checkbox.setEnabled(False)
            self.deformable_checkbox.setEnabled(False)
            self.advanced_rotation_checkbox.setEnabled(True)  # Permitir rotación manual
            self.registerButton.text = "Apply Manual Alignment & Resample Dose"
            self.registerButton.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")  # Naranja
        else:
            self.affine_checkbox.setEnabled(True)
            self.deformable_checkbox.setEnabled(True)
            self.registerButton.text = "Auto-Registration and Dose Resample"
            self.registerButton.setStyleSheet(
                "background-color: #2196F3; color: white; font-weight: bold;")  # Azul original
            # --- PROTECCIÓN ANTI-BRAINSFIT ---
            # Deshabilitamos la rotación
            self.advanced_rotation_checkbox.setChecked(False)
            self.advanced_rotation_checkbox.setEnabled(False)
            self.onAdvancedRotationToggled(False)  # Esto oculta los sliders

            # Reseteamos los valores de rotación a 0 para asegurar un inicio limpio
            self.sliderPitch.value = 0
            self.sliderRoll.value = 0
            self.sliderYaw.value = 0

    def onApplyButton(self):
        # SEGURIDAD: Limpiar interfaz ANTES de hacer cualquier cálculo
        self.resetResultsDisplay()
        # Bloqueamos el botón temporalmente para que no hagan doble clic
        self.applyButton.setEnabled(False)

        # ==========================================================
        # 1. CREAR VENTANA DE ESPERA (PROGRESS DIALOG)
        # ==========================================================
        progress_dialog = slicer.util.createProgressDialog(
            parent=slicer.util.mainWindow(),
            labelText="Calculating 3D biological Dose EQD2...\n\nThis may take a moment. Please wait.",
            maximum=0  # ¡El '0' es el truco! Hace que la barra se mueva de lado a lado infinitamente
        )
        progress_dialog.windowTitle = "RadReirradiation - Processing Dose"
        progress_dialog.setCancelButton(None)  # Ocultamos el botón "Cancelar" para que el usuario no rompa el cálculo
        progress_dialog.show()
        slicer.app.processEvents()  # Forzamos a que la ventana se dibuje INMEDIATAMENTE en pantalla

        try:

            try:
                slicer.util.showStatusMessage("Calculating new EQD2 dose... Please wait.")

                # ===================== TABLA BIOLÓGICA ====================================
                # 1. Extraemos la configuración de la tabla
                current_bio_setup = self.getBiologicalConfiguration()

                # 2. Imprimimos para ver la magia en la consola de Python de Slicer
                print("--- Biological configuration extracted ---")
                for structure, config in current_bio_setup.items():
                    print(f"structure: {structure} | Role: {config['role']} | Wins in interception: {config['priority']}")
                print("----------------------------------------")

                # Si la tabla estaba vacía, detenemos el cálculo por seguridad
                if not current_bio_setup:
                    slicer.util.warningDisplay("The biological table is empty. Please load the structures first..")
                    return
                # =========================================================================

                import numpy as np

                # 1. Recolectar los datos que el usuario puso en la interfaz
                dose_a_node = self.dose_a_selector.currentNode()
                dose_b_node = self.dose_b_selector.currentNode()
                fx_a = self.fractions_a_spinbox.value
                fx_b = self.fractions_b_spinbox.value
                use_recovery = self.recovery_checkbox.isChecked()
                months = self.months_spinbox.value
                custom_name = self.output_name_input.text.strip()

                # ---  LÓGICA: VALORES ALPHA/BETA ---

                ab_oar_value = float(self.ab_spinbox.value)
                ab_tumor_value = float(self.ab_tumor_spinbox.value)

                # --- CREACIÓN DEL MAPA BIOLÓGICO 3D (Las Capas) ---
                slicer.util.showStatusMessage("Generating biological masks...")
                slicer.app.processEvents()  # Mantiene la UI fluida

                # Usamos dose_a_node como referencia para el tamaño (shape) del paciente
                dose_array_shape = slicer.util.arrayFromVolume(dose_a_node).shape
                ab_map = np.full(dose_array_shape, ab_oar_value, dtype=np.float32)

                segmentation_node = self.rtstruct_selector.currentNode()
                segmentation = segmentation_node.GetSegmentation()

                tumor_mask_global = np.zeros(dose_array_shape, dtype=bool)
                oar_mask_global = np.zeros(dose_array_shape, dtype=bool)
                segment_masks = {}

                # Recorremos y extraemos matrices de las estructuras seleccionadas
                for i in range(segmentation.GetNumberOfSegments()):
                    segment_id = segmentation.GetNthSegmentID(i)
                    segment_name = segmentation.GetSegment(segment_id).GetName()

                    if segment_name in current_bio_setup:
                        # Extraer matriz binaria, ajustada al tamaño de la dosis A
                        segment_array = slicer.util.arrayFromSegmentBinaryLabelmap(segmentation_node, segment_id,
                                                                                   dose_a_node)

                        if segment_array is not None:
                            binary_mask = (segment_array > 0)
                            segment_masks[segment_name] = binary_mask

                            if current_bio_setup[segment_name]["role"] == "Tumor":
                                tumor_mask_global |= binary_mask
                            else:
                                oar_mask_global |= binary_mask

                # Pintamos las capas en la matriz ab_map
                ab_map[tumor_mask_global] = ab_tumor_value
                ab_map[oar_mask_global] = ab_oar_value  # La Capa 3: OAR sobreescribe Tumor por defecto

                # Capa 4: Excepciones (Si el usuario forzó que un Tumor gane)
                for name, config in current_bio_setup.items():
                    if config["priority"] == "Tumor" and name in segment_masks:
                        overlap = segment_masks[name] & tumor_mask_global
                        ab_map[overlap] = ab_tumor_value

                # 2. Enviar los datos a la Lógica (el cerebro)
                try:
                    slicer.util.showStatusMessage("Calculating BED/EQD2 voxel by voxel...")

                    # ¡Llamamos a la magia! ATENCIÓN: Ahora enviamos 'ab_map' en lugar de 'ab'
                    resultado = self.logic.procesarDosis(dose_a_node, dose_b_node, ab_map, fx_a, fx_b, use_recovery, months,
                                                         custom_name)

                    # 1. Guardar el resultado en la memoria del Widget (para el botón de exportar)
                    self.eqd2_node = resultado
                    # Encendemos el botón verde de exportar
                    self.exportButton.enabled = True

                    slicer.util.showStatusMessage("¡Calculation completed!")
                    slicer.util.infoDisplay("Cumulative EQD2 calculation successfully completed!",
                                            windowTitle="RadReirradiation")

                except Exception as e:
                    # Si algo falla (ej. tamaños distintos)
                    slicer.util.errorDisplay(f"Calculation Error:\n{str(e)}", windowTitle="RadReirradiation Error")

            except Exception as e:
                slicer.util.errorDisplay(f"Calculation failed: {e}")
        except Exception as e:
            slicer.util.errorDisplay(f"Calculation failed: {e}")
        # ==========================================================
        # 2. CERRAR VENTANA DE ESPERA Y LIBERAR INTERFAZ
        # ==========================================================
        finally:
            #  Al terminar (o si hay error), volvemos a habilitar el botón
            self.applyButton.setEnabled(True)
            slicer.util.showStatusMessage("Ready.")
            progress_dialog.close()  # Destruimos la ventana de carga

    def updateVisualizationSelector(self, node=None):
        """Filtra el combobox del Panel 2 para mostrar solo las estructuras cargadas en el Panel 1"""
        segmentation_nodes = list(slicer.util.getNodesByClass("vtkMRMLSegmentationNode"))

        # 1. Quitamos la etiqueta especial a TODAS las estructuras de la escena
        for seg_node in segmentation_nodes:
            seg_node.RemoveAttribute("RadReirradiationUse")

        # 2. Leemos qué seleccionó el usuario exactamente en el Panel 1
        fixed_node = getattr(self, 'fixed_rtstruct_selector', None)
        moving_node = getattr(self, 'moving_rtstruct_selector', None)

        # 3. Le ponemos la etiqueta VIP SOLO a las elegidas
        if fixed_node and fixed_node.currentNode():
            fixed_node.currentNode().SetAttribute("RadReirradiationUse", "True")

        if moving_node and moving_node.currentNode():
            moving_node.currentNode().SetAttribute("RadReirradiationUse", "True")

    def onRegisterButton(self):

        fixed_ct = self.fixed_ct_selector.currentNode()
        moving_ct = self.moving_ct_selector.currentNode()
        moving_dose = self.moving_dose_selector.currentNode()
        fixed_dose = self.fixed_dose_selector.currentNode()
        moving_rtstruct = self.moving_rtstruct_selector.currentNode()
        fixed_rtstruct = self.fixed_rtstruct_selector.currentNode()

        # Leemos qué algoritmos quiere el usuario
        use_deformable = self.deformable_checkbox.isChecked()
        use_affine = self.affine_checkbox.isChecked()
        use_manual_only = self.manual_only_checkbox.isChecked()  # <-- Leemos la nueva casilla

        if not fixed_ct or not moving_ct or not moving_dose:
            slicer.util.errorDisplay("Please select the two CTs and the Dose you wish to align.",
                                     windowTitle="Data is missing")
            return

        # =======================================================
        # BARRERA DE SEGURIDAD INTERLOCK (Anti-Error Humano)
        # =======================================================
        if fixed_rtstruct and moving_rtstruct:
            if fixed_rtstruct.GetID() == moving_rtstruct.GetID():
                slicer.util.errorDisplay(
                    "CRITICAL ERROR: El set de estructuras fijas (Current) y móviles (Prev) no pueden ser el mismo.\n\n"
                    "Por seguridad, el proceso se ha detenido para evitar deformar las estructuras actuales.",
                    windowTitle="Validación Interlock"
                )
                return

        try:
            # Mensajes de estado dinámicos
            if use_manual_only:
                slicer.util.showStatusMessage("Applying Manual Alignment & Resampling Dose...")
            elif use_deformable:
                slicer.util.showStatusMessage("Running Deformable Registration (May take minutes)...")
            else:
                slicer.util.showStatusMessage("Running Rigid Registration...")

            # =======================================================
            # 2. LLAMAR A LA LÓGICA (obtenemos dosis y matrix de de transformacion)
            # =======================================================
            aligned_dose_node, transform_node = self.logic.runFastRegistration(
                fixed_ct, moving_ct, moving_dose, fixed_dose,
                use_deformable, use_affine, self.manual_transform_node, use_manual_only
            )

            if not aligned_dose_node:
                return  # Si falló algo en la lógica, paramos.

            # =======================================================
            # 2.5 NUEVO: ALINEAR, DIFERENCIAR Y RENOMBRAR ESTRUCTURAS MÓVILES
            # =======================================================
            moving_rtstruct = self.moving_rtstruct_selector.currentNode()

            if moving_rtstruct and transform_node:
                # A. Aplicar la matriz matemática a las estructuras móviles
                moving_rtstruct.SetAndObserveTransformNodeID(transform_node.GetID())

                # B. Diferenciación Visual: Contornos huecos
                display_node = moving_rtstruct.GetDisplayNode()
                if display_node:
                    display_node.SetVisibility(True)
                    display_node.SetVisibility2D(True)
                    display_node.SetVisibility2DFill(False)
                    display_node.SetVisibility2DOutline(True)
                    display_node.SetSliceIntersectionThickness(3)

                # C. MAGIA PARA EL DVH: Renombrar los segmentos internos
                segmentation = moving_rtstruct.GetSegmentation()
                for i in range(segmentation.GetNumberOfSegments()):
                    segment_id = segmentation.GetNthSegmentID(i)
                    segment = segmentation.GetSegment(segment_id)
                    current_name = segment.GetName()

                    # Evitar que se agregue _PREV múltiples veces si el usuario registra dos veces
                    if not current_name.endswith("_PREV"):
                        segment.SetName(current_name + "_PREV")

                # D. Renombrar el nodo padre para que en la interfaz también sea obvio
                parent_name = moving_rtstruct.GetName()
                if not parent_name.endswith("_REGISTERED"):
                    moving_rtstruct.SetName(parent_name + "_REGISTERED")

            # =======================================================
            # 3. MAGIA UX: Asignación al Paso 2
            # =======================================================
            self.dose_a_selector.setCurrentNode(aligned_dose_node)
            self.dose_b_selector.setCurrentNode(fixed_dose)

            slicer.util.showStatusMessage("Registration and Dose resampling completed!")
            slicer.util.infoDisplay(
                "Successful alignment.\n\nLook for the new Dose volume with the suffix '_Resampled' in your Base Dose (RT1) list to perform the calculation.",
                windowTitle="RadReirradiation FastReg")

        except Exception as e:
            slicer.util.errorDisplay(f"Error during image registration:\n{str(e)}",
                                     windowTitle="RadReirradiation Error")

    def onRTStructSelected(self, node):
        """Conecta las estructuras a la tabla usando la visualización nativa de SlicerRT"""
        if node:
            # 1. Conectamos el nodo directamente a la tabla
            self.segments_table.setSegmentationNode(node)

            # 2. Aseguramos el interruptor maestro y ajustamos la estética clínica
            display_node = node.GetDisplayNode()
            if display_node:
                display_node.SetVisibility(True)
                display_node.SetVisibility2D(True)

                # =======================================================
                # 3. MAGIA LÓGICA: ¿Es la estructura fija o la móvil?
                # =======================================================
                if node.GetTransformNodeID():
                    # Opción A: Tiene transformación (Es RS PREVIOUS registrada)
                    # La hacemos hueca y con bordes gruesos
                    display_node.SetVisibility2DFill(False)
                    display_node.SetVisibility2DOutline(True)
                    display_node.SetSliceIntersectionThickness(3)
                    slicer.util.showStatusMessage("Showing Registered Moving Structures (Outline)")
                else:
                    # Opción B: No tiene transformación (Es RS CURRENT fija)
                    # Le damos el aspecto clínico estándar de Slicer (relleno transparente)
                    display_node.SetVisibility2DFill(True)
                    display_node.SetOpacity2DFill(0.3)
                    display_node.SetOpacity2DOutline(1.0)
                    display_node.SetSliceIntersectionThickness(1)
                    slicer.util.showStatusMessage("Showing Base Fixed Structures (Filled)")

        else:
            # Si se selecciona "None", vaciamos la tabla
            self.segments_table.setSegmentationNode(None)

    def onHideAllStructures(self):
        slicer.util.showStatusMessage("Coordinating visibility for all structures...")
        slicer.app.processEvents()

        segmentation_nodes = slicer.util.getNodesByClass("vtkMRMLSegmentationNode")

        # =======================================================
        # PASO 1: Evaluación Global (¿Hay ALGO encendido en la escena?)
        # =======================================================
        global_any_visible = False

        for node in segmentation_nodes:
            display_node = node.GetDisplayNode()
            if display_node:
                segmentation = node.GetSegmentation()
                for i in range(segmentation.GetNumberOfSegments()):
                    segment_id = segmentation.GetNthSegmentID(i)
                    if display_node.GetSegmentVisibility(segment_id):
                        global_any_visible = True
                        break  # Encontramos uno encendido, dejamos de buscar el primer set
            if global_any_visible:
                break  # Rompemos el ciclo principal, ya tenemos nuestra respuesta global

        # =======================================================
        # PASO 2: Acción Sincronizada (Aplicar a todos usando la decisión GLOBAL)
        # =======================================================
        for node in segmentation_nodes:
            display_node = node.GetDisplayNode()
            if display_node:
                # 1. OBLIGATORIO: Mantener el contenedor padre encendido para que la tabla funcione
                display_node.SetVisibility(True)

                # 2. Sincronizar la interfaz basándonos estrictamente en el estado global
                if global_any_visible:
                    # Si había al menos una estructura visible en toda la escena, la orden para TODOS es apagar
                    display_node.SetAllSegmentsVisibility(False)
                else:
                    # Si absolutamente todo estaba oculto en la escena, la orden para TODOS es encender
                    display_node.SetAllSegmentsVisibility(True)

        slicer.util.showStatusMessage("")

    def onLoadStructuresForBiology(self):
        # SEGURIDAD: Limpiar interfaz ANTES de hacer cualquier cálculo
        self.resetResultsDisplay()
        """Lee TODOS los sets de estructuras en la escena y genera la tabla solo con las visibles."""
        # 1. Buscamos todos los nodos de segmentación en la escena en lugar de usar un solo selector
        segmentation_nodes = list(slicer.util.getNodesByClass("vtkMRMLSegmentationNode"))

        if not segmentation_nodes:
            slicer.util.warningDisplay("No RTSTRUCTs found in the scene.")
            return

        # Limpiamos la tabla en caso de que el usuario vuelva a presionar el botón
        self.bio_table.setRowCount(0)
        row = 0

        # 2. Recorremos TODOS los sets de estructuras encontrados (Fijos, Móviles, etc.)
        for segmentation_node in segmentation_nodes:
            segmentation = segmentation_node.GetSegmentation()
            display_node = segmentation_node.GetDisplayNode()

            if not display_node:
                continue

            # 3. Recorremos los órganos internos de este set específico
            for i in range(segmentation.GetNumberOfSegments()):
                segment_id = segmentation.GetNthSegmentID(i)

                # EL EMBUDO: Solo pasan las estructuras con el "ojito" encendido
                if display_node.GetSegmentVisibility(segment_id):
                    segment_name = segmentation.GetSegment(segment_id).GetName()

                    self.bio_table.insertRow(row)

                    # Columna 0: Nombre de la estructura (Solo lectura)
                    name_item = qt.QTableWidgetItem(segment_name)
                    name_item.setFlags(name_item.flags() & ~qt.Qt.ItemIsEditable)
                    self.bio_table.setItem(row, 0, name_item)

                    # Columna 1: Menú de Rol (OAR / Tumor)
                    role_combo = qt.QComboBox()
                    role_combo.addItems(["OAR", "Tumor"])
                    role_combo.setStyleSheet("background-color: white; color: black;")
                    self.bio_table.setCellWidget(row, 1, role_combo)

                    # Columna 2: Menú de Prioridad
                    priority_combo = qt.QComboBox()
                    priority_combo.addItems(["OAR", "Tumor"])
                    priority_combo.setStyleSheet("background-color: #ecf0f1; color: black;")
                    self.bio_table.setCellWidget(row, 2, priority_combo)

                    # Conexión de señales para los estilos
                    role_combo.connect("currentTextChanged(QString)",
                                       lambda text, r_combo=role_combo, p_combo=priority_combo: self.onRoleStyleUpdate(
                                           text, r_combo, p_combo))

                    row += 1

        if row > 0:
            slicer.util.showStatusMessage(f"Success: {row} structures loaded for biological setup.")
        else:
            slicer.util.warningDisplay(
                "No visible structures found. Please turn on the 'eye' icon for at least one structure in your panels.")
    def onRoleStyleUpdate(self, text, r_combo, p_combo):
        """Actualiza visualmente los menús de rol y prioridad basado en la selección."""
        if text == "Tumor":
            # 1. Pintamos el menú de Rol
            r_combo.setStyleSheet(
                "background-color: #fdf2e9; color: #d35400; font-weight: bold;")  # Naranja/Rojizo suave con negrita

            # 2. Ajustamos y pintamos el menú de Prioridad del mismo color
            p_combo.setCurrentText("OAR")
            p_combo.setStyleSheet("background-color: #fdf2e9; color: #d35400;")
        else:
            # 1. Volvemos al estilo estándar para el menú de Rol
            r_combo.setStyleSheet("background-color: white; color: black; font-weight: normal;")

            # 2. Volvemos al estilo estándar para el menú de Prioridad
            p_combo.setCurrentText("OAR")
            p_combo.setStyleSheet("background-color: #ecf0f1; color: black;")

    def getBiologicalConfiguration(self):
        """
        Lee la tabla biológica fila por fila y extrae las configuraciones.
        Retorna un diccionario estructurado con los roles y prioridades.
        """
        bio_config = {}

        # Recorremos todas las filas que existan en la tabla
        for row in range(self.bio_table.rowCount):

            # 1. Extraemos el Nombre de la Estructura (Columna 0)
            name_item = self.bio_table.item(row, 0)
            if not name_item:
                continue
            structure_name = name_item.text()

            # 2. Extraemos el Rol seleccionado (Columna 1)
            role_widget = self.bio_table.cellWidget(row, 1)
            # Por seguridad, si por alguna razón falla el widget, asumimos 'OAR'
            role_selected = role_widget.currentText if role_widget else "OAR"

            # 3. Extraemos la Prioridad seleccionada (Columna 2)
            priority_widget = self.bio_table.cellWidget(row, 2)
            priority_selected = priority_widget.currentText if priority_widget else "OAR"

            # 4. Guardamos los datos en nuestro diccionario maestro
            bio_config[structure_name] = {
                "role": role_selected,
                "priority": priority_selected
            }

        return bio_config

    def onCalculateMetrics(self):
        """Calcula métricas forzando la actualización de los datos de dosis visibles en toda la escena"""
        import numpy as np

        # Identificar el volumen activo en el visor rojo
        layoutManager = slicer.app.layoutManager()
        sliceWidget = layoutManager.sliceWidget('Red')
        compositeNode = sliceWidget.sliceLogic().GetSliceCompositeNode()

        # IMPORTANTE: Tomamos el volumen del Foreground (lo que estás viendo)
        foreground_id = compositeNode.GetForegroundVolumeID()
        if not foreground_id:
            slicer.util.warningDisplay(
                "There is no active volume in the foreground layer. Make sure you have the dose map selected.")
            return

        eqd2_dose_node = slicer.mrmlScene.GetNodeByID(foreground_id)

        slicer.util.showStatusMessage(f"Calculating about: {eqd2_dose_node.GetName()}...")
        slicer.app.processEvents()

        # ==========================================================
        # ESCÁNER GLOBAL: Buscamos TODOS los sets de estructuras
        # ==========================================================
        segmentation_nodes = list(slicer.util.getNodesByClass("vtkMRMLSegmentationNode"))
        if not segmentation_nodes:
            slicer.util.warningDisplay("No RTSTRUCTs found in the scene.")
            return

        self.metrics_table.setRowCount(0)
        row = 0

        # EXTRAER LA MATRIZ DE DOSIS ACTUALIZADA
        dose_array = slicer.util.arrayFromVolume(eqd2_dose_node)

        # Recorremos cada set de estructuras encontrado
        for segmentation_node in segmentation_nodes:
            segmentation = segmentation_node.GetSegmentation()
            display_node = segmentation_node.GetDisplayNode()

            if not display_node:
                continue

            # Recorremos los órganos internos de este set
            for i in range(segmentation.GetNumberOfSegments()):
                segment_id = segmentation.GetNthSegmentID(i)

                # EL EMBUDO: Solo pasan las estructuras con el "ojito" encendido
                if display_node.GetSegmentVisibility(segment_id):
                    segment_name = segmentation.GetSegment(segment_id).GetName()

                    # Resamplear el segmento a la resolución del NUEVO volumen de dosis
                    segment_array = slicer.util.arrayFromSegmentBinaryLabelmap(segmentation_node, segment_id,
                                                                               eqd2_dose_node)

                    if segment_array is not None:
                        organ_dose_values = dose_array[segment_array > 0]
                        if len(organ_dose_values) > 0:
                            max_dose = np.max(organ_dose_values)
                            mean_dose = np.mean(organ_dose_values)

                            self.metrics_table.insertRow(row)
                            self.metrics_table.setItem(row, 0, qt.QTableWidgetItem(segment_name))

                            item_max = qt.QTableWidgetItem(f"{max_dose:.2f}")
                            item_max.setTextAlignment(qt.Qt.AlignCenter)
                            self.metrics_table.setItem(row, 1, item_max)

                            item_mean = qt.QTableWidgetItem(f"{mean_dose:.2f}")
                            item_mean.setTextAlignment(qt.Qt.AlignCenter)
                            self.metrics_table.setItem(row, 2, item_mean)

                            row += 1

        slicer.util.showStatusMessage("Metrics updated correctly.")

    def onGenerateDVH(self):
        """Genera el DVH usando todas las estructuras visibles en la escena"""
        import numpy as np
        import vtk

        layoutManager = slicer.app.layoutManager()
        sliceWidget = layoutManager.sliceWidget('Red')
        compositeNode = sliceWidget.sliceLogic().GetSliceCompositeNode()

        foreground_id = compositeNode.GetForegroundVolumeID()
        if not foreground_id:
            slicer.util.warningDisplay("There is no active volume in the foreground layer.")
            return

        eqd2_dose_node = slicer.mrmlScene.GetNodeByID(foreground_id)

        # ==========================================================
        # LIMPIEZA PROFUNDA (GARBAGE COLLECTOR)
        # ==========================================================
        nodes_to_delete = slicer.util.getNodesByClass("vtkMRMLPlotChartNode") + \
                          slicer.util.getNodesByClass("vtkMRMLTableNode") + \
                          slicer.util.getNodesByClass("vtkMRMLPlotSeriesNode")

        for node in nodes_to_delete:
            if "DVH" in node.GetName():
                slicer.mrmlScene.RemoveNode(node)
        # ==========================================================

        plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode", "DVH_EQD2_Chart")
        plotChartNode.SetTitle(f"Dose Volume Histogram ({eqd2_dose_node.GetName()})")
        plotChartNode.SetXAxisTitle("Dose EQD2 (Gy)")
        plotChartNode.SetYAxisTitle("Relative Volume (%)")

        # ==========================================================
        # ESCÁNER GLOBAL: Buscamos TODOS los sets de estructuras
        # ==========================================================
        segmentation_nodes = list(slicer.util.getNodesByClass("vtkMRMLSegmentationNode"))
        if not segmentation_nodes:
            return

        dose_array = slicer.util.arrayFromVolume(eqd2_dose_node)

        # Recorremos cada set de estructuras encontrado
        for segmentation_node in segmentation_nodes:
            segmentation = segmentation_node.GetSegmentation()
            display_node = segmentation_node.GetDisplayNode()

            if not display_node:
                continue

            # Recorremos los órganos internos de este set
            for i in range(segmentation.GetNumberOfSegments()):
                segment_id = segmentation.GetNthSegmentID(i)

                # EL EMBUDO: Solo pasan las estructuras con el "ojito" encendido
                if display_node.GetSegmentVisibility(segment_id):
                    segment_array = slicer.util.arrayFromSegmentBinaryLabelmap(segmentation_node, segment_id,
                                                                               eqd2_dose_node)
                    if segment_array is None: continue

                    organ_dose_values = dose_array[segment_array > 0]
                    if len(organ_dose_values) == 0: continue

                    # Cálculo de DVH
                    max_dose = np.max(organ_dose_values)
                    bins = np.arange(0, max_dose + 0.2, 0.1)
                    hist, _ = np.histogram(organ_dose_values, bins=bins)
                    cum_vol_percent = (np.cumsum(hist[::-1])[::-1] / len(organ_dose_values)) * 100.0

                    # Crear Tabla Única
                    segment_name = segmentation.GetSegment(segment_id).GetName()
                    color = segmentation.GetSegment(segment_id).GetColor()

                    tableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", f"DVH_Data_{segment_name}")
                    dose_col = vtk.vtkDoubleArray()
                    dose_col.SetName("Dose")
                    vol_col = vtk.vtkDoubleArray()
                    vol_col.SetName("Volume")

                    for d, v in zip(bins[:-1], cum_vol_percent):
                        dose_col.InsertNextValue(d)
                        vol_col.InsertNextValue(v)

                    tableNode.AddColumn(dose_col)
                    tableNode.AddColumn(vol_col)

                    seriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", segment_name)
                    seriesNode.SetAndObserveTableNodeID(tableNode.GetID())
                    seriesNode.SetXColumnName("Dose")
                    seriesNode.SetYColumnName("Volume")
                    seriesNode.SetPlotType(slicer.vtkMRMLPlotSeriesNode.PlotTypeScatter)
                    seriesNode.SetMarkerStyle(slicer.vtkMRMLPlotSeriesNode.MarkerStyleNone)
                    seriesNode.SetColor(color[0], color[1], color[2])

                    plotChartNode.AddAndObservePlotSeriesNodeID(seriesNode.GetID())

        # Configurar Layout y mostrar
        layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpPlotView)
        plotWidget = layoutManager.plotWidget(0)
        plotViewNode = plotWidget.mrmlPlotViewNode()
        plotViewNode.SetPlotChartNodeID(plotChartNode.GetID())

        slicer.util.showStatusMessage("¡DVH Successfully generated!")

    def resetResultsDisplay(self):
        """Limpia de forma segura los datos anteriores de las métricas y el DVH."""

        # ---------------------------------------------------------
        # 1. LIMPIAR TABLA DE MÉTRICAS (Interfaz Qt)
        # ---------------------------------------------------------
        if hasattr(self, 'metrics_table') and self.metrics_table is not None:
            self.metrics_table.clearContents()
            self.metrics_table.setRowCount(0)

            # ---------------------------------------------------------
        # 2. LIMPIAR EL GRÁFICO DVH (Corregido para Slicer 5+)
        # ---------------------------------------------------------
        layoutManager = slicer.app.layoutManager()
        if layoutManager:
            # Seleccionamos la ventana del gráfico
            plotWidget = layoutManager.plotWidget(0)


            # Le pedimos al "View Node" que suelte el gráfico actual
            if plotWidget and plotWidget.mrmlPlotViewNode():
                plotWidget.mrmlPlotViewNode().SetPlotChartNodeID("")

        # Vaciamos la memoria interna si el nodo del gráfico está guardado
        if hasattr(self, 'chartNode') and self.chartNode is not None:
            self.chartNode.RemoveAllPlotSeriesNodeIDs()

        # ---------------------------------------------------------
        # 3. FORZAR ACTUALIZACIÓN VISUAL
        # ---------------------------------------------------------
        # Obliga a Slicer a mostrar la pantalla en blanco antes de congelarse calculando
        slicer.app.processEvents()
        print("Interfaz limpia: Lienzo en blanco para el nuevo cálculo.")

    def onExportDICOMClicked(self):
        fixed_ct = self.fixed_ct_selector.currentNode()
        fixed_dose = self.fixed_dose_selector.currentNode()

        if not hasattr(self, 'eqd2_node') or not self.eqd2_node:
            slicer.util.warningDisplay("Please calculate the EQD2 dose first.")
            return

        try:
            shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            eqd2_item_id = shNode.GetItemByDataNode(self.eqd2_node)
            fixed_ct_item_id = shNode.GetItemByDataNode(fixed_ct)

            # 1. Copiar el "ADN" de la dosis original
            attrNames = fixed_dose.GetAttributeNames()
            if attrNames:
                for attrName in attrNames:
                    if attrName.startswith("DICOM."):
                        self.eqd2_node.SetAttribute(attrName, fixed_dose.GetAttribute(attrName))

            self.eqd2_node.SetAttribute("DICOM.Modality", "RTDOSE")
            self.eqd2_node.SetAttribute("DICOM.SeriesDescription", "RadReirradiation_EQD2_Sum")
            self.eqd2_node.RemoveAttribute("DICOM.instanceUIDs")

            # 2. Mover la Dosis para que sea "hermana" exacta del CT en la carpeta del paciente
            parent_item_id = shNode.GetItemParent(fixed_ct_item_id)
            shNode.SetItemParent(eqd2_item_id, parent_item_id)
            shNode.SetItemAttribute(eqd2_item_id, "DICOM.Modality", "RTDOSE")

            # 3. Abrir ventana de exportación
            slicer.modules.dicom.widgetRepresentation()
            exportDialog = slicer.qSlicerDICOMExportDialog(None)
            exportDialog.setMRMLScene(slicer.mrmlScene)
            exportDialog.execDialog()

        except Exception as e:
            slicer.util.errorDisplay(f"Export Error: {str(e)}")


# ==========================================================
# 3. LÓGICA MATEMÁTICA (CEREBRO)
# ==========================================================

class RadReirradiationLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)

    def runFastRegistration(self, fixed_ct, moving_ct, moving_dose, fixed_dose, use_deformable=False, use_affine=False,
                            manual_transform=None, use_manual_only=False):
        # ==========================================================
        # UX: INICIAR VENTANA DE CARGA Y CURSOR DE ESPERA
        # ==========================================================
        slicer.app.setOverrideCursor(qt.Qt.WaitCursor)  # Cambia el ratón a reloj de arena

        # Creamos una barra de progreso "infinita" (maximum=0)
        progress = slicer.util.createProgressDialog(
            parent=slicer.util.mainWindow(),
            labelText="Calculating Image Registration......\nPlease wait, Slicer will appear frozen for a couple of minutes.",
            windowTitle="RadReirradiation Processing",
            value=0, maximum=0
        )
        progress.show()
        slicer.app.processEvents()  # Vital: Fuerza a Slicer a dibujar la ventana antes de congelarse
        try:
            # ==========================================================
            # EL BYPASS: SI NO ES MODO MANUAL, EJECUTAMOS BRAINSFit
            # ==========================================================
            final_transform = None
            # Detectamos si el CT está enganchado al nodo de transformación
            is_manual_active = (manual_transform is not None) and (
                        moving_ct.GetParentTransformNode() == manual_transform)

            if not use_manual_only:


                # 1. Crear el "recipiente" donde se guardará el resultado matemático de la fusión
                transform_name = f"Transform_{moving_ct.GetName()}_to_{fixed_ct.GetName()}"
                final_transform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", transform_name)

                # 2. Configurar el tipo de transformación dinámicamente según la interfaz
                fases_registro = ["Rigid"]  # Rígido siempre es obligatorio como base

                if use_affine:
                    fases_registro.append("Affine")

                if use_deformable:
                    fases_registro.append("BSpline")

                # Unir las palabras con comas (Ej: "Rigid,BSpline" si Affine está apagado)
                t_types = ",".join(fases_registro)

                tasa_muestreo = 0.01 if use_deformable else 0.02

                # 3. Diccionario de Parámetros de BRAINSFit con "Balance Clínico"
                parameters = {
                    "fixedVolume": fixed_ct.GetID(),
                    "movingVolume": moving_ct.GetID(),
                    "transformType": t_types,
                    "maskProcessingMode": "NOMASK",
                    "samplingPercentage": tasa_muestreo,  # 2% de los píxeles (Estándar comercial para velocidad/precisión)
                    "numberOfIterations": 500,  # Límite de intentos para evitar ciclos infinitos
                    "minimumStepLength": 0.005,  # Detenerse temprano si el "match" óseo ya es perfecto
                }

                # 4. El Puente: ¿El usuario ajustó las barras manuales?
                # Si el usuario movió las barras, inyectamos esa matriz inicial sin duplicarla.
                # Si no, usamos el centrado geométrico automático.
                if is_manual_active:
                    parameters["initialTransform"] = manual_transform.GetID()
                    parameters["initializeTransformMode"] = "Off"
                else:
                    parameters["initializeTransformMode"] = "useGeometryAlign"

                # 5. Decirle al motor de registro DÓNDE GUARDAR el resultado
                if use_deformable:
                    parameters["bsplineTransform"] = final_transform.GetID()
                    parameters["splineGridSize"] = [5, 5, 5]
                else:
                    parameters["linearTransform"] = final_transform.GetID()

                # ==========================================================
                # 6. EJECUTAR EL MOTOR DE REGISTRO DE IMÁGENES (BRAINSFit)
                # ==========================================================
                brainsFit = slicer.modules.brainsfit
                cliNode = slicer.cli.runSync(brainsFit, None, parameters)

                if cliNode.GetStatus() & cliNode.ErrorsMask:
                    raise ValueError("The image registration engine (BRAINSFit) failed.")

            # ==========================================================
            # 7. MOVER LA DOSIS ANTIGUA (BRAINSResample)
            # (ESTO SE EJECUTA SIEMPRE, YA SEA MANUAL O AUTOMÁTICO)
            # ==========================================================
            # Preparar un volumen clonado vacío para recibir la nueva dosis deformada
            output_dose_name = f"{moving_dose.GetName()}_Resampled"
            volumesLogic = slicer.modules.volumes.logic()

            reference_volume = fixed_dose if fixed_dose else fixed_ct

            outputDose = volumesLogic.CloneVolume(slicer.mrmlScene, reference_volume, output_dose_name)
            outputDose.SetAttribute("DICOM.Modality", "RTDOSE")

            # Configurar el motor de re-muestreo pasándole el final_transform obtenido arriba
            resample_params = {
                "inputVolume": moving_dose.GetID(),
                "referenceVolume": reference_volume.GetID(),
                "outputVolume": outputDose.GetID(),
              #  "warpTransform": final_transform.GetID(),  # Aplicar el mismo movimiento de los huesos a la dosis
                "interpolationMode": "Linear",
                "pixelType": "float"
            }

            # INYECCIÓN MATEMÁTICA: Si se usó Auto-Registro, le pasamos el cálculo final
            # Si se eligió Solo Manual, le pasamos los movimientos de las barras directamente a la Dosis
            if not use_manual_only and final_transform:
                resample_params["warpTransform"] = final_transform.GetID()
            elif use_manual_only and is_manual_active:
                resample_params["warpTransform"] = manual_transform.GetID()

            cliNodeResample = slicer.cli.runSync(slicer.modules.brainsresample, None, resample_params)

            if cliNodeResample.GetStatus() & cliNodeResample.ErrorsMask:
                raise ValueError("The Dose resample (BRAINSResample) failed.")

            # ==========================================================
            # 8. ACTUALIZAR LA PANTALLA
            # ==========================================================
            # Enganchar el TAC Antiguo a la transformación final para que el usuario vea el resultado
            if not use_manual_only and final_transform:
                moving_ct.SetAndObserveTransformNodeID(final_transform.GetID())

            slicer.util.setSliceViewerLayers(background=fixed_ct, foreground=moving_ct, foregroundOpacity=0.5)

            # ==========================================================
            # 9. RETORNAR RESULTADOS A LA INTERFAZ (Dosis y Matriz)
            # ==========================================================
            # Evaluamos qué matriz de movimiento se usó realmente
            # (la automática de BRAINSFit o la manual de las barras)
            applied_transform = final_transform if not use_manual_only else manual_transform

            return outputDose, applied_transform

        finally:
            # ==========================================================
            # UX: RESTAURAR INTERFAZ (Incluso si hay un error)
            # ==========================================================
            progress.close()
            slicer.app.restoreOverrideCursor()  # Regresa el cursor a la normalidad

    def procesarDosis(self, dose_a_node, dose_b_node, ab, fx_a, fx_b, use_recovery, months, custom_name=""):
        import numpy as np


        # --- PASO A: Validaciones Clínicas ---
        if not dose_a_node or not dose_b_node:
            raise ValueError("Please select both dose matrices (RT1 y RT2).")
        if fx_a <= 0 or fx_b <= 0:
            raise ValueError("The number of fractions must be greater than zero.")

        #  Validación matricial para Alpha/Beta
        if np.any(ab <= 0):
            raise ValueError("The Alpha/Beta values must be greater than zero.")

        # --- PASO B: Extracción de Vóxeles ---
        array_a = slicer.util.arrayFromVolume(dose_a_node)
        array_b = slicer.util.arrayFromVolume(dose_b_node)

        if array_a.shape != array_b.shape:
            raise ValueError(
                f"The Matrix dimensions do not match..\nDose RT1: {array_a.shape}\nDose RT2: {array_b.shape}\nYou must register and resample the images beforehand.")

        # --- PASO C: Matemática Radiobiológica ---
        d_a = array_a / fx_a
        d_b = array_b / fx_b
        bed_a = array_a * (1.0 + (d_a / ab))
        bed_b = array_b * (1.0 + (d_b / ab))
        # bed_total = bed_a + bed_b
        #  eqd2_total = bed_total * (ab / (2.0 + ab))
        # --- Lógica de Recuperación (Misma de tu Streamlit) ---
        recovery = 0.0
        if use_recovery:
            if months < 6:
                recovery = 0.0
            elif months < 12:
                recovery = 0.25
            elif months < 24:
                recovery = 0.50
            else:
                recovery = 0.65

        # Calculamos el BED efectivo restando la recuperación
        effective_bed_a = bed_a * (1.0 - recovery)

        # Sumamos el BED viejo con descuento + el BED nuevo
        bed_total = effective_bed_a + bed_b
        eqd2_total = bed_total * (ab / (2.0 + ab))

        # --- PASO D: Retorno a Slicer ---
        volumesLogic = slicer.modules.volumes.logic()
        # nuevo_nombre = f"RadReirradiation_EQD2_Acumulado_ab{int(ab)}"

        # Ajuste de nomenclatura para evitar errores de conversión de matrices
        if custom_name:
            nuevo_nombre = custom_name
        else:
            nuevo_nombre = "RadReirradiation_EQD2_Accumulated_VoxelAB"

        eqd2_node = volumesLogic.CloneVolume(slicer.mrmlScene, dose_a_node, nuevo_nombre)
        eqd2_node.SetAttribute("DICOM.Modality", "RTDOSE")
        slicer.util.updateVolumeFromArray(eqd2_node, eqd2_total)

        # --- PASO E: AUTOMATIZACIÓN VISUAL ---
        # 1. Encontrar la dosis máxima para escalar los colores automáticamente
        dosis_maxima = np.max(eqd2_total)


        # 2. Configurar el "Display Node" (el pintor de Slicer)
        display_node = eqd2_node.GetDisplayNode()
        if display_node is None:
            eqd2_node.CreateDefaultDisplayNodes()
            display_node = eqd2_node.GetDisplayNode()

        # 3. Aplicar paleta de colores de dosis (Arcoíris)
        # display_node.SetAndObserveColorNodeID('vtkMRMLColorTableNodeRainbow')
        # ==========================================================
        # 3. CREAR Y ASIGNAR MAPA DE COLORES ESTILO "ECLIPSE TPS"
        # ==========================================================
        color_name = "Eclipse_Dose_Wash"
        color_node = slicer.mrmlScene.GetFirstNodeByName(color_name)

        # Si el mapa no existe en la escena, lo creamos desde cero
        if not color_node:
            color_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLColorTableNode", color_name)
            color_node.SetTypeToUser()
            color_node.SetNumberOfColors(256)

            # Usamos una función de transferencia para crear el degradado suave
            ctf = vtk.vtkColorTransferFunction()
            ctf.AddRGBPoint(0.00, 0.0, 0.0, 0.6)  # 0%   - Azul Oscuro (Bajas dosis)
            ctf.AddRGBPoint(0.25, 0.0, 0.8, 1.0)  # 25%  - Cyan
            ctf.AddRGBPoint(0.50, 0.0, 1.0, 0.0)  # 50%  - Verde
            ctf.AddRGBPoint(0.75, 1.0, 1.0, 0.0)  # 75%  - Amarillo
            ctf.AddRGBPoint(0.90, 1.0, 0.5, 0.0)  # 90%  - Naranja
            ctf.AddRGBPoint(1.00, 1.0, 0.0, 0.0)  # 100% - Rojo (Altas dosis)

            # Llenamos la paleta de Slicer con los 256 colores interpolados
            for i in range(256):
                r, g, b = ctf.GetColor(i / 255.0)
                color_node.SetColor(i, str(i), r, g, b, 1.0)  # El 1.0 es la opacidad base

        # Le aplicamos nuestro nuevo mapa de colores al volumen de dosis
        display_node.SetAndObserveColorNodeID(color_node.GetID())
        # ==========================================================

        # 4. Ajustar umbral: Hacer transparente todo lo que esté por debajo de 2 Gy
        umbral_minimo = 2.0
        display_node.SetAutoWindowLevel(False)
        display_node.SetWindowLevelMinMax(umbral_minimo, dosis_maxima)
        display_node.SetApplyThreshold(1)
        display_node.SetLowerThreshold(umbral_minimo)
        display_node.SetUpperThreshold(dosis_maxima)

        # 5. Inyectar automáticamente el mapa de calor sobre las vistas 2D
        slicer.util.setSliceViewerLayers(foreground=eqd2_node, foregroundOpacity=0.4)

        # 6. CREAR Y MOSTRAR LA LEYENDA (SCALAR BAR)
        try:
            # Invoca el motor de leyendas de Slicer y lo ancla a nuestro volumen
            color_legend = slicer.modules.colors.logic().AddDefaultColorLegendDisplayNode(eqd2_node)
            color_legend.SetTitleText("Dose EQD2 (Gy)")
        except Exception as e:
            # En caso de que se use una versión antigua de Slicer que no soporte este método
            print(f"Notice: The legend could not be generated automatically. {e}")

        return eqd2_node


# ==========================================================
# 4. PRUEBAS AUTOMATIZADAS
# ==========================================================
class RadReirradiationTest(ScriptedLoadableModuleTest):
    def setUp(self):
        slicer.mrmlScene.Clear()

    def runTest(self):
        pass
