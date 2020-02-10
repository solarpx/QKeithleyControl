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

			# Plot control widgets
			self.plot_x_inst.refresh( self )
			self.plot_y_inst.refresh( self )

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
		self.meas_pages.addWidget(self.gen_plot_ctrl())

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
		self.meas_config_page.addItems(["IV-sweep", "IV-step", "IV-plot"])	
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
		self.sweep_src_label = QLabel("Sweep Type")
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

		# Step control mode selector
		self.step_src_label = QLabel("Step Type")
		self.step_src = QComboBox()
		self.step_src.setFixedWidth(200)
		self.step_src.addItems(["Voltage", "Current"])	
		self.step_src.currentTextChanged.connect(self.update_step_ctrl)

		# Generate voltage and current source widgets
		self.gen_voltage_step()		# self.voltage_step
		self.gen_current_step()		# self.current_step		

		# Add step modes to step_pages widget
		self.step_pages = QStackedWidget()	
		self.step_pages.addWidget(self.voltage_step)
		self.step_pages.addWidget(self.current_step)
		self.step_pages.setCurrentIndex(0)

		# Step control state machine
		self.step_state = QStateMachine()
		self.step_button = QPushButton()
		self.step_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create measurement states
		self.step_on  = QState()
		self.step_off = QState()

		# Assign state properties and transitions
		self.step_on.assignProperty(self.step_button, 'text', 'Step Bias ON')
		self.step_on.addTransition(self.step_button.clicked, self.step_off)
		self.step_on.entered.connect(self.exec_step_on)

		self.step_off.assignProperty(self.step_button, 'text', 'Step Bias OFF')
		self.step_off.addTransition(self.step_button.clicked, self.step_on)
		self.step_off.entered.connect(self.exec_step_off)

		# Add states, set initial state, and state machine
		self.step_state.addState(self.step_on)
		self.step_state.addState(self.step_off)
		self.step_state.setInitialState(self.step_off)
		self.step_state.start()

		# Pack widgets
		self.step_ctrl_layout.addWidget(self.step_ctrl_label)
		self.step_ctrl_layout.addWidget(self._gen_hbox_widget([self.step_inst,self.step_inst_label]))
		self.step_ctrl_layout.addWidget(self._gen_hbox_widget([self.step_src, self.step_src_label]))
		self.step_ctrl_layout.addWidget(self.step_pages)
		self.step_ctrl_layout.addWidget(self.step_button)
		self.step_ctrl_layout.addStretch(1)

		# Set layout and return reference
		self.step_ctrl.setLayout(self.step_ctrl_layout)		
		return self.step_ctrl	

	# Plot control layout	
	def gen_plot_ctrl(self):

		self.plot_ctrl = QWidget()
		self.plot_ctrl_layout = QVBoxLayout()

		# Voltage step instruement selector
		self.plot_x_inst_label = QLabel("<b>Configure x-axis</b>")
		self.plot_x_inst = self._gen_device_select()
		self.plot_x_inst.setFixedWidth(200)
		self.plot_x_inst.set_callback("update_plot_ctrl")

		self.plot_x_data = QComboBox()
		self.plot_x_data.setFixedWidth(100)
		self.plot_x_data.addItems(["Voltage", "Current"])	
		self.plot_x_data.currentTextChanged.connect( self.update_plot_ctrl )

		# Voltage step instruement selector
		self.plot_y_inst_label = QLabel("<b>Configure y-axis</b>")
		self.plot_y_inst = self._gen_device_select()
		self.plot_y_inst.setFixedWidth(200)
		self.plot_y_inst.set_callback("update_plot_ctrl")

		self.plot_y_data = QComboBox()
		self.plot_y_data.setFixedWidth(100)
		self.plot_y_data.addItems(["Voltage", "Current"])	
		self.plot_y_data.setCurrentIndex(1)
		self.plot_y_data.currentTextChanged.connect( self.update_plot_ctrl )

		# Add widgets
		self.plot_ctrl_layout.addWidget( self.plot_x_inst_label )
		self.plot_ctrl_layout.addWidget( self._gen_hbox_widget( [self.plot_x_inst,self.plot_x_data]) )
		self.plot_ctrl_layout.addWidget( self.plot_y_inst_label )
		self.plot_ctrl_layout.addWidget( self._gen_hbox_widget( [self.plot_y_inst,self.plot_y_data]) )
		self.plot_ctrl_layout.addStretch(1)

		# Set layout and return reference
		self.plot_ctrl.setLayout(self.plot_ctrl_layout)		
		return self.plot_ctrl

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
			"signed"	: True,
			"limit"		: [20.0, ""],
			"default"	: [0.00, ""]
		} 
		self.voltage_sweep_start = QVisaUnitSelector.QVisaUnitSelector(self.voltage_sweep_start_config)

		# Sweep Stop
		self.voltage_sweep_stop_config={
			"unit" 		: "V",
			"min"		: "u",
			"max"		: "",
			"label"		: "Sweep Stop (V)",
			"signed"	: True,
			"limit"		: [20.0, ""],
			"default"	: [1.00, ""]
		} 
		self.voltage_sweep_stop = QVisaUnitSelector.QVisaUnitSelector(self.voltage_sweep_stop_config)

		# Compliance Spinbox
		self.voltage_sweep_cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (A)",
			"signed"	: False,
			"limit"		: [1.0, "" ], 
			"default"	: [150, "m"]
		} 
		self.voltage_sweep_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.voltage_sweep_cmpl_config)	

		# Number of points
		self.voltage_sweep_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"signed"	: False,
			"limit"		: [512],
			"default"	: [51]
		}
		self.voltage_sweep_npts = QVisaUnitSelector.QVisaUnitSelector(self.voltage_sweep_npts_config)

		# Measurement Delay
		self.voltage_sweep_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"signed"	: False,
			"limit"		: [60.0], 
			"default"	: [0.10]
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
			"signed"	: True,
			"limit"		: [1.0, "" ],
			"default"	: [0.0, "m"]
		} 
		self.current_sweep_start = QVisaUnitSelector.QVisaUnitSelector(self.current_sweep_start_config)

		# Sweep Stop
		self.current_sweep_stop_config={
			"unit" 		: "A",
			"min"		: "u",
			"max"		: "",
			"label"		: "Sweep Stop (A)",
			"signed"	: True,
			"limit"		: [1.0, "" ],
			"default"	: [100, "m"]
		} 
		self.current_sweep_stop = QVisaUnitSelector.QVisaUnitSelector(self.current_sweep_stop_config)

		# Compliance Spinbox
		self.current_sweep_cmpl_config={
			"unit" 		: "V", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (V)",
			"signed"	: False,
			"limit"		: [20., ""],
			"default"	: [1.0, ""]
		} 
		self.current_sweep_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.current_sweep_cmpl_config)

		# Number of points
		self.current_sweep_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"signed"	: False,
			"limit"		: [256],
			"default"	: [11]
		}
		self.current_sweep_npts = QVisaUnitSelector.QVisaUnitSelector(self.current_sweep_npts_config)

		# Measurement Delay
		self.current_sweep_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"signed"	: False,
			"limit"		: [60.0],
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

		# Step Start
		self.voltage_step_start_config={
			"unit" 		: "V",
			"min"		: "u",
			"max"		: "",
			"label"		: "Step Start (V)",
			"signed"	: True,
			"limit"		: [20.0, ""],
			"default"	: [0.00, ""]
		} 
		self.voltage_step_start = QVisaUnitSelector.QVisaUnitSelector(self.voltage_step_start_config)

		# Step Stop
		self.voltage_step_stop_config={
			"unit" 		: "V",
			"min"		: "u",
			"max"		: "",
			"label"		: "Step Stop (V)",
			"signed"	: True,
			"limit"		: [20.0, ""],
			"default"	: [1.00, ""]
		} 
		self.voltage_step_stop = QVisaUnitSelector.QVisaUnitSelector(self.voltage_step_stop_config)

		# Step Compliance Spinbox
		self.voltage_step_cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (A)",
			"signed"	: False,
			"limit"		: [1.0, "" ], 
			"default"	: [150, "m"]
		} 
		self.voltage_step_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.voltage_step_cmpl_config)	

		# Step Number of points
		self.voltage_step_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"signed"	: False,
			"limit"		: [256], 
			"default"	: [5]
		}
		self.voltage_step_npts = QVisaUnitSelector.QVisaUnitSelector(self.voltage_step_npts_config)

		# Pack selectors into layout
		self.voltage_step_layout.addWidget(self.voltage_step_start)
		self.voltage_step_layout.addWidget(self.voltage_step_stop)
		self.voltage_step_layout.addWidget(self.voltage_step_cmpl)
		self.voltage_step_layout.addWidget(self.voltage_step_npts)
		self.voltage_step_layout.setContentsMargins(0,0,0,0)

		# Set layout 
		self.voltage_step.setLayout(self.voltage_step_layout)		

	# Generate current step widget
	def gen_current_step(self):

		# New QWidget
		self.current_step = QWidget()
		self.current_step_layout = QVBoxLayout()

		# Step Start
		self.current_step_start_config={
			"unit" 		: "A",
			"min"		: "u",
			"max"		: "",
			"label"		: "Step Start (A)",
			"signed"	: True,
			"limit"		: [1.0, "" ],
			"default"	: [0.0, "m"]
		} 
		self.current_step_start = QVisaUnitSelector.QVisaUnitSelector(self.current_step_start_config)

		# Step Stop
		self.current_step_stop_config={
			"unit" 		: "A",
			"min"		: "u",
			"max"		: "",
			"label"		: "Step Stop (A)",
			"signed"	: True,
			"limit"		: [1.0, "" ],
			"default"	: [1.0, "m"]
		} 
		self.current_step_stop = QVisaUnitSelector.QVisaUnitSelector(self.current_step_stop_config)

		# Step Compliance Spinbox
		self.current_step_cmpl_config={
			"unit" 		: "V", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (V)",
			"signed"	: False,
			"limit"		: [20.0, ""],
			"default"	: [1.00, ""]
		} 
		self.current_step_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.current_step_cmpl_config)	

		# Step Number of points
		self.current_step_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"signed"	: False,
			"limit"		: [256],
			"default"	: [5]
		}
		self.current_step_npts = QVisaUnitSelector.QVisaUnitSelector(self.current_step_npts_config)

		# Pack selectors into layout
		self.current_step_layout.addWidget(self.current_step_start)
		self.current_step_layout.addWidget(self.current_step_stop)
		self.current_step_layout.addWidget(self.current_step_cmpl)
		self.current_step_layout.addWidget(self.current_step_npts)
		self.current_step_layout.addStretch(1)
		self.current_step_layout.setContentsMargins(0,0,0,0)

		# Set layout 
		self.current_step.setLayout(self.current_step_layout)		

	# Ádd dynamic plot
	def gen_main_plot(self): 		

		# Create QVisaDynamicPlot object (inherits QWidget) 
		self.plot = QVisaDynamicPlot.QVisaDynamicPlot(self)
		self.plot.add_subplot(111)
		self.plot.add_origin_lines("111", "both")
		self.plot.set_axes_labels("111", "Voltage (V)", "Current (A)")
		
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

		if self.meas_config_page.currentText() == "IV-step":
			self.meas_pages.setCurrentIndex(1)

		if self.meas_config_page.currentText() == "IV-plot":
			self.meas_pages.setCurrentIndex(2)


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

	# Sweep control dynamic update
	def update_step_ctrl(self):

		# Switch to voltage sweep page
		if self.step_src.currentText() == "Voltage":
			self.step_pages.setCurrentIndex(0)
			self.update_meas_params()

		# Switch to current sweep page
		if self.step_src.currentText() == "Current":		
			self.step_pages.setCurrentIndex(1)
			self.update_meas_params()

	# Update plot axes when we change configuration		
	def update_plot_ctrl(self):		

		# Extract correct unit labels
		x_unit = "(V)" if self.plot_x_data.currentText() == "Voltage" else "(A)"
		y_unit = "(V)" if self.plot_y_data.currentText() == "Voltage" else "(A)"

		# Update axes
		self.plot.set_axes_labels("111", 
			"%s %s : %s"%(self.plot_x_data.currentText(), x_unit ,self.plot_x_inst.currentText()), 
			"%s %s : %s"%(self.plot_y_data.currentText(), y_unit ,self.plot_y_inst.currentText())
		)

		self.plot.update_canvas()

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


		# Set step keithley as voltage source. Also ensure that we are not initializing
		# the the sweep keithely with step params if doubly selected.
		if ( ( self.keithley(self.step_inst) is not None) and
			 (self.keithley(self.step_inst) != self.keithley(self.sweep_inst) ) ):


			# Set up v-source(i-compliance) on keithley 
			if self.step_src.currentText() == "Voltage":
				
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
	

			# Set up i-source(v-compliance) on keithley 
			if self.step_src.currentText() == "Current":

				# Set sweeep paramaters
				self.set_step_params(
					self.current_step_start.value(), 
					self.current_step_stop.value(), 
					self.current_step_npts.value())

		
				# Set keithley as voltage source
				if self.keithley(self.step_inst) is not None:
				
					self.keithley(self.step_inst).current_src()
					self.keithley(self.step_inst).set_current(0.0)
					self.keithley(self.step_inst).voltage_cmp(self.current_step_cmpl.value())	


	#####################################
	#  MEASUREMENT EXECUTION THREADS
	#		

	# Function we run when we enter run state
	def exec_step_on(self):

		# Update UI button to abort 
		self.step_button.setStyleSheet(
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
			self._set_app_metadata("__exec_step__", False)
			self.step_button.click()

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
				self._set_app_metadata("__exec_step__", True)

			else:	
				self._set_app_metadata("__exec_step__", False)
				self.step_button.click()

		else:
			self._set_app_metadata("__exec_step__", True)


	# Function we run when we enter run state
	def exec_step_off(self):

		# Update UI button to abort 
		self.step_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		self._set_app_metadata("__exec_step__", False)

	
	# Execute Sweep-Step Measurement
	def exec_sweep_step_thread(self):
	
		# Generate function pointer for sweep voltage/current mode
		if self.sweep_src.currentText() == "Voltage":
			__sweep_func__  = self.keithley(self.sweep_inst).set_voltage
			__sweep_delay__ = self.voltage_sweep_delay.value()

		if self.sweep_src.currentText() == "Current":
			__sweep_func__ = self.keithley(self.sweep_inst).set_current
			__sweep_delay__ = self.current_sweep_delay.value()

		# Clear plot and zero arrays
		start  = time.time()

		# Use generator function so all traces have same color
		_c = self.plot.gen_next_color()
		_handle_index = 0 

		# Get data object
		data = self._get_data_object()

		# Master key
		_root = data.add_hash_key("iv-sweep-v-step")

		# Set metatata for root
		if self.step_src.currentText() == "Voltage":
			
			data.set_metadata(_root, "__type__", "iv-sweep-v-step")

		if self.step_src.currentText() == "Current":
			
			data.set_metadata(_root, "__type__", "iv-sweep-v-step")

		# Add key to meta widget
		self.meta_widget.add_meta_key(_root)		

		# Create internal data structure for buffers
		buffers = {
			"__sweep__" : {"inst" : self.sweep_inst, "data" : None},
			"__step__"	: {"inst" : self.step_inst , "data" : None},
			"__plotx__" : None,
			"__ploty__" : None
		}


		# plot-axis insturments
		for plot_key, plot_inst in zip(["__plotx__", "__ploty__" ], [ self.plot_x_inst, self.plot_y_inst] ):

			if self.sweep_inst.currentText() == plot_inst.currentText():
				
				buffers[ plot_key ] = {"inst" : "__sweep__", "data" : None }

			elif self.step_inst.currentText() == plot_inst.currentText():
				
				buffers[ plot_key ] = {"inst" : "__step__", "data" : None }

			else: 

				buffers[ plot_key ] = {"inst" : plot_inst, "data" : None}


		# Loop throgh all insurments and enable outputs
		for _key, _buffer in buffers.items():

			if _buffer["inst"] not in ["__sweep__", "__step__"]:

				self.keithley( _buffer["inst"] ).output_on()
		

		# Loop through step variables and generate subkeys
		for _step in self._get_app_metadata("__step__"):

			# If thread is running
			if self.thread_running:

				# A hash is generated for each voltage/current step for ease of data processing
				# Generate function pointer for step voltage/current mode
				if self.step_src.currentText() == "Voltage":
				
					__step_func__  = self.keithley(self.step_inst).set_voltage

					# Generate data key and set metadata
					data 	= self._get_data_object()
					key  = data.add_hash_key("iv-sweep-v-step%s"%_step)

					# Add keys and metadata to data object
					data.set_metadata(key, "__root__", _root)
					data.set_metadata(key, "__step__", _step)
					data.set_subkeys(key, ["t", "V0", "I0", "P0", "V1", "I1", "P1"])

				# Current Mode
				if self.step_src.currentText() == "Current":

					__step_func__  = self.keithley(self.step_inst).set_current

					key  = data.add_hash_key("iv-sweep-i-step%s"%_step)

					# Add keys and metadata to data object
					data.set_metadata(key, "__root__", _root)
					data.set_metadata(key, "__step__", _step)
					data.set_subkeys(key, ["t", "V0", "I0", "P0", "V1", "I1", "P1"])


				# Set step voltage/current
				__step_func__(_step)

				# Add axes handle to root
				self.plot.add_axes_handle("111", _root, _color=_c)

				# Bias settle
				if __sweep_delay__ != 0: 
					time.sleep(__sweep_delay__)

				# Loop through sweep variables
				for _bias in self._get_app_metadata("__sweep__"):

					# If thread is running
					if self.thread_running:

						# Set voltage/current bias
						__sweep_func__(_bias)			

						# Get data from buffer
						# Populate buffers
						buffers["__sweep__"]["data"] = self.keithley( buffers["__sweep__"]["inst"] ).meas().split(",")
						buffers["__step__"]["data"]  = self.keithley( buffers["__step__"]["inst"]  ).meas().split(",")

						# Plot insturments will copy sweep data or meas() if needed
						for plot_buffer in ["__plotx__", "__ploty__"]:
			
							if buffers[plot_buffer]["inst"] == "__sweep__":
								
								buffers[plot_buffer]["data"] = buffers["__sweep__"]["data"]

							elif buffers[plot_buffer]["inst"] == "__step__":

								buffers[plot_buffer]["data"] = buffers["__step__"]["data"]

							else: 	

								buffers[plot_buffer]["data"] = self.keithley( buffers[plot_buffer]["inst"] ).meas().split(",")

						# Apply delay
						if __sweep_delay__ != 0: 
							time.sleep(__sweep_delay__)

						# Extract data from buffer
						_now = float(time.time() - start)

						# Append measured values to data arrays	
						data.append_subkey_data(key,"t", _now )
						data.append_subkey_data(key,"V0", float( buffers["__sweep__"]["data"][0]) )
						data.append_subkey_data(key,"I0", float( buffers["__sweep__"]["data"][1]) )
						data.append_subkey_data(key,"P0", float( buffers["__sweep__"]["data"][0]) * float(buffers["__sweep__"]["data"][1]) )
						data.append_subkey_data(key,"V1", float( buffers["__step__"]["data"][0]) )
						data.append_subkey_data(key,"I1", float( buffers["__step__"]["data"][1]) )
						data.append_subkey_data(key,"P1", float( buffers["__step__"]["data"][0]) * float(buffers["__step__"]["data"][1]) )

						# Sync x-axis data
						if self.plot_x_data.currentText() == "Voltage":
							
							p0 = buffers["__plotx__"]["data"][0]

						if self.plot_x_data.currentText() == "Current":

							p0 = buffers["__plotx__"]["data"][1]

						# Sync y-axis data
						if self.plot_y_data.currentText() == "Voltage":
							
							p1 = buffers["__ploty__"]["data"][0]

						if self.plot_y_data.currentText() == "Current":

							p1 = buffers["__ploty__"]["data"][1]

						# Update the data
						self.plot.append_handle_data("111", _root, float(p0), float(p1), _handle_index)
						self.plot.update_canvas()
				
					else: 

						break 

				# Increment handle index
				_handle_index += 1

			else:

				break

		# Reset active keithleys
		__sweep_func__(0.0)
		__step_func__(0.0)

		# Loop throgh all insurments and disable outputs
		for _key, _buffer in buffers.items():

			if _buffer["inst"] not in ["__sweep__", "__step__"]:

				self.keithley( _buffer["inst"] ).output_off()


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
			__sweep_func__  = self.keithley(self.sweep_inst).set_voltage
			__sweep_delay__ = self.voltage_sweep_delay.value()

		if self.sweep_src.currentText() == "Current":
			__sweep_func__  = self.keithley(self.sweep_inst).set_current
			__sweep_delay__ = self.current_sweep_delay.value()

		# Clear plot and zero arrays
		handle = self.plot.add_axes_handle("111", key)
		start  = time.time()
		
		# Create internal data structure for buffers
		buffers = {
			"__sweep__" : {"inst" : self.sweep_inst, "data" : None},
			"__plotx__" : None,
			"__ploty__" : None
		}

		# x-axis insturment
		for plot_key, plot_inst in zip( ["__plotx__", "__ploty__" ], [self.plot_x_inst, self.plot_y_inst] ):

			if self.sweep_inst.currentText() == plot_inst.currentText():

				buffers[plot_key] = {"inst" : "__sweep__", "data" : None }

			else: 

				buffers[plot_key] = {"inst" : plot_inst, "data" : None}


		# Loop throgh all insurments and enable outputs
		for _key, _buffer in buffers.items():

			if _buffer["inst"] not in ["__sweep__"]:

				self.keithley( _buffer["inst"] ).output_on()


		# Loop through sweep variables
		for _bias in self._get_app_metadata("__sweep__"):

			# If thread is running
			if self.thread_running:

				# Set voltage/current bias
				__sweep_func__(_bias)			

				# Populate buffers
				buffers["__sweep__"]["data"] = self.keithley( buffers["__sweep__"]["inst"] ).meas().split(",")

				# Plot insturments will copy sweep data or meas() if needed
				for plot_buffer in ["__plotx__", "__ploty__"]:
	
					if buffers[plot_buffer]["inst"] == "__sweep__":
						
						buffers[plot_buffer]["data"] = buffers["__sweep__"]["data"]

					else: 	

						buffers[plot_buffer]["data"] = self.keithley( buffers[plot_buffer]["inst"] ).meas().split(",")

				if __sweep_delay__ != 0: 
					time.sleep(__sweep_delay__)

				# Extract data from buffer
				_now = float(time.time() - start)

				# Append measured values to data arrays	
				data.append_subkey_data(key,"t", _now )
				data.append_subkey_data(key,"V", float( buffers["__sweep__"]["data"][0]) )
				data.append_subkey_data(key,"I", float( buffers["__sweep__"]["data"][1]) )
				data.append_subkey_data(key,"P", float( buffers["__sweep__"]["data"][0]) * float(buffers["__sweep__"]["data"][1]) )

				# Sync x-axis data
				if self.plot_x_data.currentText() == "Voltage":
					
					p0 = buffers["__plotx__"]["data"][0]

				if self.plot_x_data.currentText() == "Current":

					p0 = buffers["__plotx__"]["data"][1]

				# Sync y-axis data
				if self.plot_y_data.currentText() == "Voltage":
					
					p1 = buffers["__ploty__"]["data"][0]

				if self.plot_y_data.currentText() == "Current":

					p1 = buffers["__ploty__"]["data"][1]

				# Update the data
				self.plot.append_handle_data("111", key, float(p0), float(p1))
				self.plot.update_canvas()
		
		# Reset Keithley
		__sweep_func__(0.0)
	
		# Loop throgh all insurments and enable outputs
		for _key, _buffer in buffers.items():

			if _buffer["inst"] not in ["__sweep__"]:

				self.keithley( _buffer["inst"] ).output_off()


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

			# Disable controls (sweep)
			self.sweep_src.setEnabled(False)
			self.sweep_inst.setEnabled(False)
			
			# Disable controls (step)
			self.step_src.setEnabled(False)
			self.step_inst.setEnabled(False)
			self.step_button.setEnabled(False)

			# Disable controls (save)
			self.save_widget.setEnabled(False)
			
			# Plot contollers (plots)
			self.plot.mpl_refresh_setEnabled(False)
			self.plot_x_inst.setEnabled(False)
			self.plot_x_data.setEnabled(False)
			self.plot_y_inst.setEnabled(False)
			self.plot_y_data.setEnabled(False)

	 		# Check app meta and run sweep or sweep-step tread
			if self._get_app_metadata("__exec_step__") == True:
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

			# Enable controls (sweep)
			self.sweep_src.setEnabled(True)
			self.sweep_inst.setEnabled(True)

			# Enable controls (step)
			self.step_src.setEnabled(True)
			self.step_inst.setEnabled(True)
			self.step_button.setEnabled(True)

			# Enable controls (save)
			self.save_widget.setEnabled(True)
	
			# Plot contollers
			self.plot.mpl_refresh_setEnabled(True)
			self.plot_x_inst.setEnabled(True)
			self.plot_x_data.setEnabled(True)
			self.plot_y_inst.setEnabled(True)
			self.plot_y_data.setEnabled(True)
			
			# Kill measurement thread
			self.thread_running = False
			self.thread.join()  # Waits for thread to complete
