# ---------------------------------------------------------------------------------
# 	QKeithleySweep -> QVisaApplication
#	Copyright (C) 2019 Michael Winters
#	github: https://github.com/mesoic
#	email:  mesoic@protonmail.com
# ---------------------------------------------------------------------------------
# 
# 	Permission is hereby granted, free of charge, to any person obtaining a copy
# 	of this software and associated documentation files (the "Software"), to deal
# 	in the Software without restriction, including without limitation the rights
# 	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# 	copies of the Software, and to permit persons to whom the Software is
# 	furnished to do so, subject to the following conditions:
# 	
# 	The above copyright notice and this permission notice shall be included in all
# 	copies or substantial portions of the Software.
# 	
# 	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# 	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# 	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# 	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# 	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# 	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# 	SOFTWARE.
#

#!/usr/bin/env python 
import os
import sys
import time
import threading

# Import numpy
import numpy as np

# Import QVisaApplication
from PyQtVisa import QVisaApplication

# Import PyQtVisa widgets
from PyQtVisa.widgets import QVisaUnitSelector
from PyQtVisa.widgets import QVisaDynamicPlot 

# Import QT backends
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel, QLineEdit, QStackedWidget, QSizePolicy
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject
from PyQt5.QtGui import QIcon

# Container class to construct sweep measurement widget
class QKeithleySweep(QVisaApplication.QVisaApplication):

	def __init__(self, _config):

		# Inherits QVisaApplication -> QWidget
		super(QKeithleySweep, self).__init__(_config)

		# Generate Main Layout
		self.gen_main_layout()


	#####################################
	# APPLICATION HELPER METHODS
	#

	# Wrapper method to get keitley write handle
	# 	Returns the pyVisaDevice object
	def keithley(self, __widget__):
		return self.get_device_by_name( __widget__.currentText() )

	# Method to refresh the widget
	def refresh(self):
	
		# If add insturments have been initialized
		if self.get_devices() is not None:

			# Reset the widget and add insturments
			self.sweep_inst.refresh( self )
			self.step_inst.refresh( self )

			# Update sweep parameters and enable output button
			self.meas_button.setEnabled(True)
			self.update_meas_params()

		else: 

			# Disable output button
			self.meas_button.setEnabled(False)	

	# Method to set sweep parameters
	def set_sweep_params(self, start, stop, npts):

		# No hysteresis	
		if self.sweep_hist.currentText() == "None": 	
			sp = np.linspace(float(start), float(stop), int(npts) )
			self._set_app_metadata("__sweep__", sp)

		# Prepare reverse sweep
		if self.sweep_hist.currentText() == "Reverse-sweep":

			# Sweep centered hysteresis
			sp = np.linspace(float(start), float(stop), int(npts) )
			sp = np.concatenate( (sp, sp[-2::-1]) )
			self._set_app_metadata("__sweep__", sp)

		# Prepare a zero centered hysteresis
		if self.sweep_hist.currentText() == "Zero-centered":

			# Create a linspace
			sp = np.linspace(float(start), float(stop), int(npts) )
			
			# Extract positive slice
			pos = np.where(sp > 0, sp, np.nan) 	
			pos = pos[~np.isnan(pos)]

			# Extract negative slice
			neg = np.where(sp < 0, sp, np.nan) 
			neg = neg[~np.isnan(neg)]

			# Create the zero centered hysteresis re-insert zeros
			# Forward sweep, zero crossing
			if (start < 0.) and (stop > 0.) and (start < stop):
				sp = np.concatenate( ([0.0], pos, pos[-2::-1], [0.0], neg[::-1], neg[1::], [0.0]) )

		 	# Reverse sweep, zero crossing
			elif  (start > 0.) and (stop < 0.) and (start > stop):	
				sp = np.concatenate( ([0.0], neg, neg[-2::-1], [0.0], pos[::-1], pos[1::], [0.0]) )
				print(sp)				

			# If not zero crossing, default to "Reverse-sweep" case
			else: 	
				sp = np.concatenate( (sp, sp[-2::-1]) )	

			# Set meta field
			self._set_app_metadata( "__sweep__", sp)


	# Method to set step parameters
	def set_step_params(self, start, stop, npts):

		# No hysteresis	
		sp = np.linspace(float(start), float(stop), int(npts) )
		self._set_app_metadata("__step__", sp)


	#####################################
	# MAIN LAYOUT
	#

	def gen_main_layout(self):
	
		# Create Icon for QMessageBox
		self._set_icon( QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico")))	
		
		# Create layout objects and set layout
		self.layout = QHBoxLayout()
		self.layout.addWidget(self.gen_main_ctrl(), 1)
		self.layout.addWidget(self.gen_main_plot(), 3)
		self.setLayout(self.layout)

	#####################################
	# MAIN LAYOUT
	#

	# Main controls: 
	# 	a) Measure button and state machine
	# 	b) V-Step mode on/off state machine
	#	c) IV-sweep and V-step configure pages
	#	d) Save button

	def gen_main_ctrl(self):

		# Main control widget
		self.meas_ctrl = QWidget()
		self.meas_ctrl_layout = QVBoxLayout()

		#####################################
		# MEASURE STATE MACHINE AND BUTTON
		#

		# Measurement Button. This will be a state machine which 
		# alternates between 'measure' and 'abort' states
		self.meas_state  = QStateMachine()
		self.meas_button = QPushButton()

		self.meas_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create measurement states
		self.meas_run  = QState()
		self.meas_stop = QState()

		# Assign state properties and transitions
		self.meas_run.assignProperty(self.meas_button, 'text', 'Abort Sweep')
		self.meas_run.addTransition(self.meas_button.clicked, self.meas_stop)
		self.meas_run.entered.connect(self.exec_meas_run)

		self.meas_stop.assignProperty(self.meas_button, 'text', 'Measure Sweep')
		self.meas_stop.addTransition(self.meas_button.clicked, self.meas_run)
		self.meas_stop.entered.connect(self.exec_meas_stop)

		# Add states, set initial state, and state machine
		self.meas_state.addState(self.meas_run)
		self.meas_state.addState(self.meas_stop)
		self.meas_state.setInitialState(self.meas_stop)
		self.meas_state.start()
	
		# Meas pages
		self.meas_pages = QStackedWidget()
		self.meas_pages.addWidget(self.gen_sweep_ctrl())
		self.meas_pages.addWidget(self.gen_step_ctrl())

		# Meta widget for trace description
		self.meta_widget_label = QLabel("<b>Trace Description</b>")
		self.meta_widget = self._gen_meta_widget()
		self.meta_widget.set_meta_subkey("__desc__")

		# Save widget
		self.save_widget = self._gen_save_widget()

		# Pack widgets into layout
		self.meas_ctrl_layout.addWidget(self.meas_button)
		self.meas_ctrl_layout.addWidget(self.gen_config_ctrl())
		self.meas_ctrl_layout.addWidget(self.meas_pages)

		# Add save widget
		self.meas_ctrl_layout.addStretch(1)
		self.meas_ctrl_layout.addWidget(self.meta_widget_label)
		self.meas_ctrl_layout.addWidget(self.meta_widget)
		self.meas_ctrl_layout.addWidget(self.save_widget)

		# Set layout and return widget reference
		self.meas_ctrl.setLayout(self.meas_ctrl_layout)
		return self.meas_ctrl


	#####################################
	# CONFIGURE WIDGET
	#

	def gen_config_ctrl(self):

		self.meas_config = QWidget()
		self.meas_config_layout = QVBoxLayout()

		# Current/Voltage Sweep Mode 
		self.meas_config_page_label = QLabel("<b>Configure Parameters</b>")
		self.meas_config_page = QComboBox()
		self.meas_config_page.setFixedWidth(200)
		self.meas_config_page.addItems(["IV-sweep", "V-step"])	
		self.meas_config_page.currentTextChanged.connect(self.update_config_page)

		# Add some space for layout clarity
		self.meas_config_layout.setContentsMargins(0,10,0,10)
		self.meas_config_layout.addWidget(self._gen_vbox_widget([self.meas_config_page_label, self.meas_config_page]))

		# Pack config layout and return reference
		self.meas_config.setLayout(self.meas_config_layout)
		return self.meas_config


	# Sweep control layout
	def gen_sweep_ctrl(self): 

		self.sweep_ctrl = QWidget()
		self.sweep_ctrl_layout = QVBoxLayout()
		
		# Main control label
		self.sweep_ctrl_label = QLabel("<b>IV-sweep Parameters</b>")
	
		#####################################
		#  SWEEP INST SELECT
		#

		# Insturement selector and save widget
		self.sweep_inst_label = QLabel("Select Device")
		self.sweep_inst = self._gen_device_select()
		self.sweep_inst.setFixedWidth(200)

		#####################################
		#  SWEEP MEASUREMENT CONFIGURATION
		#
		
		# Current/Voltage Sweep Mode 
		self.sweep_src_label = QLabel("Source Type")
		self.sweep_src = QComboBox()
		self.sweep_src.setFixedWidth(200)
		self.sweep_src.addItems(["Voltage", "Current"])	
		self.sweep_src.currentTextChanged.connect(self.update_sweep_ctrl)

		# Generate voltage and current source widgets
		self.gen_voltage_sweep()		# self.voltage_sweep
		self.gen_current_sweep()		# self.current_sweep

		# Add to stacked widget
		self.sweep_pages = QStackedWidget()	
		self.sweep_pages.addWidget(self.voltage_sweep)
		self.sweep_pages.addWidget(self.current_sweep)
		self.sweep_pages.setCurrentIndex(0)

		# Hysteresis mode
		self.sweep_hist_label = QLabel("Hysteresis Mode")
		self.sweep_hist = QComboBox()
		self.sweep_hist.setFixedWidth(200)
		self.sweep_hist.addItems(["None", "Reverse-sweep", "Zero-centered"])	

		#####################################
		#  ADD CONTROLS
		#

		# Sweep configuration controls
		self.sweep_ctrl_layout.addWidget(self.sweep_ctrl_label)
		self.sweep_ctrl_layout.addWidget(self._gen_hbox_widget([self.sweep_inst,self.sweep_inst_label]))
		self.sweep_ctrl_layout.addWidget(self._gen_hbox_widget([self.sweep_src, self.sweep_src_label]))
		self.sweep_ctrl_layout.addWidget(self._gen_hbox_widget([self.sweep_hist, self.sweep_hist_label]))
		self.sweep_ctrl_layout.addWidget(self.sweep_pages)
		
		# Positioning
		self.sweep_ctrl.setLayout(self.sweep_ctrl_layout)
		return self.sweep_ctrl

	# Step control layout	
	def gen_step_ctrl(self):
	
		self.step_ctrl = QWidget()
		self.step_ctrl_layout = QVBoxLayout()

		# Step control label
		self.step_ctrl_label = QLabel("<b>V-step Parameters</b>")
	
		# Voltage step instruement selector
		self.step_inst_label = QLabel("Select Device")
		self.step_inst = self._gen_device_select()
		self.step_inst.setFixedWidth(200)

		# Generate voltage and current source widgets
		self.gen_voltage_step()		# self.voltage_step

		# Pack widgets
		self.step_ctrl_layout.addWidget(self.step_ctrl_label)
		self.step_ctrl_layout.addWidget(self._gen_hbox_widget([self.step_inst,self.step_inst_label]))
		self.step_ctrl_layout.addWidget(self.voltage_step)

		# Set layout and return reference
		self.step_ctrl.setLayout(self.step_ctrl_layout)		
		return self.step_ctrl	


	# Generate voltage sweep widget
	def gen_voltage_sweep(self):
	
		# New QWidget
		self.voltage_sweep = QWidget()
		self.voltage_sweep_layout = QVBoxLayout()
	
		# Sweep Start
		self.voltage_sweep_start_config={
			"unit" 		: "V",
			"min"		: "u",
			"max"		: "",
			"label"		: "Sweep Start (V)",
			"limit"		: 20.0,
			"signed"	: True,
			"default"	: [-1.0, ""]
		} 
		self.voltage_sweep_start = QVisaUnitSelector.QVisaUnitSelector(self.voltage_sweep_start_config)

		# Sweep Stop
		self.voltage_sweep_stop_config={
			"unit" 		: "V",
			"min"		: "u",
			"max"		: "",
			"label"		: "Sweep Stop (V)",
			"limit"		: 20.0,
			"signed"	: True,
			"default"	: [1.0, ""]
		} 
		self.voltage_sweep_stop = QVisaUnitSelector.QVisaUnitSelector(self.voltage_sweep_stop_config)

		# Compliance Spinbox
		self.voltage_sweep_cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (A)",
			"limit"		: 1.0, 
			"signed"	: False,
			"default"	: [100, "m"]
		} 
		self.voltage_sweep_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.voltage_sweep_cmpl_config)	

		# Number of points
		self.voltage_sweep_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"limit"		: 256.0, 
			"signed"	: False,
			"default"	: [11.0]
		}
		self.voltage_sweep_npts = QVisaUnitSelector.QVisaUnitSelector(self.voltage_sweep_npts_config)

		# Measurement Delay
		self.voltage_sweep_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: [0.1]
		}
		self.voltage_sweep_delay = QVisaUnitSelector.QVisaUnitSelector(self.voltage_sweep_delay_config)


		# Pack selectors into layout
		self.voltage_sweep_layout.addWidget(self.voltage_sweep_start)
		self.voltage_sweep_layout.addWidget(self.voltage_sweep_stop)
		self.voltage_sweep_layout.addWidget(self.voltage_sweep_cmpl)
		self.voltage_sweep_layout.addWidget(self.voltage_sweep_npts)
		self.voltage_sweep_layout.addWidget(self.voltage_sweep_delay)
		self.voltage_sweep_layout.setContentsMargins(0,0,0,0)

		# Set layout 
		self.voltage_sweep.setLayout(self.voltage_sweep_layout)	


	# Generate current sweep widget
	def gen_current_sweep(self):
	
		# New QWidget
		self.current_sweep = QWidget()
		self.current_sweep_layout = QVBoxLayout()
	
		# Sweep Start
		self.current_sweep_start_config={
			"unit" 		: "A",
			"min"		: "u",
			"max"		: "",
			"label"		: "Sweep Start (A)",
			"limit"		: 1.0,
			"signed"	: True,
			"default"	: [0.0, "m"]
		} 
		self.current_sweep_start = QVisaUnitSelector.QVisaUnitSelector(self.current_sweep_start_config)

		# Sweep Stop
		self.current_sweep_stop_config={
			"unit" 		: "A",
			"min"		: "u",
			"max"		: "",
			"label"		: "Sweep Stop (A)",
			"limit"		: 1.0,
			"signed"	: True,
			"default"	: [100, "m"]
		} 
		self.current_sweep_stop = QVisaUnitSelector.QVisaUnitSelector(self.current_sweep_stop_config)

		# Compliance Spinbox
		self.current_sweep_cmpl_config={
			"unit" 		: "V", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (V)",
			"limit"		: 20, 
			"signed"	: False,
			"default"	: [1.0, ""]
		} 
		self.current_sweep_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.current_sweep_cmpl_config)

		# Number of points
		self.current_sweep_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"limit"		: 256.0, 
			"signed"	: False,
			"default"	: [11.0]
		}
		self.current_sweep_npts = QVisaUnitSelector.QVisaUnitSelector(self.current_sweep_npts_config)

		# Measurement Delay
		self.current_sweep_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: [0.1]
		}
		self.current_sweep_delay = QVisaUnitSelector.QVisaUnitSelector(self.current_sweep_delay_config)			

		# Pack selectors into layout
		self.current_sweep_layout.addWidget(self.current_sweep_start)
		self.current_sweep_layout.addWidget(self.current_sweep_stop)
		self.current_sweep_layout.addWidget(self.current_sweep_cmpl)
		self.current_sweep_layout.addWidget(self.current_sweep_npts)
		self.current_sweep_layout.addWidget(self.current_sweep_delay)
		self.current_sweep_layout.setContentsMargins(0,0,0,0)

		# Set layout 
		self.current_sweep.setLayout(self.current_sweep_layout)	


	# Generate voltage step widget
	def gen_voltage_step(self):
	
		# New QWidget
		self.voltage_step= QWidget()
		self.voltage_step_layout = QVBoxLayout()
	
		# Voltage step control state maching
		self.voltage_step_state = QStateMachine()
		self.voltage_step_button = QPushButton()
		self.voltage_step_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create measurement states
		self.voltage_step_on  = QState()
		self.voltage_step_off = QState()

		# Assign state properties and transitions
		self.voltage_step_on.assignProperty(self.voltage_step_button, 'text', 'V-Step ON')
		self.voltage_step_on.addTransition(self.voltage_step_button.clicked, self.voltage_step_off)
		self.voltage_step_on.entered.connect(self.exec_voltage_step_on)

		self.voltage_step_off.assignProperty(self.voltage_step_button, 'text', 'V-Step OFF')
		self.voltage_step_off.addTransition(self.voltage_step_button.clicked, self.voltage_step_on)
		self.voltage_step_off.entered.connect(self.exec_voltage_step_off)

		# Add states, set initial state, and state machine
		self.voltage_step_state.addState(self.voltage_step_on)
		self.voltage_step_state.addState(self.voltage_step_off)
		self.voltage_step_state.setInitialState(self.voltage_step_off)
		self.voltage_step_state.start()


		# Sweep Start
		self.voltage_step_start_config={
			"unit" 		: "V",
			"min"		: "u",
			"max"		: "",
			"label"		: "Step Start (V)",
			"limit"		: 20.0,
			"signed"	: True,
			"default"	: [0.0, ""]
		} 
		self.voltage_step_start = QVisaUnitSelector.QVisaUnitSelector(self.voltage_step_start_config)

		# Sweep Stop
		self.voltage_step_stop_config={
			"unit" 		: "V",
			"min"		: "u",
			"max"		: "",
			"label"		: "Step Stop (V)",
			"limit"		: 20.0,
			"signed"	: True,
			"default"	: [1.0, ""]
		} 
		self.voltage_step_stop = QVisaUnitSelector.QVisaUnitSelector(self.voltage_step_stop_config)

		# Compliance Spinbox
		self.voltage_step_cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (A)",
			"limit"		: 1.0, 
			"signed"	: False,
			"default"	: [100, "m"]
		} 
		self.voltage_step_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.voltage_step_cmpl_config)	

		# Number of points
		self.voltage_step_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"limit"		: 256.0, 
			"signed"	: False,
			"default"	: [5]
		}
		self.voltage_step_npts = QVisaUnitSelector.QVisaUnitSelector(self.voltage_step_npts_config)

		# Pack selectors into layout
		self.voltage_step_layout.addWidget(self.voltage_step_start)
		self.voltage_step_layout.addWidget(self.voltage_step_stop)
		self.voltage_step_layout.addWidget(self.voltage_step_cmpl)
		self.voltage_step_layout.addWidget(self.voltage_step_npts)
		self.voltage_step_layout.addWidget(self.voltage_step_button)
		self.voltage_step_layout.addStretch(1)
		self.voltage_step_layout.setContentsMargins(0,0,0,0)

		# Set layout 
		self.voltage_step.setLayout(self.voltage_step_layout)		


	# Ádd dynamic plot
	def gen_main_plot(self): 		

		# Create QVisaDynamicPlot object (inherits QWidget) 
		self.plot = QVisaDynamicPlot.QVisaDynamicPlot(self)
		self.plot.add_subplot(111)
		self.plot.set_axes_labels("111", "Voltage (V)", "Current (A)")
		self.plot.add_origin_lines("111", "both")

		# Refresh canvas
		self.plot.refresh_canvas(supress_warning=True)		

		# Sync plot clear data button with application data
		self.plot.sync_application_data(True)

		# Sync meta widget when clearing data
		self.plot.set_mpl_refresh_callback("_sync_meta_widget_to_data_object")

		# Return the plot
		return self.plot

	# Sync meta widget
	def _sync_meta_widget_to_data_object(self):

		# Application keys
		_data_keys = self._get_data_object().keys()
		_widget_keys = self.meta_widget.get_meta_keys()

		# Check if widget keys are not in data keys
		for _key in _widget_keys:
			
			# If not then delete the key from meta_widget
			if _key not in _data_keys:

				self.meta_widget.del_meta_key(_key)


	#####################################
	#  UPDATE CONFIG PAGE 
	#	
	def update_config_page(self):

		if self.meas_config_page.currentText() == "IV-sweep":
			self.meas_pages.setCurrentIndex(0)

		if self.meas_config_page.currentText() == "V-step":
			self.meas_pages.setCurrentIndex(1)


	#####################################
	#  SWEEP CONTROL UPDATE METHODS
	#	

	# Sweep control dynamic update
	def update_sweep_ctrl(self):

		# Switch to voltage sweep page
		if self.sweep_src.currentText() == "Voltage":
			self.sweep_pages.setCurrentIndex(0)
			self.update_meas_params()

		# Switch to current sweep page
		if self.sweep_src.currentText() == "Current":		
			self.sweep_pages.setCurrentIndex(1)
			self.update_meas_params()

	# Create Measurement 
	def update_meas_params(self):

		# Set up v-source(i-compliance) on keithley 
		if self.sweep_src.currentText() == "Voltage":
			
			# Set sweeep paramaters
			self.set_sweep_params(
				self.voltage_sweep_start.value(), 
				self.voltage_sweep_stop.value(), 
				self.voltage_sweep_npts.value())

			# Set keithley as voltage source
			if self.keithley(self.sweep_inst) is not None:
	
				self.keithley(self.sweep_inst).voltage_src()
				self.keithley(self.sweep_inst).set_voltage(0.0)
				self.keithley(self.sweep_inst).current_cmp(self.voltage_sweep_cmpl.value())
	

		# Set up i-source(v-compliance) on keithley 
		if self.sweep_src.currentText() == "Current":

			# Set sweeep paramaters
			self.set_sweep_params(
				self.current_sweep_start.value(), 
				self.current_sweep_stop.value(), 
				self.current_sweep_npts.value())

	
			# Set keithley as voltage source
			if self.keithley(self.sweep_inst) is not None:
			
				self.keithley(self.sweep_inst).current_src()
				self.keithley(self.sweep_inst).set_current(0.0)
				self.keithley(self.sweep_inst).voltage_cmp(self.current_sweep_cmpl.value())


		# Set sweeep paramaters
		self.set_step_params(
			self.voltage_step_start.value(), 
			self.voltage_step_stop.value(), 
			self.voltage_step_npts.value())

		# Set keithley as voltage source
		if self.keithley(self.step_inst) is not None:
	
			self.keithley(self.step_inst).voltage_src()
			self.keithley(self.step_inst).set_voltage(0.0)
			self.keithley(self.step_inst).current_cmp(self.voltage_step_cmpl.value())		

	#####################################
	#  MEASUREMENT EXECUTION THREADS
	#		

	# Function we run when we enter run state
	def exec_voltage_step_on(self):

		# Update UI button to abort 
		self.voltage_step_button.setStyleSheet(
			"background-color: #cce6ff; border-style: solid; border-width: 1px; border-color: #1a75ff; padding: 7px;")

		# Check if no insturments are initialized
		if self.sweep_inst.currentText() == "" and self.step_inst.currentText() == "":

			# Message box to warn the user
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("No devices initialized")
			msg.setWindowTitle("QKeithleySweep")
			msg.setWindowIcon(self._icon)
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()

			# Set app meta and revert state
			self._set_app_metadata("__exec_voltage_step__", False)
			self.voltage_step_button.click()

		# Check if the same insturment is initialized
		elif self.sweep_inst.currentText() == self.step_inst.currentText():

			# Message box to warn the user
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Same device %s selected for sweep and step parameters. Proceed?"%self.step_inst.currentText())
			msg.setWindowTitle("QKeithleySweep")
			msg.setWindowIcon(self._icon)
			msg.setStandardButtons(QMessageBox.Ok)
			msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			self.msg_clear = msg.exec_()

			# Expose this for testing
			if self.msg_clear == QMessageBox.Yes:
				self._set_app_metadata("__exec_voltage_step__", True)

			else:	
				self._set_app_metadata("__exec_voltage_step__", False)
				self.voltage_step_button.click()

		else:
			self._set_app_metadata("__exec_voltage_step__", True)


	# Function we run when we enter run state
	def exec_voltage_step_off(self):

		# Update UI button to abort 
		self.voltage_step_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		self._set_app_metadata("__exec_voltage_step__", False)

	
	# Execute Sweep-Step Measurement
	def exec_sweep_step_thread(self):

		# Generate data key 
		data = self._get_data_object()
		key  = data.add_hash_key("iv-sweep-v-step")

		# Add data fields to key	
		data.set_subkeys(key, ["t", "V0", "I0", "P0", "V1", "I1", "P1"])
		data.set_metadata(key, "__type__", "iv-sweep-v-step")

		# Add key to meta widget
		self.meta_widget.add_meta_key(key)

		# Generate function pointer for voltage/current mode
		if self.sweep_src.currentText() == "Voltage":
			__func__  = self.keithley(self.sweep_inst).set_voltage
			__delay__ = self.voltage_sweep_delay.value()

		if self.sweep_src.currentText() == "Current":
			__func__ = self.keithley(self.sweep_inst).set_current
			__delay__ = self.current_sweep_delay.value()

		# Clear plot and zero arrays
		start  = time.time()

		# Output on
		self.keithley(self.step_inst).output_on()
		self.keithley(self.sweep_inst).output_on()

		# Use generator function so all traces have same color
		_c = self.plot.gen_next_color()
		_handle_index = 0 

		# Loop through step variables
		for _step in self._get_app_metadata("__step__"):

			# Set step voltage
			self.keithley(self.step_inst).set_voltage(_step)
			self.plot.add_axes_handle("111", key, _color=_c)

			# Bias settle
			if __delay__ != 0: 
				time.sleep(__delay__)

			# Loop through sweep variables
			for _bias in self._get_app_metadata("__sweep__"):

				# If thread is running
				if self.thread_running:

					# Set voltage/current bias
					__func__(_bias)			

					# Get data from buffer
					_b0 = self.keithley(self.sweep_inst).meas().split(",")	
					_b1 = self.keithley(self.step_inst).meas().split(",")


					if __delay__ != 0: 
						time.sleep(__delay__)

					# Extract data from buffer
					_now = float(time.time() - start)

					# Append measured values to data arrays	
					data.append_subkey_data(key,"t", _now )
					data.append_subkey_data(key,"V0", float(_b0[0]) )
					data.append_subkey_data(key,"I0", float(_b0[1]) )
					data.append_subkey_data(key,"P0", float(_b0[0]) * float(_b0[1]) )
					data.append_subkey_data(key,"V1", float(_b1[0]) )
					data.append_subkey_data(key,"I1", float(_b1[1]) )
					data.append_subkey_data(key,"P1", float(_b1[0]) * float(_b1[1]) )

					# Add data to plot
					self.plot.append_handle_data("111", key, float(_b0[0]), float(_b0[1]), _handle_index)
					self.plot.update_canvas()
			
			# Increment handle index
			_handle_index += 1
	

		# Reset Keithleys
		__func__(0.0)
		self.keithley(self.step_inst).set_voltage(0.0)
		self.keithley(self.step_inst).output_off()
		self.keithley(self.sweep_inst).output_off()
		
		# Reset sweep control and update measurement state to stop. 
		# Post a button click event to the QStateMachine to trigger 
		# a state transition if thread is still running (not aborted)
		if self.thread_running:
			self.meas_button.click()			


	# Execute Sweep Measurement
	def exec_sweep_thread(self):

		# Generate data key 
		data = self._get_data_object()
		key  = data.add_hash_key("iv-sweep")

		# Add data fields to key	
		data.set_subkeys(key, ["t", "V", "I", "P"])
		data.set_metadata(key, "__type__", "iv-sweep")

		# Add key to meta widget
		self.meta_widget.add_meta_key(key)

		# Generate function pointer for voltage/current mode
		if self.sweep_src.currentText() == "Voltage":
			__func__  = self.keithley(self.sweep_inst).set_voltage
			__delay__ = self.voltage_sweep_delay.value()

		if self.sweep_src.currentText() == "Current":
			__func__ = self.keithley(self.sweep_inst).set_current
			__delay__ = self.current_sweep_delay.value()

		# Clear plot and zero arrays
		handle = self.plot.add_axes_handle("111", key)
		start  = time.time()
		
		# Output on
		self.keithley(self.sweep_inst).output_on()

		# Loop through sweep variables
		for _bias in self._get_app_metadata("__sweep__"):

			# If thread is running
			if self.thread_running:

				# Set voltage/current bias
				__func__(_bias)			

				# Get data from buffer
				_b = self.keithley(self.sweep_inst).meas().split(",")
		
				if __delay__ != 0: 
					time.sleep(__delay__)

				# Extract data from buffer
				_now = float(time.time() - start)

				# Append measured values to data arrays	
				data.append_subkey_data(key,"t", _now )
				data.append_subkey_data(key,"V", float(_b[0]) )
				data.append_subkey_data(key,"I", float(_b[1]) )
				data.append_subkey_data(key,"P", float(_b[0]) * float(_b[1]) )

				self.plot.append_handle_data("111", key, float(_b[0]), float(_b[1]))
				self.plot.update_canvas()	
		
		# Reset Keithley
		__func__(0.0)
		self.keithley(self.sweep_inst).output_off()
		
		# Reset sweep control and update measurement state to stop. 
		# Post a button click event to the QStateMachine to trigger 
		# a state transition if thread is still running (not aborted)
		if self.thread_running:
			self.meas_button.click()

	# Function we run when we enter run state
	def exec_meas_run(self):

		# Update sweep and step params
		self.update_meas_params()

		# For startup protection
		if self.keithley(self.sweep_inst) is not None:

			# Update UI button to abort 
			self.meas_button.setStyleSheet(
				"background-color: #ffcccc; border-style: solid; border-width: 1px; border-color: #800000; padding: 7px;")

			# Disable controls
			self.sweep_src.setEnabled(False)
			self.sweep_inst.setEnabled(False)
			self.save_widget.setEnabled(False)
			self.plot.mpl_refresh_setEnabled(False)
			self.voltage_step_button.setEnabled(False)

	 		# Check app meta and run sweep or sweep-step tread
			if self._get_app_metadata("__exec_voltage_step__") == True:
				self.thread = threading.Thread(target=self.exec_sweep_step_thread, args=())

			else:	
				self.thread = threading.Thread(target=self.exec_sweep_thread, args=())


			self.thread.daemon = True						# Daemonize thread
			self.thread.start()         					# Start the execution
			self.thread_running = True

	# Function we run when we enter abort state
	def exec_meas_stop(self):
	
		# For startup protection
		if self.keithley(self.sweep_inst) is not None:

			# Update UI button to start state
			self.meas_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

			# Enable controls
			self.sweep_src.setEnabled(True)
			self.sweep_inst.setEnabled(True)
			self.save_widget.setEnabled(True)
			self.plot.mpl_refresh_setEnabled(True)
			self.voltage_step_button.setEnabled(True)

			# Kill measurement thread
			self.thread_running = False
			self.thread.join()  # Waits for thread to complete
