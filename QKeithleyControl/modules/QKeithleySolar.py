# ---------------------------------------------------------------------------------
# 	QKeithleyControl
# 	Copyright (C) 2019 Michael Winters
#	mwchalmers@protonmail.com
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
import visa
import time
import numpy as np

# Import d_plot and keithley driver
import drivers.keithley_2400

# Import widgets
import widgets.QDynamicPlot 
import widgets.QUnitSelector

# Import QT backends
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel, QFileDialog, QSizePolicy, QLineEdit
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject
from PyQt5.QtGui import QIcon

# Container class to construct solar measurement widget
class QKeithleySolar(QWidget):

	def __init__(self):

		QWidget.__init__(self)

		# Create Icon for QMessageBox
		self.icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico"))	

		# Initialize Keithley Object
		self.keithley = None

		# Create objects to hold data
		self._data = []
			
		# Create layout objects and set layout
		self.layout = QHBoxLayout()
		self.layout.addLayout(self._gen_solar_control())
		self.layout.addWidget(self._gen_solar_plots())
		self.setLayout(self.layout)

	# Helper method to generate QHBoxLayouts
	def _gen_hboxlayout(self, _widget_list):
	
		_layout = QHBoxLayout()
		for _w in _widget_list:
			_layout.addWidget(_w)
		return _layout

	# Set visa insturment handle for keithley
	def _set_keithley_handle(self, keithley):
		self.keithley=keithley

	# Method to reset sweep on window switch
	def _reset_defaults(self):
		self._data = []

	def _update_current_plot(self):

		if self.plot_select.currentText() == "IV":
			self.plot_stack.setCurrentIndex(0)

		if self.plot_select.currentText() == "Voc":
			self.plot_stack.setCurrentIndex(1)

		if self.plot_select.currentText() == "MPP":
			self.plot_stack.setCurrentIndex(2)

	# Method to generate solar characterization controls
	def _gen_solar_control(self):

		self.ctl_layout = QVBoxLayout()

		#####################################
		#  SWEEP MEASUREMENT STATE MACHINE
		#
		
		# Sweep measurement Button. This will be a state machine which 
		# alternates between 'measure' and 'abort' states
		self.sweep_meas_state  = QStateMachine()
		self.sweep_meas_button = QPushButton()
		self.sweep_meas_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create measurement states
		self.sweep_meas_run  = QState()
		self.sweep_meas_stop = QState()

		# Assign state properties and transitions
		self.sweep_meas_run.assignProperty(self.sweep_meas_button, 'text', 'Abort Sweep')
		self.sweep_meas_run.addTransition(self.sweep_meas_button.clicked, self.sweep_meas_stop)
		self.sweep_meas_run.entered.connect(self._exec_sweep_run)

		self.sweep_meas_stop.assignProperty(self.sweep_meas_button, 'text', 'Measure Sweep')
		self.sweep_meas_stop.addTransition(self.sweep_meas_button.clicked, self.sweep_meas_run)
		self.sweep_meas_stop.entered.connect(self._exec_sweep_stop)

		# Add states, set initial state, and state machine
		self.sweep_meas_state.addState(self.sweep_meas_run)
		self.sweep_meas_state.addState(self.sweep_meas_stop)
		self.sweep_meas_state.setInitialState(self.sweep_meas_stop)
		self.sweep_meas_state.start()


		#####################################
		#  SWEEP MEASUREMENT CONFIGURATION
		#
		 
		# Sweep control layout
		self.sweep_start_config={
			"unit" 		: "V", 
			"min"		: "m",
			"max"		: "",
			"label"		: "Sweep Start (V)",
			"limit"		: 2.0, 
			"signed"	: True,
			"default"	: -1.0
		} 
		self.sweep_start = widgets.QUnitSelector.QUnitSelector(self.sweep_start_config)

		# Configuration for bias level unit box
		self.sweep_stop_config={
			"unit" 		: "V", 
			"min"		: "m",
			"max"		: "",
			"label"		: "Sweep Start (V)",
			"limit"		: 2.0, 
			"signed"	: True,
			"default"	: 1.0
		} 
		self.sweep_stop = widgets.QUnitSelector.QUnitSelector(self.sweep_stop_config)

		
		self.sweep_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"limit"		: 256.0, 
			"signed"	: False,
			"default"	: 11.0
		}
		self.sweep_npts = widgets.QUnitSelector.QUnitSelector(self.sweep_npts_config)


		#####################################
		#  TRACKING MEASUREMENT STATE MACHINE
		#

		# Create QStateMachine for output state
		self.tmode_state = QStateMachine()
		self.tmode_meas_button = QPushButton()
		self.tmode_meas_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create output states
		self.tmode_meas_off = QState()
		self.tmode_meas_on  = QState()

		# Attach states to output button and define state transitions
		self.tmode_meas_off.assignProperty(self.tmode_meas_button, 'text', 'Monitor Off')
		self.tmode_meas_off.addTransition(self.tmode_meas_button.clicked, self.tmode_meas_on)
		self.tmode_meas_off.entered.connect(self._exec_tmode_off)

		self.tmode_meas_on.assignProperty(self.tmode_meas_button, 'text', 'Monitor On')
		self.tmode_meas_on.addTransition(self.tmode_meas_button.clicked, self.tmode_meas_off)
		self.tmode_meas_on.entered.connect(self._exec_tmode_on)
		
		# Add states, set initial state, and start machine
		self.tmode_state.addState(self.tmode_meas_off)
		self.tmode_state.addState(self.tmode_meas_on)
		self.tmode_state.setInitialState(self.tmode_meas_off)
		self.tmode_state.start()


		#####################################
		#  TRACKING MEASUREMENT CONFIGURATION
		#

		# Tracking mode control
		self.tmode_select_label = QLabel("Parameter Tracking")
		self.tmode_select = QComboBox()
		self.tmode_select.setFixedWidth(200)
		self.tmode_select.addItems(["Voc", "MPP"])	

		# Tracking mode initialization
		self.tmode_init_config={
			"unit" 		: "V", 
			"min"		: "m",
			"max"		: "",
			"label"		: "Initialization (V)",
			"limit"		: 2.0, 
			"signed"	: True,
			"default"	: 0.7
		} 
		self.tmode_init = widgets.QUnitSelector.QUnitSelector(self.tmode_init_config)

		# Tracking mode convergence
		self.tmode_conv_config={
			"unit" 		: "V", 
			"min"		: "u",
			"max"		: "m",
			"label"		: "Convergence (mV)",
			"limit"		: 10.0, 
			"signed"	: True,
			"default"	: 1.0
		} 
		self.tmode_conv = widgets.QUnitSelector.QUnitSelector(self.tmode_conv_config)


		# Delay
		self.tmode_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: 0.1
		}
		self.tmode_delay = widgets.QUnitSelector.QUnitSelector(self.tmode_delay_config)

		#####################################
		#  PLOT AND SAVE MEASUREMENTS
		#

		# Plotting and save control
		self.plot_select_label = QLabel("Measurement Plot")
		self.plot_select = QComboBox()
		self.plot_select.addItems(["IV", "Voc", "MPP"])
		self.plot_select.setFixedWidth(200)
		self.plot_select.currentTextChanged.connect(self._update_current_plot)

		# Save traces 
		self.save_note_label = QLabel("Measurement Note")
		self.save_note = QLineEdit()
		self.save_note.setFixedWidth(200)
		
		self.save_button = QPushButton("Save Characterization")
		#self.save_button.clicked.connect(self._save_traces)	

		#####################################
		#  ADD CONTROLS
		#

		# Add sweep controls	
		self.ctl_layout.addWidget(self.sweep_meas_button)
		self.ctl_layout.addWidget(self.sweep_start)
		self.ctl_layout.addWidget(self.sweep_stop)
		self.ctl_layout.addWidget(self.sweep_npts)

	
		# Add tracking controls
		self.ctl_layout.addStretch(1)
		self.ctl_layout.addWidget(self.tmode_meas_button)
		_layout = self._gen_hboxlayout([self.tmode_select, self.tmode_select_label])
		self.ctl_layout.addLayout(_layout)
		self.ctl_layout.addWidget(self.tmode_delay)
		self.ctl_layout.addWidget(self.tmode_init)
		self.ctl_layout.addWidget(self.tmode_conv)

		# Add save control 
		self.ctl_layout.addStretch(1)
		_layout = self._gen_hboxlayout([self.plot_select, self.plot_select_label])
		self.ctl_layout.addLayout(_layout)
		_layout = self._gen_hboxlayout([self.save_note, self.save_note_label])
		self.ctl_layout.addLayout(_layout)
		self.ctl_layout.addWidget(self.save_button)

		# Positioning
		self.ctl_layout.setContentsMargins(0,15,0,20)
		return self.ctl_layout

	# Method to generate solar cell plots. This will be implemented 
	# as three QDynamicPlots packed into a QStackedWidget
	def _gen_solar_plots(self):

		# Call QStackedWidget constructor
		self.plot_stack = QStackedWidget()

		# Plot IV-Sweep mode
		self.sweep_plot =  widgets.QDynamicPlot.QDynamicPlot()
		self.sweep_plot.set_axes_labels('Voltage (V)', 'Current (A)')
		self.sweep_plot.add_axes()
		
		self.voc_plot =  widgets.QDynamicPlot.QDynamicPlot()
		self.voc_plot.set_axes_labels('Time (s)', 'Voc (V)')
		self.voc_plot.add_axes()

		self.mpp_plot =  widgets.QDynamicPlot.QDynamicPlot()
		self.mpp_plot.set_axes_labels('Time (s)', 'MPP (V)')
		self.mpp_plot.add_axes()


		# Add QDynamicPlots to QStackedWidget
		self.plot_stack.addWidget(self.sweep_plot)
		self.plot_stack.addWidget(self.voc_plot)
		self.plot_stack.addWidget(self.mpp_plot)

		# Return the stacked widget
		self.plot_stack.setCurrentIndex(0);
		return self.plot_stack

	###########################	
	# State Machine Callbacks #	
	###########################
	# Sweep measurement ON
	def _exec_sweep_run(self):

		if self.keithley is not None:

			self.sweep_meas_button.setStyleSheet(
				"background-color: #ffcccc; border-style: solid; border-width: 1px; border-color: #800000; padding: 7px;")
			self.save_button.setEnabled(False)

	# Sweep measurement OFF
	def _exec_sweep_stop(self):

		if self.keithley is not None:

			self.sweep_meas_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )
			self.save_button.setEnabled(True)
		
	# Tracking measurement ON
	def _exec_tmode_on(self):
		
		if self.keithley is not None:

			# Update UI for ON state
			self.tmode_meas_button.setStyleSheet(
				"background-color: #cce6ff; border-style: solid; border-width: 1px; border-color: #1a75ff; padding: 7px;")
			self.save_button.setEnabled(False)
			


	# Tracking measurement OFF
	def _exec_tmode_off(self):
		
		if self.keithley is not None:

			self.tmode_meas_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )			
			self.save_button.setEnabled(True)