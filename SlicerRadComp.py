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
class SlicerRadComp(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "RadComp Reirradiation analysis"  # Nombre que verás en Slicer
        self.parent.categories = ["Radiotherapy"]  # Se creará esta categoría en el menú
        self.parent.dependencies = []
        self.parent.contributors = ["Luis Paredes, Clinical Medical Physicist "]
        self.parent.helpText = "A clinical tool for Reirradiation calculations, visit the online version https://radcomp.streamlit.app ."
        self.parent.acknowledgementText = "Basado en la librería radcomp."


# ==========================================================
# 2. INTERFAZ GRÁFICA (WIDGET / GUI)
# ==========================================================
class SlicerRadCompWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = SlicerRadCompLogic()

        # --- Collapsible Panel ---
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Calculation Settings"  # Mismo nombre que el sidebar de Streamlit
        self.layout.addWidget(parametersCollapsibleButton)
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        # --- 1. Dose Volume Selectors ---
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
        parametersFormLayout.addRow("Dose (.RD) Previous Treatment (RT1): ", self.dose_a_selector)

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
        parametersFormLayout.addRow("Dose (.RD) Planned Treatment (RT2): ", self.dose_b_selector)

        # --- 2. Radiobiological Parameters (Smart Defaults) ---
        # SpinBox for Alpha/Beta Ratio (ab)
        self.ab_spinbox = qt.QDoubleSpinBox()
        self.ab_spinbox.setValue(3.0)
        self.ab_spinbox.setDecimals(1)
        self.ab_spinbox.setToolTip("Alpha/Beta Ratio of the tissue under study (Gy).")
        parametersFormLayout.addRow("Alpha/Beta Ratio (Gy): ", self.ab_spinbox)

        # SpinBox for fractions_a (RT1)
        self.fractions_a_spinbox = qt.QSpinBox()
        self.fractions_a_spinbox.setValue(25)  # Valor por defecto de tu main.py
        self.fractions_a_spinbox.setMaximum(100)
        parametersFormLayout.addRow("Number of Fractions RT1: ", self.fractions_a_spinbox)

        # SpinBox for fractions_b (RT2)
        self.fractions_b_spinbox = qt.QSpinBox()
        self.fractions_b_spinbox.setValue(10)  # Valor por defecto de tu main.py para B
        self.fractions_b_spinbox.setMaximum(100)
        parametersFormLayout.addRow("Number of Fractions RT2: ", self.fractions_b_spinbox)

        # --- 3. Time / Recovery Factor (Basado en RadComp Streamlit) ---
        self.recovery_checkbox = qt.QCheckBox("Enable Partial Recovery (Time-based model)")
        self.recovery_checkbox.setChecked(False)
        self.recovery_checkbox.setToolTip("The BED contribution from the previous irradiation course is reduced according its recovery assumption before being combined with the new treatment")
        parametersFormLayout.addRow(self.recovery_checkbox)

        self.months_spinbox = qt.QSpinBox()
        self.months_spinbox.setRange(0, 100)
        self.months_spinbox.setValue(12)
        self.months_spinbox.setSuffix(" months")
        self.months_spinbox.setEnabled(False)  # Inicia apagado hasta que marquen la casilla
        parametersFormLayout.addRow("Time interval (RT1 to RT2): ", self.months_spinbox)

        # Conectar la casilla para que encienda o apague el selector de meses
        self.recovery_checkbox.connect('toggled(bool)', self.months_spinbox.setEnabled)

        # --- 4. Configuración de Salida ---
        self.output_name_input = qt.QLineEdit()
        self.output_name_input.setPlaceholderText("Optional: Custom name for the new volume...")
        self.output_name_input.setToolTip("If you leave it blank, it will use the default name..")
        parametersFormLayout.addRow("Accumulated Dose Volume Name: ", self.output_name_input)

        # --- Apply Button ---
        self.applyButton = qt.QPushButton("Calculate Cumulative EQD2 Dose")
        self.applyButton.toolTip = "Execute the voxel-by-voxel BED/EQD2 accumulation."
        self.applyButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        parametersFormLayout.addRow(self.applyButton)

        # Connect button to function
        self.applyButton.connect('clicked(bool)', self.onApplyButton)

        # Empuja todo hacia arriba para que quede ordenado
        self.layout.addStretch(1)

    def onApplyButton(self):
        # 1. Recolectar los datos que el usuario puso en la interfaz
        dose_a_node = self.dose_a_selector.currentNode()
        dose_b_node = self.dose_b_selector.currentNode()
        ab = self.ab_spinbox.value
        fx_a = self.fractions_a_spinbox.value
        fx_b = self.fractions_b_spinbox.value

        # Nuevos valores de tiempo
        use_recovery = self.recovery_checkbox.isChecked()
        months = self.months_spinbox.value

        # Leemos el nombre personalizado
        custom_name = self.output_name_input.text.strip()

        # 2. Enviar los datos a la Lógica (el cerebro) envueltos en un bloque de seguridad
        try:
            # Mostramos un mensaje temporal en la barra de estado de Slicer
            slicer.util.showStatusMessage("Calculating BED/EQD2 voxel by voxel...")

            # ¡Llamamos a la magia!
            self.logic.procesarDosis(dose_a_node, dose_b_node, ab, fx_a, fx_b, use_recovery, months,custom_name)

            slicer.util.showStatusMessage("¡Calculation completed!")
            slicer.util.infoDisplay("¡Cálculation of accumulated EQD2 completed con successfully!", windowTitle="RadComp")
        except Exception as e:
            # Si algo falla (ej. tamaños distintos), Slicer no se cierra, solo muestra un aviso
            slicer.util.errorDisplay(f"Calculation Error:\n{str(e)}", windowTitle="RadComp Error")


# ==========================================================
# 3. LÓGICA MATEMÁTICA (CEREBRO)
# ==========================================================

class SlicerRadCompLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)

    def procesarDosis(self, dose_a_node, dose_b_node, ab, fx_a, fx_b, use_recovery, months, custom_name=""):
        import numpy as np

        # --- PASO A: Validaciones Clínicas ---
        if not dose_a_node or not dose_b_node:
            raise ValueError("Please select both dose matrices (RT1 y RT2).")
        if fx_a <= 0 or fx_b <= 0:
            raise ValueError("The number of fractions must be greater than zero.")
        if ab <= 0:
            raise ValueError("The Alpha/Beta value must be greater than zero.")

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
       # nuevo_nombre = f"RadComp_EQD2_Acumulado_ab{int(ab)}"

        # Aquí aplicamos la lógica del nombre
        if custom_name:
            nuevo_nombre = custom_name
        else:
            nuevo_nombre = f"RadComp_EQD2_Accumulated_ab{int(ab)}"

        eqd2_node = volumesLogic.CloneVolume(slicer.mrmlScene, dose_a_node, nuevo_nombre)
        slicer.util.updateVolumeFromArray(eqd2_node, eqd2_total)

        # --- PASO E: AUTOMATIZACIÓN VISUAL (MAGIA UI) ---
        # 1. Encontrar la dosis máxima para escalar los colores automáticamente
        dosis_maxima = np.max(eqd2_total)

        # 2. Configurar el "Display Node" (el pintor de Slicer)
        display_node = eqd2_node.GetDisplayNode()
        if display_node is None:
            eqd2_node.CreateDefaultDisplayNodes()
            display_node = eqd2_node.GetDisplayNode()

        # 3. Aplicar paleta de colores de dosis (Arcoíris)
        display_node.SetAndObserveColorNodeID('vtkMRMLColorTableNodeRainbow')

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
class SlicerRadCompTest(ScriptedLoadableModuleTest):
    def setUp(self):
        slicer.mrmlScene.Clear()

    def runTest(self):
        pass